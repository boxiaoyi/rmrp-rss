#!/usr/bin/env python3
# 本机(国内IP)一键生成三个RSS并推送到 GitHub，再刷新 jsDelivr 缓存。
# 用本机跑的原因：GitHub Actions 在美国IP，浙江在线/人民网会限流，
#               生成的 zjxc.xml / rmrb_comment.xml 抓不到最新文章。
# 用法: python update_and_push.py   （在 rmrp-rss/ 目录下运行）
import os, re, sys, subprocess, shutil, time, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.environ.get("RMREPO", HERE)          # 默认本脚本所在目录即为仓库
REPO_NAME = "boxiaoyi/rmrp-rss"                # 改成你的 用户名/仓库
BRANCH = "main"                                # 若仓库默认分支是 master，改这里

# min: 硬性最少篇数；低于此数且低于旧文件50%则判定为抓取失败，保留旧文件
SOURCES = [
    {"name": "人民锐评",     "script": "rmrp_rss.py",        "xml": "rmrp.xml",           "min": 20},
    {"name": "浙江宣传",     "script": "zjxc_rss.py",        "xml": "zjxc.xml",           "min": 20},
    {"name": "人民日报评论", "script": "rmrb_comment_rss.py","xml": "rmrb_comment.xml",   "min": 20},
]


def run(cmd):
    return subprocess.run(cmd, cwd=REPO, capture_output=True, text=True,
                          encoding="utf-8", errors="ignore")


def count_items(path):
    if not os.path.exists(path):
        return 0
    return open(path, encoding="utf-8", errors="ignore").read().count("<item>")


def purge(files):
    for f in files:
        url = "https://purge.jsdelivr.net/gh/%s@%s/%s" % (REPO_NAME, BRANCH, f)
        try:
            urllib.request.urlopen(url, timeout=15)
            print("  ✓ 已刷新缓存", f)
        except Exception as e:
            print("  ! 缓存刷新失败(可忽略，稍后自动生效)", f, e)


def git(*args):
    r = run(["git"] + list(args))
    return r.returncode == 0, (r.stdout + r.stderr).strip()


def main():
    accepted = []
    for s in SOURCES:
        tmp = os.path.join(HERE, "_tmp_%s" % s["xml"])
        print("▶ 生成【%s】..." % s["name"])
        r = run([sys.executable, os.path.join(HERE, s["script"]), "-o", tmp])
        if r.returncode != 0:
            print("  ✗ 生成器报错，跳过：", r.stderr[:200])
            continue
        new_n = count_items(tmp)
        old_n = count_items(os.path.join(REPO, s["xml"]))
        floor = max(s["min"], int(old_n * 0.5))   # 防境外IP/断网把好内容洗掉
        if new_n < floor:
            print("  ✗ 篇数异常(新%d < 阈值%d)，保留旧文件，跳过" % (new_n, floor))
            try: os.remove(tmp)
            except: pass
            continue
        shutil.move(tmp, os.path.join(REPO, s["xml"]))
        print("  ✓ %s：%d 篇（旧 %d）" % (s["name"], new_n, old_n))
        accepted.append(s["xml"])

    if not accepted:
        print("\n没有可更新的源，结束。")
        return

    print("\n▶ 提交到 GitHub ...")
    git("config", "user.name", "rmrp-local")
    git("config", "user.email", "local@example.com")
    git("add", *accepted)
    ok, msg = git("commit", "-m", "chore: 本机更新评论RSS %s" % time.strftime("%F"))
    if not ok and ("nothing to commit" in msg or "无变化" in msg or "no changes" in msg):
        print("  无变化，无需推送。")
    elif not ok:
        print("  ✗ 提交失败：", msg)
        return
    else:
        print("  ✓ 已提交")
    ok2, msg2 = git("push", "-u", "origin", BRANCH)
    print("  push:", "成功" if ok2 else ("失败: " + msg2))
    print("\n▶ 刷新 jsDelivr 缓存 ...")
    purge(accepted)
    print("\n完成。阅读App里下拉刷新即可看到新文章。")


if __name__ == "__main__":
    main()
