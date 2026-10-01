# 公考评论订阅源 + ePub 合集

把三套官方评论（**人民锐评 / 人民日报评论 / 浙江宣传**）+ 实时源（**求是网**）爬取为「含全文」的 RSS，并打包成 ePub，方便在阅读 App、KOReader、微信读书、Kindle 上订阅 / 导入。

内容托管在 GitHub + jsDelivr CDN：**分发层自动**——手机订阅后自动拉取最新文章，手机端零常开。但**「抓取生成」这一环需要本机参与**（详见「六、本机更新」）：须在国内 IP 的电脑上跑一次 `update_rss.bat`（手动，或配 Windows 任务计划程序实现每日自动）。GitHub Actions 因美国 IP 被人民网/浙江在线限流，无法自动抓取。

---

## 一、本仓库内含资源

| 文件 | 说明 | 规模 |
|------|------|------|
| `rmrp.xml` | 人民锐评 RSS（含全文） | 209 篇，2026-05-17 ~ 10-01 |
| `rmrb_comment.xml` | 人民日报评论 RSS（含全文） | 200 篇，2025-08-22 ~ 2026-10-01 |
| `zjxc.xml` | 浙江宣传 RSS（含全文） | 197 篇，2026-05-31 ~ 10-01 |
| `人民锐评.epub` | 离线合集（全量） | 209 篇 / 514 KB |
| `人民日报评论.epub` | 离线合集（全量） | 200 篇 / 646 KB |
| `浙江宣传.epub` | 离线合集（全量） | 197 篇 / 948 KB |
| `求是网.epub` | 离线快照（静态，实时源见下） | 近 30 天 |
| `feeds.opml` | 人民锐评 + 求是网 一组（KOReader/OPML 用） | — |
| `rmrp_rss_source.json` | 阅读 App 订阅源规则（三套源合并，一键导入） | — |
| `rmrp_rss.py` / `rmrb_comment_rss.py` / `zjxc_rss.py` | 三个 RSS 生成器（国内 IP 跑） | — |
| `build_epub.py` / `rss2epub.py` | ePub 构建脚本 | — |
| `update_rss.bat` / `update_and_push.py` | 本机一键更新（国内 IP 抓取 + 重建 + 推送） | — |
| `.github/workflows/update_rss.yml` | 每日自动更新（含定时；人民锐评 3414 接口失败则保留旧文件） | — |

---

## 二、在阅读 App（Legado）订阅

**方式 A · RSS 直接订阅**（推荐，自动追更）
订阅页 → 点 + → 添加 RSS 源，分别填下面 jsDelivr 链接：

- 人民锐评：`https://cdn.jsdelivr.net/gh/boxiaoyi/rmrp-rss@main/rmrp.xml`
- 人民日报评论：`https://cdn.jsdelivr.net/gh/boxiaoyi/rmrp-rss@main/rmrb_comment.xml`
- 浙江宣传：`https://cdn.jsdelivr.net/gh/boxiaoyi/rmrp-rss@main/zjxc.xml`

> 把 `boxiaoyi/rmrp-rss` 换成你自己的 `用户名/仓库名`；`@main` 须与仓库默认分支一致（若是 `master` 改 `@master`）。这是 RSS 地址，在阅读「订阅」里粘贴即可，**不走**二维码/订阅源导入。

**方式 B · 订阅源规则一键导入**（三套源一次到位）
我的 → 订阅源管理 → 右上 + → 网络导入 / 本地导入 → 选 `rmrp_rss_source.json`。

---

## 三、在 KOReader（墨水屏）订阅

**方式 A · 内置 News downloader**（无需插件）
主菜单 → **News downloader (RSS/Atom)** → **Edit news feeds**，分别添加上面三个 jsDelivr URL；求是网额外加 `https://rsshub.dicomp.net/qstheory/toutiao`。回到上层点 **Sync news feeds** 即拉取，每篇存成离线文件。

**方式 B · rssreader 插件**（支持 OPML 批量导入）
把本仓库 `feeds.opml` 拷到 `plugins/rssreader.koplugin/` 下，主菜单 → **RSS Reader** → **Settings → Import from OPML**，选 `feeds.opml` 即可导入「人民锐评 + 求是网」两组。

---

## 四、微信读书（无原生 RSS，用 ePub）

微信读书不支持 RSS，用 ePub 导入：
**我 → 导入图书**（WiFi 传书 / 本地文件 / 网盘）→ 选 `人民锐评.epub` 等。

- ePub 是**静态快照**，不会自动更新；想看新版重跑脚本再导入。
- 想要「最新 30 篇」精简版：`python rss2epub.py -i rmrp.xml -o 人民锐评.epub -n 30`

---

## 五、Kindle（用 ePub）

把 `人民锐评.epub` 等通过邮箱 / USB 导入 Kindle。脚本已统一正文 `text-indent:2em`，如需再调排版，用 Calibre 转换时**删多余样式 + 首段缩进设 2 字符**即可，不会叠加成 4 字。

---

## 六、本机更新（推荐每日，须在国内 IP）

双击 `update_rss.bat`（或命令行 `python update_and_push.py`）：会用**国内 IP** 重新抓取三套源、重建四个 ePub、并 `git push` 到仓库。

> ⚠️ 国内网络不是必须——GitHub Actions 每天会自动跑（见 `update_rss.yml`），浙江宣传 / 人民日报评论静态页从美 IP 也能抓。但人民锐评的 3414 接口美 IP 可能取不到；若 Action 日志出现 `::warning::3414 接口未取到内容`，说明需要本机在国内 IP 跑一次补上，或改用下方任务计划程序方案。

### 想要「全自动零常开」？配 Windows 任务计划程序

在 Windows「任务计划程序」里新建一个**每日**任务，操作为启动 `update_rss.bat`，触发器设「每天 08:00」并勾选「唤醒计算机运行此任务」。只要当天电脑开机且在国内网络，就会自动抓取 + 推送，你完全不用手动点；电脑关机那天不更新，开机后次日自动补上。

一行命令（管理员 PowerShell 运行，按实际路径改）即可创建：
```powershell
schtasks /create /tn "rmrp-rss每日更新" /tr '"C:\Users\Lee\WorkBuddy\2026-09-30-15-45-09\rmrp-rss\update_rss.bat"' /sc daily /st 08:00 /rl limited /f
```
> 前提：本仓库已 `git push` 过一次、且 git 凭据已保存（Windows 凭据管理器），否则自动任务会因要输密码而卡住。

---

## 七、上传到 GitHub

本目录已 `git init` 并关联远程 `origin = https://github.com/boxiaoyi/rmrp-rss.git`。
上传步骤见 **`上传到GitHub.md`**（审阅后 `git add -A && git commit && git push` 即可）。

---

## 八、常见问题

- **阅读 App 刷新后还是只有 3 篇 / 旧文**：之前若加过多个同名源，进「订阅源管理」删掉只留指向 jsDelivr 的那一个，再刷新。
- **jsDelivr 看不到刚更新的文章**：CDN 有缓存，等几分钟；或访问 `https://purge.jsdelivr.net/gh/boxiaoyi/rmrp-rss@main/rmrp.xml` 强制刷新。
- **Kindle 连不上 raw.githubusercontent.com**：一律改用上面的 jsDelivr 链接（国内可直连）。
- **怎么判断 Action 有没有抓到人民锐评新内容**：GitHub 仓库 → Actions → 最新一次运行 → 搜 `3414` 或 `人民锐评已更新` / `3414 接口未取到内容`：`::notice::人民锐评已更新` 即成功，`::warning::3414` 即被墙需本机补。
