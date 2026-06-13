#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
"""
  _____ _       _   _      ____        _
 / ____| |     | | | |    / __ \      (_)
| (___ | | ___ | |_| |_  | |  | |_   _ _ __ ___  __ _
 \___ \| |/ _ \| __| __| | |  | | | | | '__/ _ \/ _` |
 ____) | | (_) | |_| |_  | |__| | |_| | | |  __/ (_| |
|_____/|_|\___/ \__|\__|  \____/ \__,_|_|  \___|\__,_|
                                                           
Bookmark Cleaner - 浏览器收藏夹失效链接清理工具
Version: 1.1.0 (Optimized & Bug Fixed)
GitHub: https://github.com/lynx2016/bookmark-cleaner
"""
__version__ = "1.1.0"

import sys
import os
import argparse
import time
import csv
import shutil
import re
import random
import multiprocessing
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urlparse

# ── Windows 终端乱码修复 ─────────────────────────────────────────────────────
if sys.platform.startswith('win'):
    # 1. 设置控制台代码页为 UTF-8 (65001)
    import ctypes
    kernel32 = ctypes.windll.kernel32
    kernel32.SetConsoleCP(65001)
    kernel32.SetConsoleOutputCP(65001)
    # 2. 启用 ANSI 虚拟终端序列支持 (ENABLE_VIRTUAL_TERMINAL_PROCESSING=0x0004)
    #    同时保留现有模式 (保留低3位)，加或运算防止覆盖
    STD_OUTPUT_HANDLE = -11
    handle = kernel32.GetStdHandle(STD_OUTPUT_HANDLE)
    mode = ctypes.c_uint32()
    kernel32.GetConsoleMode(handle, ctypes.byref(mode))
    kernel32.SetConsoleMode(handle, mode.value | 0x0004)
    # 3. 强制 stdout/stderr 使用 UTF-8 编码
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# ── 依赖检查 ──────────────────────────────────────────────────────────────────
try:
    import requests
    from bs4 import BeautifulSoup
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
except ImportError:
    print("[ERROR] 缺少依赖库，请先执行：")
    print("   pip install requests beautifulsoup4")
    sys.exit(1)

requests.packages.urllib3.disable_warnings(
    requests.packages.urllib3.exceptions.InsecureRequestWarning
)

# ── 全局配置项 ──────────────────────────────────────────────────────────────────
DEAD_STATUS_CODES = set(range(400, 600))
SUSPICIOUS_CODES = {401, 403, 429, 503, 504}
FALLBACK_TO_GET_CODES = {405, 501}
SHORTLINK_DOMAINS = {
    "t.co", "bit.ly", "goo.gl", "url.cn", "dwz.cn", "t.cn",
    "tinyurl.com", "ow.ly", "buff.ly", "rebrand.ly", "cutt.ly",
    "is.gd", "cli.gs", "soo.gd", "v.ht", "x.co", "rb.gy", "sourl.cn"
}
TIMEOUT_SECS = 10
MAX_RETRIES = 2
# 自适应并发数，上限20
MAX_WORKERS = min(20, multiprocessing.cpu_count() * 2 + 1)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/126.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}

# ── 复用请求 Session（连接池+重试策略）────────────────────────────────────────
def create_request_session() -> requests.Session:
    """创建带连接池、自动重试的全局Session"""
    session = requests.Session()
    retry_strategy = Retry(
        total=MAX_RETRIES,
        backoff_factor=0.5,
        status_forcelist=FALLBACK_TO_GET_CODES,
        allowed_methods=["HEAD", "GET"]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    session.headers.update(HEADERS)
    return session

GLOBAL_SESSION = create_request_session()

# ── 终端颜色类（Windows/Linux 全兼容）──────────────────────────────────────────
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    RESET = '\033[0m'

    @staticmethod
    def init():
        """Windows ANSI颜色已在模块顶部通过 ctypes 初始化，此处保留兼容"""

# ── 进度条（Windows终端适配）──────────────────────────────────────────────────
class ProgressBar:
    def __init__(self, total: int, width: int = 30, quiet: bool = False):
        self.total = total
        self.width = width
        self.quiet = quiet
        self.start_time = time.time()
        self.done = 0
        self.stats = {'alive': 0, 'dead': 0, 'suspicious': 0, 'skipped': 0}

    def update(self, status: bool | None, skipped: bool = False):
        if self.quiet:
            return
        self.done += 1
        if skipped:
            self.stats['skipped'] += 1
        elif status is True:
            self.stats['alive'] += 1
        elif status is False:
            self.stats['dead'] += 1
        else:
            self.stats['suspicious'] += 1

        elapsed = time.time() - self.start_time
        eta = elapsed * (self.total - self.done) / self.done if self.done > 0 else 0
        eta_str = f"ETA {int(eta//60)}m{int(eta%60):02d}s" if eta > 0 else "ETA --:--"

        pct = self.done / self.total if self.total > 0 else 1
        filled = int(self.width * pct)
        bar = "█" * filled + "░" * (self.width - filled)

        s = self.stats
        line = (f"\r  [{bar}] {self.done:4d}/{self.total} {pct:5.0%} "
                f"| ✅有效链接 {s['alive']:<4d}  ❌失效链接 {s['dead']:<4d}  ⚠️可疑链接 {s['suspicious']:<3d} | {eta_str}")
        print(line, end="", flush=True)

        if self.done == self.total:
            print()

# ── URL 隐私脱敏 ──────────────────────────────────────────────────────────────
# 常见的敏感 query 参数名（含 token/key/secret/auth/session/password 等）
_SENSITIVE_PARAMS = re.compile(
    r'([?&])(token|access_token|auth|api_key|apikey|key|secret|password|passwd|'
    r'session|sid|sig|sign|signature|hash|credential|authorization|'
    r'jwt|bearer|refresh_token|client_secret|private_key|'
    r'code|state|nonce|oauth_token|oauth_verifier)=[^&]*',
    re.IGNORECASE
)

def sanitize_url(url: str) -> str:
    """脱敏 URL 中的敏感 query 参数，将值替换为 ***"""
    return _SENSITIVE_PARAMS.sub(r'\1\2=***', url)

# ── URL 检测核心逻辑（修复短链接、异常处理）──────────────────────────────────
def check_url(url: str, timeout: int, proxy: str | None = None) -> tuple[str, bool | None, str, bool]:
    """
    检测链接可用性
    :return: (url, 状态, 原因, 是否跳过)
    status: True=有效, False=失效, None=可疑
    skipped: 是否被白名单跳过
    """
    scheme = urlparse(url).scheme.lower()
    if scheme not in ("http", "https"):
        return url, True, "非HTTP协议", True

    domain = urlparse(url).netloc.lower().rstrip('.')
    domain_parts = domain.split('.')
    # 修复：精准匹配短链接域名（仅匹配二级域名）
    is_shortlink = False
    if domain in SHORTLINK_DOMAINS:
        is_shortlink = True
    elif len(domain_parts) >= 2:
        root_domain = '.'.join(domain_parts[-2:])
        if root_domain in SHORTLINK_DOMAINS:
            is_shortlink = True

    if is_shortlink:
        return url, True, "短链接服务", True

    proxies = {'http': proxy, 'https': proxy} if proxy else None
    GLOBAL_SESSION.proxies = proxies
    last_error = ""

    for attempt in range(MAX_RETRIES + 1):
        try:
            resp = GLOBAL_SESSION.head(
                url, timeout=timeout,
                allow_redirects=True, verify=False
            )

            if resp.status_code in FALLBACK_TO_GET_CODES:
                try:
                    with GLOBAL_SESSION.get(
                        url, timeout=timeout,
                        allow_redirects=True, verify=False, stream=True
                    ) as resp_get:
                        if resp_get.status_code in SUSPICIOUS_CODES:
                            return url, None, f"待确认 HTTP {resp_get.status_code}", False
                        if resp_get.status_code in DEAD_STATUS_CODES:
                            return url, False, f"HTTP {resp_get.status_code}", False
                        return url, True, f"HTTP {resp_get.status_code}", False
                except requests.exceptions.RequestException:
                    last_error = "GET降级请求失败"
                    if attempt < MAX_RETRIES:
                        time.sleep(0.2 + random.uniform(0.1, 0.5))
                        continue
                    return url, None, f"待确认 {last_error}", False

            if resp.status_code in SUSPICIOUS_CODES:
                return url, None, f"待确认 HTTP {resp.status_code}", False
            if resp.status_code in DEAD_STATUS_CODES:
                return url, False, f"HTTP {resp.status_code}", False
            return url, True, f"HTTP {resp.status_code}", False

        except requests.exceptions.Timeout:
            last_error = "超时"
        except requests.exceptions.SSLError:
            last_error = "SSL证书错误"
            break
        except requests.exceptions.ConnectionError as e:
            err = str(e).lower()
            if "nameresolution" in err or "getaddrinfo" in err:
                last_error = "DNS解析失败"
                break
            elif "connection refused" in err:
                last_error = "连接被拒绝"
            elif "reset" in err:
                last_error = "连接被重置"
            else:
                last_error = "连接失败"
        except requests.exceptions.TooManyRedirects:
            last_error = "重定向次数过多"
            break
        except requests.exceptions.RequestException as e:
            last_error = f"请求异常: {str(e)[:50]}"

        # 重试随机延迟，防封禁
        if attempt < MAX_RETRIES:
            time.sleep(0.2 + random.uniform(0.1, 0.5))

    return url, False, last_error, False

# ── HTML 书签解析 & 清理（修复空文件夹、正则兼容）────────────────────────────
def get_folder_path(dt) -> str:
    """获取书签所在的文件夹路径"""
    path = []
    current = dt
    while current:
        parent_dl = current.find_parent("dl")
        if parent_dl:
            parent_dt = parent_dl.find_previous_sibling("dt")
            if parent_dt is None:
                break
            h3 = parent_dt.find("h3")
            if h3:
                path.insert(0, h3.get_text(strip=True))
            current = parent_dt
        else:
            break
    return "/".join(path)

def extract_bookmarks(soup: BeautifulSoup, only_folder: str = None, exclude_folder: str = None) -> list[tuple[str, str]]:
    """提取书签 (url, folder_path)，支持文件夹过滤"""
    bookmarks = []
    for a in soup.find_all("a", href=True):
        dt = a.find_parent("dt")
        folder = get_folder_path(dt) if dt else ""

        if only_folder and only_folder not in folder:
            continue
        if exclude_folder and exclude_folder in folder:
            continue

        bookmarks.append((a["href"], folder))
    return bookmarks

def remove_dead_bookmarks(html_text: str, dead_urls: set[str]) -> str:
    """正则删除失效书签，规避DOM解析标签缺失问题"""
    modified = html_text
    for url in dead_urls:
        escaped = re.escape(url)
        pattern = re.compile(
            r'^\s*<DT><A\s+[^>]*HREF="' + escaped + r'"[^>]*>.*?</A>\s*$',
            re.MULTILINE | re.IGNORECASE | re.DOTALL
        )
        modified = pattern.sub('', modified)
    return modified

def _clean_empty_folders(html_text: str) -> str:
    """修复：兼容多浏览器空文件夹格式，逐级清理空目录"""
    while True:
        soup = BeautifulSoup(html_text, "html.parser")
        empty_h3_texts = []
        for dt in soup.find_all("dt"):
            h3 = dt.find("h3")
            if not h3:
                continue
            dl = dt.find("dl", recursive=False)
            # 判断：文件夹内无任何书签/子文件夹
            if dl and not dl.find_all(["a", "h3", "dt"]):
                folder_name = h3.get_text(strip=True)
                empty_h3_texts.append(folder_name)

        if not empty_h3_texts:
            break

        # 兼容 <DL> / <DL><p> 两种主流书签格式
        for name in empty_h3_texts:
            escaped = re.escape(name)
            pattern = re.compile(
                r'\s*<DT><H3[^>]*>' + escaped + r'</H3>\s*\n\s*<DL(?:><p)?>\s*\n\s*</DL(?:><p)?>\s*',
                re.IGNORECASE | re.DOTALL
            )
            html_text = pattern.sub('', html_text)

    return html_text

def remove_duplicate_bookmarks(html_text: str) -> tuple[str, int]:
    """新增：移除重复书签，返回新文本 + 移除数量"""
    seen = set()
    remove_count = 0
    lines = html_text.splitlines(keepends=True)
    new_lines = []
    pat = re.compile(r'<DT><A\s+[^>]*HREF="([^"]+)"', re.IGNORECASE)

    for line in lines:
        match = pat.search(line)
        if match:
            url = match.group(1)
            if url in seen:
                remove_count += 1
                continue
            seen.add(url)
        new_lines.append(line)
    return "".join(new_lines), remove_count

# ── 主程序入口 ────────────────────────────────────────────────────────────────
def main():
    Colors.init()

    parser = argparse.ArgumentParser(
        description=f"{Colors.CYAN}{Colors.BOLD}Bookmark Cleaner v{__version__}{Colors.RESET} - 浏览器收藏夹失效链接清理工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s bookmarks.html                常规检测清理
  %(prog)s bookmarks.html --dry-run      仅检测，不修改文件
  %(prog)s bookmarks.html --output clean.html  指定输出文件名
  %(prog)s bookmarks.html --csv report.csv     导出CSV报告
  %(prog)s bookmarks.html --proxy http://127.0.0.1:7890  使用代理
  %(prog)s bookmarks.html --only-folder "工作"  仅检测指定文件夹
  %(prog)s bookmarks.html --deduplicate  同时移除重复书签
        """
    )
    parser.add_argument("input", help="输入的收藏夹 HTML 文件路径")
    parser.add_argument("-o", "--output", default="bookmarks_cleaned.html", help="输出文件名 (默认: bookmarks_cleaned.html)")
    parser.add_argument("-w", "--workers", type=int, default=MAX_WORKERS, help=f"并发线程数 (默认: {MAX_WORKERS})")
    parser.add_argument("-t", "--timeout", type=int, default=TIMEOUT_SECS, help=f"超时秒数 (默认: {TIMEOUT_SECS})")
    parser.add_argument("-p", "--proxy", help="HTTP 代理，如 http://127.0.0.1:7890")
    parser.add_argument("--csv", help="导出 CSV 格式报告路径")
    parser.add_argument("--keep-suspicious", action="store_true", help="保留可疑链接（403/429等）")
    parser.add_argument("--dry-run", action="store_true", help="仅检测，不生成清理后的文件")
    parser.add_argument("--no-confirm", action="store_true", help="跳过交互确认，直接清理")
    parser.add_argument("--only-folder", help="仅检测指定文件夹（部分匹配）")
    parser.add_argument("--exclude-folder", help="排除指定文件夹（部分匹配）")
    parser.add_argument("--domain", help="仅检测指定域名（如 github.com）")
    parser.add_argument("--quiet", action="store_true", help="静默模式，仅输出最终结果")
    parser.add_argument("--verbose", action="store_true", help="详细模式，显示每个链接结果")
    parser.add_argument("--deduplicate", action="store_true", help="移除重复书签（仅保留唯一链接）")
    parser.add_argument("-v", "--version", action="version", version=f"%(prog)s {__version__}")

    args = parser.parse_args()

    if not args.quiet:
        try:
            print(f"\n{Colors.CYAN}{Colors.BOLD}{__doc__}{Colors.RESET}\n")
        except UnicodeEncodeError:
            # 降级：跳过ASCII艺术字，仅打印文本信息
            print(f"\n{Colors.CYAN}{Colors.BOLD}Bookmark Cleaner v{__version__} - 浏览器收藏夹失效链接清理工具{Colors.RESET}\n")

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"{Colors.RED}[ERROR] 文件不存在: {input_path}{Colors.RESET}")
        sys.exit(1)

    out_dir = input_path.parent
    cleaned_path = out_dir / args.output
    report_path = out_dir / "report.txt"
    error_log_path = out_dir / "error.log"

    # 自动备份原文件
    backup_path = out_dir / f"{input_path.stem}_backup{input_path.suffix}"
    shutil.copy2(input_path, backup_path)
    if not args.quiet:
        try:
            print(f"{Colors.GREEN}已自动备份原文件: {backup_path}{Colors.RESET}")
        except UnicodeEncodeError:
            print(f"[OK] 已自动备份原文件: {backup_path}")

    # 多编码尝试读取文件
    html_text = None
    used_encoding = None
    encodings = ["utf-8", "gbk", "gb2312", "utf-16"]
    for enc in encodings:
        try:
            html_text = input_path.read_text(encoding=enc)
            used_encoding = enc
            if not args.quiet:
                print(f"\n{Colors.BLUE}[读取] 读取文件: {input_path} | 编码: {enc}{Colors.RESET}")
            break
        except UnicodeDecodeError:
            continue
    # 兜底编码
    if html_text is None:
        used_encoding = "utf-8 (replace)"
        html_text = input_path.read_text(encoding="utf-8", errors="replace")
        if not args.quiet:
            print(f"\n{Colors.YELLOW}[警告] 所有编码尝试失败，使用 utf-8 替换异常字符{Colors.RESET}")

    # 解析HTML
    soup = BeautifulSoup(html_text, "html.parser")
    if not soup.find("a", href=True):
        print(f"{Colors.RED}[ERROR] 未检测到有效书签，请确认文件为浏览器导出的HTML收藏夹{Colors.RESET}")
        sys.exit(1)

    # 提取书签 + 过滤
    bookmarks = extract_bookmarks(soup, args.only_folder, args.exclude_folder)
    if args.domain:
        domain_filter = args.domain.lower()
        bookmarks = [
            (u, f) for u, f in bookmarks
            if urlparse(u).netloc.lower().endswith(domain_filter)
        ]

    urls = [u for u, _ in bookmarks]
    total = len(urls)
    url_counts = Counter(urls)
    duplicates = {u: c for u, c in url_counts.items() if c > 1}
    unique_urls = list(dict.fromkeys(urls))

    # 基础统计
    if not args.quiet:
        print(f"\n{Colors.BLUE}[统计] 书签信息{Colors.RESET}")
        print(f"   总书签字段: {total} 条")
        print(f"   独立URL:    {len(unique_urls)} 个")
        if duplicates:
            print(f"   重复URL:    {len(duplicates)} 个")
        if args.only_folder:
            print(f"   仅检测文件夹: {args.only_folder}")
        if args.exclude_folder:
            print(f"   排除文件夹: {args.exclude_folder}")
        if args.domain:
            print(f"   仅检测域名: {args.domain}")

    if args.dry_run and not args.quiet:
        print(f"\n{Colors.YELLOW}[试运行] 仅检测，不修改文件{Colors.RESET}")

    if not args.quiet:
        print(f"\n{Colors.BLUE}[检测] 开始批量检测链接...{Colors.RESET}\n")

    # 启动检测
    progress = ProgressBar(len(unique_urls), quiet=args.quiet or len(unique_urls) < 5)
    results: dict[str, tuple[bool | None, str]] = {}

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        future_map = {
            executor.submit(check_url, u, args.timeout, args.proxy): u
            for u in unique_urls
        }
        for future in as_completed(future_map):
            try:
                url, alive, reason, skipped = future.result()
            except Exception as e:
                url = future_map[future]
                alive, reason, skipped = None, f"检测异常: {str(e)[:40]}", False

            results[url] = (alive, reason)
            progress.update(alive, skipped)

            if args.verbose and not args.quiet:
                status_tag = "[OK]" if alive else "[DEAD]" if alive is False else "[?]"
                print(f"  {status_tag} {sanitize_url(url)[:60]:60s} ({reason})")

    elapsed = time.time() - progress.start_time
    skipped_count = progress.stats.get('skipped', 0)

    # 分类失效/可疑链接
    dead_urls = set()
    suspicious_urls = set()
    for u, (alive, _) in results.items():
        if alive is False:
            dead_urls.add(u)
        elif alive is None:
            suspicious_urls.add(u)
            if not args.keep_suspicious:
                dead_urls.add(u)

    dead_count = sum(1 for u in urls if u in dead_urls)
    suspicious_count = sum(1 for u in urls if u in suspicious_urls)

    # 输出汇总报告
    print(f"\n{Colors.BOLD}{'='*65}{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}[完成] 检测完毕，总耗时 {elapsed:.1f} 秒{Colors.RESET}")
    print(f"   ✅ 有效链接:   {total - dead_count:5d}")
    if suspicious_urls:
        tip = "（已删除）" if not args.keep_suspicious else "（已保留）"
        print(f"   ⚠️ 可疑链接:   {suspicious_count:5d} {tip}")
    print(f"   ❌ 失效链接:   {dead_count - (0 if args.keep_suspicious else suspicious_count):5d}")
    if skipped_count:
        print(f"   ⏭️ 跳过检测:   {skipped_count:5d} (短链接/非HTTP协议)")
    print(f"{Colors.BOLD}{'='*65}{Colors.RESET}")

    # 交互确认
    remove_dup_count = 0
    if not args.dry_run and not args.no_confirm and dead_urls:
        print(f"\n{Colors.YELLOW}⚠️ 即将删除 {dead_count} 条失效链接{Colors.RESET}")
        if sys.stdin.isatty():
            resp = input("   确认继续? [y/N] ").strip().lower()
        else:
            print("   非交互环境，自动取消（使用 --no-confirm 静默执行）")
            resp = 'n'
        if resp not in ("y", "yes"):
            print(f"{Colors.YELLOW}[取消] 用户终止操作{Colors.RESET}")
            sys.exit(2)

    # 执行清理逻辑
    if not args.dry_run:
        cleaned_html = remove_dead_bookmarks(html_text, dead_urls)
        # 去重
        if args.deduplicate:
            cleaned_html, remove_dup_count = remove_duplicate_bookmarks(cleaned_html)
            print(f"\n{Colors.GREEN}[去重] 已移除 {remove_dup_count} 条重复书签{Colors.RESET}")
        # 清理空文件夹
        cleaned_html = _clean_empty_folders(cleaned_html)
        # 写入文件
        cleaned_path.parent.mkdir(parents=True, exist_ok=True)
        cleaned_path.write_text(cleaned_html, encoding="utf-8")
        print(f"\n{Colors.GREEN}[保存] 清理后文件已输出: {cleaned_path}{Colors.RESET}")

    # 生成 TXT 报告
    report_lines = [
        "# Bookmark Cleaner 检测报告",
        "# ⚠️ 警告: 此文件包含您的书签数据（敏感参数已自动脱敏），请勿分享！",
        f"版本: v{__version__}",
        f"检测时间: {time.strftime('%Y-%m-%d %H:%M:%S')}",
        f"原始书签: {total} 条 | 删除失效: {dead_count} 条 | 移除重复: {remove_dup_count} 条",
        "",
    ]
    if suspicious_urls:
        report_lines.extend(["## ⚠️ 可疑链接（建议人工复核）", ""])
        for u in sorted(suspicious_urls):
            _, reason = results[u]
            report_lines.append(f"- [{reason}]  {sanitize_url(u)}")
        report_lines.append("")
    report_lines.extend(["## ❌ 确认失效链接", ""])
    for u in sorted(dead_urls - suspicious_urls):
        _, reason = results[u]
        report_lines.append(f"- [{reason}]  {sanitize_url(u)}")
    if duplicates:
        report_lines.extend(["", "## 🔁 重复书签统计", ""])
        for u, c in sorted(duplicates.items(), key=lambda x: -x[1]):
            report_lines.append(f"- 重复 {c} 次: {sanitize_url(u)}")
    report_path.write_text("\n".join(report_lines), encoding="utf-8")

    # 生成错误日志
    error_lines = [
        f"# 检测错误日志 - {time.strftime('%Y-%m-%d %H:%M:%S')}",
        "# ⚠️ 警告: 此文件包含您的书签数据（敏感参数已自动脱敏），请勿分享！",
        ""
    ]
    for u, (_, reason) in results.items():
        if "异常" in reason or "错误" in reason:
            error_lines.append(f"{sanitize_url(u)} | {reason}")
    if len(error_lines) > 3:
        error_log_path.write_text("\n".join(error_lines), encoding="utf-8")
        if not args.quiet:
            print(f"{Colors.YELLOW}[错误日志] 异常链接详情: {error_log_path}{Colors.RESET}")

    # 生成 CSV 报告（新增重复次数字段）
    if args.csv:
        with open(args.csv, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(['URL（敏感参数已脱敏）', '状态', '原因', '所在文件夹', '重复次数'])
            for url, folder in bookmarks:
                alive, reason = results.get(url, (None, "未检测"))
                status = "有效" if alive else "失效" if alive is False else "可疑"
                cnt = url_counts.get(url, 1)
                writer.writerow([sanitize_url(url), status, reason, folder, cnt])
        if not args.quiet:
            print(f"{Colors.GREEN}[CSV报告] 数据已导出: {args.csv}{Colors.RESET}")

    if not args.quiet:
        print(f"{Colors.GREEN}[报告] 详细文本报告: {report_path}{Colors.RESET}")
        print(f"\n{Colors.GREEN}{Colors.BOLD}[全部任务执行完成！]{Colors.RESET}")
        print(f"{Colors.YELLOW}🔒 隐私提示: 报告文件中的敏感URL参数已自动脱敏(token/key/secret等){Colors.RESET}")
        if not args.dry_run:
            print(f"   请将 {args.output} 导入浏览器使用")
        print()

if __name__ == "__main__":
    main()