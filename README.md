<div align="center">

# 🔖 Bookmark Cleaner
### 浏览器收藏夹失效链接批量清理工具

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Version](https://img.shields.io/badge/Version-1.1.0-orange.svg)]()
[![Stars](https://img.shields.io/github/stars/lynx2016/bookmark-cleaner.svg)]()

**一键检测并清理浏览器收藏夹中的死链、404页面、重复书签和空文件夹**

</div>

---

## 📖 项目简介

日常使用浏览器会积累大量收藏链接，长期使用后会产生**失效链接、404 页面、过期域名、重复书签、空文件夹**等问题，手动清理耗时费力。

**Bookmark Cleaner** 是一款基于 Python 开发的书签整理工具，专门针对浏览器导出的 HTML 书签文件进行批量检测与清理。

工具采用多线程并发检测，内置完善的异常处理与日志系统，全平台兼容，安全稳定。

✅ **支持浏览器**：Chrome、Edge、Firefox、360 浏览器、搜狗浏览器等所有可导出 HTML 书签的浏览器。

---

## ✨ 核心功能

### 🔍 智能链接检测
- 自动识别 `400~599` 各类失效状态码，精准标记死链
- 区分**可疑链接**（401/403/429/503/504），支持自定义保留/删除
- 自动跳过短链接域名、本地文件、磁力链等非 HTTP/HTTPS 链接
- 细化错误类型：连接超时、SSL 证书错误、DNS 解析失败、连接重置、重定向异常等
- 优先使用 `HEAD` 请求，请求失败自动降级为 `GET` 请求重试

### 🧹 一键自动清理
- 批量删除所有失效链接
- 递归清理空书签文件夹，兼容多浏览器书签格式
- 一键去重，自动移除重复书签（仅保留唯一链接）
- **运行前自动备份原始书签**，彻底避免数据丢失

### 📊 多格式报告输出
- 文本报告 `report.txt`：分类展示死链、可疑链接、重复链接
- CSV 表格报告：支持 Excel / WPS 直接打开查看与统计
- 独立错误日志 `error.log`：单独汇总检测异常、请求失败链接

### ⚙️ 增强特性
- 自适应多线程并发，合理利用系统硬件资源
- 全局请求连接池 + 随机延迟重试，有效规避网站封禁
- 完整代理支持，适配特殊网络环境
- 支持文件夹黑白名单、指定域名筛选检测
- 全平台终端适配：Windows / Linux / macOS 颜色、进度条正常显示
- 提供静默模式、详细日志、免交互执行，可用于自动化脚本/服务器定时任务

---

## 🚀 快速开始

### 1. 环境要求
- Python 3.8 及以上版本

### 2. 安装依赖
打开终端/命令行，执行以下命令安装所需第三方库：

```bash
pip install requests beautifulsoup4
```

### 3. 导出浏览器书签

使用工具前，先将浏览器收藏夹导出为标准 HTML 文件：

**Chrome / Edge:**
1. 打开书签管理器（快捷键：`Ctrl+Shift+O`）
2. 点击右上角菜单 → **导出书签**
3. 保存为 `bookmarks.html`

**Firefox:**
1. 书签 → 管理书签（快捷键：`Ctrl+Shift+B`）
2. 导入和备份 → **导出书签到 HTML**

### 4. 基础运行

将导出的 `bookmarks.html` 与脚本 `check_bookmarks.py` 放在同一目录，执行基础命令：

```bash
# 常规检测 + 清理失效链接 + 自动备份原文件
python check_bookmarks.py bookmarks.html
```

---

## 📝 完整命令参数

```bash
usage: check_bookmarks.py [-h] [-o OUTPUT] [-w WORKERS] [-t TIMEOUT] [-p PROXY]
                          [--csv CSV] [--keep-suspicious] [--dry-run]
                          [--no-confirm] [--only-folder ONLY_FOLDER]
                          [--exclude-folder EXCLUDE_FOLDER] [--domain DOMAIN]
                          [--quiet] [--verbose] [--deduplicate] [-v]
                          input

Bookmark Cleaner v1.1.0 - 浏览器收藏夹失效链接清理工具

positional arguments:
  input                 输入的收藏夹 HTML 文件路径

options:
  -h, --help            显示帮助信息并退出
  -o, --output OUTPUT   输出文件名 (默认: bookmarks_cleaned.html)
  -w, --workers WORKERS 并发线程数 (自动适配CPU，默认上限20)
  -t, --timeout TIMEOUT 请求超时秒数 (默认: 10)
  -p, --proxy PROXY     设置HTTP代理，格式: http://127.0.0.1:7890
  --csv CSV             导出CSV格式报告，指定文件路径
  --keep-suspicious     保留可疑链接(403/429/503等)，不自动删除
  --dry-run             仅检测链接，不生成清理后的文件（试运行）
  --no-confirm          跳过交互确认，直接执行清理（适合脚本运行）
  --only-folder ONLY_FOLDER
                        仅检测指定文件夹（部分匹配）
  --exclude-folder EXCLUDE_FOLDER
                        排除指定文件夹（部分匹配）
  --domain DOMAIN       仅检测指定域名（例：github.com）
  --quiet               静默模式，仅输出最终结果
  --verbose             详细模式，打印每一条链接的检测结果
  --deduplicate         移除重复书签，仅保留唯一链接
  -v, --version         查看程序版本
```

---

## 🧪 常用使用示例

### 1. 试运行（仅检测，不修改文件，推荐先预览）
```bash
python check_bookmarks.py bookmarks.html --dry-run
```

### 2. 检测清理 + 自动去除重复书签
```bash
python check_bookmarks.py bookmarks.html --deduplicate
```

### 3. 搭配代理访问境外链接
```bash
python check_bookmarks.py bookmarks.html --proxy http://127.0.0.1:7890
```

### 4. 保留 403 / 429 / 5xx 等可疑链接，不自动删除
```bash
python check_bookmarks.py bookmarks.html --keep-suspicious
```

### 5. 导出 CSV 表格报告（Excel 可用）
```bash
python check_bookmarks.py bookmarks.html --csv report.csv
```

### 6. 仅检测指定文件夹内的书签
```bash
python check_bookmarks.py bookmarks.html --only-folder "工作"
```

### 7. 免交互静默执行（服务器 / 定时脚本专用）
```bash
python check_bookmarks.py bookmarks.html --no-confirm --quiet
```

---

## 📂 输出文件说明

工具运行后，会在原文件同目录自动生成以下文件：

| 文件名称 | 用途说明 |
|---------|---------|
| `xxx_backup.html` | **原始书签自动备份文件**，防止误操作丢失数据 |
| `bookmarks_cleaned.html` | 清理完成后的书签文件，直接导入浏览器即可使用 |
| `report.txt` | 综合文本报告，包含统计数据、死链、可疑链接、重复链接 |
| `error.log` | 独立错误日志，记录检测异常、请求失败的链接 |
| 自定义 `.csv` | 结构化表格报告，包含 URL、状态、原因、文件夹、重复次数 |

> 💡 **建议**：试运行核对结果无误后，再将 `bookmarks_cleaned.html` 导入浏览器。

---

## 🛡️ 安全声明

1. ✅ 本工具**纯本地运行**，不会上传任何书签、链接、隐私数据至外网
2. ✅ 每次运行自动备份原始书签文件，多重保障数据安全
3. ✅ 网络请求仅用于检测链接可用性，无数据采集、窃取行为
4. ✅ 代码完全开源，可自由查阅、审计与二次开发

---
## ❓ 常见问题

### Q: 为什么有些网站明明能打开却被标记为失效？

A: 主要原因：

1. **Cloudflare 反爬**：返回 403，已被标记为 "可疑链接"，加 `--keep-suspicious` 可保留

2. **地区限制**：服务器在国外，国内检测超时，使用 `--proxy` 即可

3. **User\-Agent 拦截**：已使用最新 Chrome UA，大部分网站可通过

### Q: 几千条链接会不会很慢？

A: 20 线程下，1000 条链接约 1\-2 分钟，5000 条约 5\-10 分钟。

### Q: 支持哪些浏览器？

A: 支持所有主流浏览器导出的标准 Netscape 书签 HTML 格式：
Chrome、Edge、Firefox、Safari、Opera、Brave、Vivaldi 等。

### Q: 会泄露我的收藏夹数据吗？

A: 绝对不会！所有检测都在本地完成，代码开源可审计，没有任何数据上传。

### Q: 清理后文件夹结构会乱吗？

A: 不会！完美保留原有的文件夹层级、嵌套结构、书签顺序。只会删除失效链接条目。

---
## 🐛 问题反馈 & 开发规划

### 兼容性说明
- 完全兼容主流浏览器导出的标准 HTML 书签文件
- Windows CMD / PowerShell、Linux、macOS 终端均正常适配颜色与进度条

### 问题反馈
如果遇到 Bug、兼容性问题、功能建议，欢迎提交 [Issues](https://github.com/lynx2016/bookmark-cleaner/issues)

### 后续开发计划
- [ ] 支持 JSON 格式书签导入 / 导出
- [ ] 新增书签分类、文件夹批量重命名功能
- [ ] 支持本地定时自动扫描书签
- [ ] 开发图形化界面（GUI）版本
- [ ] 支持批量检测重定向并自动更新链接

---

## 📄 开源协议

本项目基于 **MIT License** 开源。

你可以自由使用、修改、分发本项目代码，使用时请保留原始开源协议声明。

---

## 🙏 致谢

感谢以下优秀开源库提供技术支持：

- [requests](https://github.com/psf/requests) — 简洁强大的 HTTP 请求库
- [BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/) — HTML/XML 解析工具

---

## 💡 使用小贴士

1. 首次使用建议先加上 `--dry-run` 试运行，核对检测结果
2. 对于标记为**可疑链接**的内容，建议人工二次复核
3. 书签数量庞大时，可适当调大 `--workers` 参数提升检测速度
4. 境外链接访问异常时，配合 `--proxy` 代理参数使用
5. 清理完成后，建议在浏览器中删除原有书签后再导入清理后的文件

---


如果这个工具对你有帮助，欢迎给个 ⭐ Star 支持一下！

</div>


---

Made with ❤️ for a cleaner bookmark experience
