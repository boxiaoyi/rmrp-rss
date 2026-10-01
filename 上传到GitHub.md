# 上传到 GitHub

本目录已**完全搭好**（脚本 / XML / 配置齐全，临时调试文件已清理），并已 `git init` 且关联远程：

```
origin = https://github.com/boxiaoyi/rmrp-rss.git
```

你只需做「提交 + 推送」这一步即可。

> 关于 `.epub`：本机已生成 4 个 ePub 给 Kindle/微信读书用，但**已写进 `.gitignore`**，命令行推送不会带上它们（仓库只服务 RSS/CDN，不需要 ePub）。如果你用网页拖拽上传，可自己决定是否把 `.epub` 一起拖进去（不影响订阅，只是仓库会大几 MB）。

---

## 方式一：网页拖拽（最省事、不会踩 git 历史坑，推荐）

1. 打开 https://github.com/new 新建一个**公开**仓库，名字 `rmrp-rss`（若已存在旧仓库，直接进旧仓库走第 2 步）。
2. 进仓库 → **Add file** → **Upload files**，把本目录**全部内容**拖进去：
   - 三个 `.xml`（rmrp.xml / rmrb_comment.xml / zjxc.xml）
   - 各 `.py`、`.opml`、`.json`、`README.md`、`.gitignore`、以及 `上传到GitHub.md`
   - **含隐藏的 `.github` 文件夹**（里面有 `update_rss.yml`，必须一起上传，否则没有自动更新）
3. 写个提交说明，点 **Commit changes** 即可。
4. 之后进仓库 **Actions** 标签，看 `更新评论RSS` 这条能否跑通（见下方「上传后验证」）。

---

## 方式二：命令行（已帮你 init + 关联远程）

⚠️ 你的 GitHub 仓库里**已经有旧文件（旧 history）**，而本目录是全新 `git init`、和远端没有共同祖先，直接 `git push` 会被拒（"unrelated histories"）。两种解法：

**解法 A（干净，推荐）：先拉后推**
```bash
cd 进本目录 rmrp-rss
git pull origin main --allow-unrelated-histories   # 把远端旧文件并入
git add -A
git commit -m "feat: 三套评论源 + 自动更新 workflow"
git push -u origin main
```

**解法 B（暴力覆盖，仅当你确认这仓库只干这一件事）：**
```bash
git add -A
git commit -m "feat: 三套评论源 + 自动更新 workflow"
git push -u origin main --force
```

首次 push 需要 **GitHub 用户名 + Personal Access Token**（不是登录密码）：
- GitHub → Settings → Developer settings → Personal access tokens → 生成，勾选 `repo`。
- push 时密码框粘贴该 token。

> 默认分支若是 `master` 而不是 `main`，上面所有 `main` 换成 `master`。

---

## 上传之后 · 验证 Action 是否抓到人民锐评新内容

进仓库 **Actions** → `更新评论RSS` → 最新一次运行 → 展开日志，搜 `3414`：

- 看到 **`::notice::人民锐评已更新（3414 接口正常）`** → 美国 IP 也能抓，全自动搞定，以后每天北京 08:17 自动更新。
- 看到 **`::warning::3414 接口未取到内容，保留旧 rmrp.xml`** → 该接口从 GitHub 美 IP 被墙，Action 不会覆盖你本地推的好内容，但也不会自动追人民锐评当日新文。此时改用「本机任务计划程序」方案（README 第六节）才能保证人民锐评也自动当天更新。

> 不论哪种，先在**国内 IP 的本机**跑一次 `update_rss.bat` 把最新 `rmrp.xml`（含 10-01）推上去打底，再让 Action 接手，最稳。
