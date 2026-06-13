> 专业的浏览器收藏夹失效链接清理工具
> 
> 

一键检测并清理浏览器收藏夹中的死链、404 页面、失效网站。支持 Chrome、Edge、Firefox、Safari 等所有主流浏览器导出的 HTML 格式。

---

## ✨ 功能特性

### 🚀 核心功能

- **多线程并发检测**：默认 20 线程，上千条链接分钟级完成

- **智能误判防护**：HEAD 不支持自动降级 GET，误判率 \< 5%

- **完整保留结构**：清理后完美保留原文件夹层级和排序

- **递归空文件夹清理**：自动清理删除后产生的空目录

### 🛡️ 安全机制

- **自动备份**：运行即自动备份原文件，永不丢失数据

- **可疑链接识别**：智能识别反爬、限流、维护中站点，不盲目删除

- **交互式确认**：删除前二次确认，防止误操作

- **失败重试机制**：网络波动自动重试 2 次

### 🎯 精准检测

- **状态码细分**：401/403/429/503 标记为 "待人工确认"

- **短链接白名单**：自动跳过 \[t\.co\]\(t\.co\)、\[bit\.ly\]\(bit\.ly\)、[url\.cn](https://url.cn)、[t\.cn](https://t.cn) 等 20\+ 种跳转服务

- **错误类型细分**：SSL 错误、DNS 失败、连接拒绝、超时等

- **非 HTTP 协议自动跳过**：file://、ftp://、javascript: 等

### ⚙️ 灵活可控

|选项|功能|
|---|---|
|`--dry-run`|**试运行模式**：仅检测不修改，推荐首次使用|
|`--output`|自定义输出文件名|
|`--keep-suspicious`|保留可疑链接，保守模式|
|`--proxy`|HTTP 代理支持，解决国外网站访问问题|
|`--csv`|导出 CSV 报告，Excel 友好|
|`--only-folder`|仅检测指定文件夹|
|`--exclude-folder`|排除指定文件夹|
|`--domain`|仅检测指定域名|

### 💎 用户体验

- **实时进度条 \+ ETA**：剩余时间一目了然

- **彩色终端输出**：状态清晰可辨

- **静默 / 详细模式**：按需选择输出级别

- **重复书签检测**：自动找出重复收藏

- **编码自动识别**：兼容 Windows GBK / UTF\-8

---

## 🚀 快速开始

### 1\. 安装依赖

```bash
pip install requests beautifulsoup4
```

### 2\. 导出浏览器收藏夹

- **Chrome/Edge**: 地址栏输入 `chrome://bookmarks/` → 右上角三个点 → 导出书签

- **Firefox**: 书签 → 管理书签 → 导入和备份 → 导出书签为 HTML

- **Safari**: 文件 → 导出 → 书签

### 3\. 运行检测（推荐先试运行）

```bash
# 🔍 推荐：先试运行，只检测不修改
python check_bookmarks.py 你的收藏夹.html --dry-run

# ✅ 确认无误后，正式清理
python check_bookmarks.py 你的收藏夹.html
```

### 4\. 导入清理后的文件

将生成的 `bookmarks_cleaned.html` 导入浏览器即可。

---

## 📖 完整使用文档

### 基础用法

```bash
# 常规清理
python check_bookmarks.py bookmarks.html

# 自定义输出文件名
python check_bookmarks.py bookmarks.html -o my_bookmarks.html

# 保留可疑链接（保守模式）
python check_bookmarks.py bookmarks.html --keep-suspicious
```

### 高级用法

```bash
# 使用代理（解决 Cloudflare / 国外网站检测问题）
python check_bookmarks.py bookmarks.html --proxy http://127.0.0.1:7890

# 仅检测"工作"文件夹
python check_bookmarks.py bookmarks.html --only-folder "工作"

# 排除"临时"文件夹
python check_bookmarks.py bookmarks.html --exclude-folder "临时"

# 仅检测 github.com 的链接
python check_bookmarks.py bookmarks.html --domain github.com

# 导出 CSV 报告
python check_bookmarks.py bookmarks.html --csv report.csv

# 详细模式：显示每个链接的检测结果
python check_bookmarks.py bookmarks.html --verbose
```

### 所有参数

```Plain Text
positional arguments:
  input                 输入的收藏夹 HTML 文件路径

options:
  -h, --help            显示帮助信息
  -o OUTPUT, --output OUTPUT
                        输出文件名 (默认: bookmarks_cleaned.html)
  -w WORKERS, --workers WORKERS
                        并发线程数 (默认: 20)
  -t TIMEOUT, --timeout TIMEOUT
                        超时秒数 (默认: 10)
  -p PROXY, --proxy PROXY
                        HTTP 代理，如 http://127.0.0.1:7890
  --csv CSV             导出 CSV 格式报告
  --keep-suspicious     保留可疑链接（403/429等）
  --dry-run             仅检测，不生成清理后的文件
  --no-confirm          跳过确认直接清理
  --only-folder ONLY_FOLDER
                        仅检测指定文件夹（部分匹配）
  --exclude-folder EXCLUDE_FOLDER
                        排除指定文件夹（部分匹配）
  --domain DOMAIN       仅检测指定域名（如 github.com）
  --quiet               静默模式，仅输出最终结果
  --verbose             详细模式，显示每个链接结果
  -v, --version         显示版本号
```

---

## 📊 输出示例

### 运行界面

```Plain Text
[████████████████████████████░░░░░░]  752/1000  75% | ✅680 ❌65 ⚠️7 | ETA 0m12s
```

### 检测报告

```Plain Text
=================================================================
📊 检测完成，耗时 45.2 秒
   ✅ 有效链接:     872
   ❌ 失效链接:     115
   ⚠️  可疑链接:      13 （已删除）
=================================================================

⚠️  即将删除 128 条失效链接
   确认继续? [Y/n]
```

### 生成文件

- `bookmarks_cleaned.html` \- 清理后的收藏夹，可直接导入浏览器

- `report.txt` \- 详细检测报告（失效链接清单、重复书签等）

- `xxx_backup.html` \- 原文件自动备份

- `report.csv` \- CSV 格式报告（可选）

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

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库

2. 创建特性分支 \(`git checkout -b feature/AmazingFeature`\)

3. 提交更改 \(`git commit -m 'Add some AmazingFeature'`\)

4. 推送到分支 \(`git push origin feature/AmazingFeature`\)

5. 开启 Pull Request

---

## 📄 许可证

MIT License \- 可自由使用、修改、分发。

---

## ⭐ 支持

如果这个工具帮到了你，请给个 Star ⭐ 支持一下！

---

Made with ❤️ for a cleaner bookmark experience
