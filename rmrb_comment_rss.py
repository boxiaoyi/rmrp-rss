#!/usr/bin/env python3
# 人民日报评论 RSS 生成器（合并人民网观点频道核心子栏目，含全文正文）
# 用法: python rmrb_comment_rss.py -o rmrb_comment.xml
# 说明: 人民日报评论(微信公众号)内容同步发布于人民网观点频道，分散在多个子栏目。
#       本脚本合并以下子栏目（不含 436867 人民锐评——用户已有独立源，避免重复）:
#         人民时评 / 人民论坛 / 本报评论员 / 人民观点 / 评论员观察 / 现场评论
#       详情页正文容器同人民锐评: <div id="rm_txt_zw">
import urllib.request, re, ssl, sys, html as ihtml, time

ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
BASE = "http://opinion.people.com.cn"
ICON = "https://www.people.com.cn/favicon.ico"
A_RE = re.compile(r'<a[^>]+href=([\"\'])([^\"\']+)\1[^>]*>(.*?)</a>', re.S)
ART_RE = re.compile(r'/n1/(\d{4})/(\d{2})(\d{2})/c\d+-\d+\.html')
# 子栏目（人民日报评论各板块）；不含 436867 人民锐评
# 注意：49160 主栏目落地页会列出最新的「今日谈」「社论」等（常含当日文章），
#      必须扫描，否则像 2026-10-01 那篇「弘扬英烈精神…（今日谈）」会被漏掉。
SUBCATS = {
    "人民日报评论首页": "http://opinion.people.com.cn/GB/8213/49160/index.html",
    "人民时评":   "http://opinion.people.com.cn/GB/8213/49160/49219/index.html",
    "人民论坛":   "http://opinion.people.com.cn/GB/8213/49160/49220/index.html",
    "本报评论员": "http://opinion.people.com.cn/GB/8213/49160/49217/index.html",
    "人民观点":   "http://opinion.people.com.cn/GB/8213/49160/385787/index.html",
    "评论员观察": "http://opinion.people.com.cn/GB/8213/49160/457597/index.html",
    "现场评论":   "http://opinion.people.com.cn/GB/8213/49160/457598/index.html",
}


def get(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Referer": "http://opinion.people.com.cn/"})
        with urllib.request.urlopen(req, timeout=30, context=ctx) as r:
            return r.read().decode("utf-8", "ignore")
    except Exception as e:
        print("  [warn] 抓取失败 %s -> %s" % (url, e))
        return None


def parse_subcat(url, seen, cat, pages=6):
    """扫一个栏目页及其分页（index.html / index2.html ...），抓全部文章链接。"""
    items = []
    base = url.rsplit("index.html", 1)[0]
    for p in range(pages):
        u = url if p == 0 else base + "index%d.html" % (p + 1)
        d = get(u)
        if not d:
            break
        got = 0
        for m in A_RE.finditer(d):
            href = m.group(2).strip()
            am = ART_RE.search(href)
            if not am:
                continue
            if href.startswith("/"):
                href = BASE + href
            if href in seen:
                continue
            text = re.sub(r"<[^>]+>", "", m.group(3)).strip()
            if not text or len(text) < 4:
                continue
            seen.add(href)
            date = "%s-%s-%s" % (am.group(1), am.group(2), am.group(3))
            items.append((text, href, date, cat))
            got += 1
        time.sleep(0.3)
        if got == 0:
            break
    return items


def parse_list(limit=30):
    items, seen = [], set()
    for cat, url in SUBCATS.items():
        batch = parse_subcat(url, seen, cat)
        items.extend(batch)
        time.sleep(0.3)
    return items


def parse_detail(link, date_hint=""):
    d = get(link)
    if not d:
        return "", [], date_hint
    mt = re.search(r"<title>(.*?)</title>", d, re.S)
    title = mt.group(1).split("--")[0].strip() if mt else ""
    zw = re.search(r'<div id="rm_txt_zw">(.*?)</div>\s*</div>', d, re.S)
    paras = []
    if zw:
        for p in re.findall(r"<p[^>]*>(.*?)</p>", zw.group(1), re.S):
            t = re.sub(r"<[^>]+>", "", p).strip()
            if len(t) > 5:
                paras.append(t)
    date = date_hint
    if not date:
        dm = re.search(r"20\d\d[-/]\d\d[-/]\d\d", d)
        if dm:
            date = dm.group(0).replace("/", "-")
    return title, paras, date


def esc(s):
    return ihtml.escape(s, quote=True)


def build_rss(limit=30):
    items = parse_list()
    # 全局按发布时间倒序（最新在前）。date 为 "YYYY-MM-DD" 字符串，字典序即日期序
    items.sort(key=lambda x: x[2], reverse=True)
    items = items[:limit]
    out = ['<?xml version="1.0" encoding="utf-8"?>',
           '<rss version="2.0"><channel>',
           '<title>人民日报评论</title>', '<link>%s/GB/8213/49160/</link>' % BASE,
           '<description>人民网观点频道 · 人民日报评论（人民时评/人民论坛/本报评论员/人民观点/评论员观察/现场评论，含全文）</description>',
           '<image><url>%s</url></image>' % ICON]
    for title, link, date, cat in items:
        t, paras, _ = parse_detail(link, date_hint=date)
        desc = "".join("<p>%s</p>" % p for p in paras)
        out.append('<item>')
        out.append('<title>%s</title>' % esc(t or title))
        out.append('<link>%s</link>' % esc(link))
        if date:
            out.append('<pubDate>%s</pubDate>' % date)
        out.append('<description><![CDATA[%s]]></description>' % desc)
        out.append('</item>')
    out.append('</channel></rss>')
    return "\n".join(out)


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "-o":
        xml = build_rss()
        with open(sys.argv[2], "w", encoding="utf-8") as f:
            f.write(xml)
        print("written %s (%d articles, %d bytes)" % (sys.argv[2], xml.count("<item>"), len(xml)))
    else:
        print("usage: python rmrb_comment_rss.py -o rmrb_comment.xml")


if __name__ == "__main__":
    main()
