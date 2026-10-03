# -*- coding: utf-8 -*-
"""抓取「求是网评」栏目 (http://www.qstheory.cn/qswp.htm) 近期评论文章，
输出 RSS 2.0 全文 xml，供 build_epub.py 生成 ePub。
用法:
  python qs_comment_rss.py -o qs_comment.xml
  python qs_comment_rss.py -o qs_comment.xml -n 6   # 只前6篇(调试)
"""
import sys, os, re, time, argparse
import urllib.request as ureq
import xml.sax.saxutils as su

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
COL = "http://www.qstheory.cn/qswp.htm"


def get(url, enc="utf-8", retry=2):
    url = url.replace("https://", "http://")
    for _ in range(retry):
        try:
            req = ureq.Request(url, headers={"User-Agent": UA})
            with ureq.urlopen(req, timeout=25) as r:
                return r.read().decode(enc, errors="ignore")
        except Exception as e:
            print("  ERR", url, repr(e)[:80])
            time.sleep(0.5)
    return None


def parse_list():
    h = get(COL)
    if not h:
        return []
    rels = re.findall(r'href="(20\d{6}/[0-9a-f]{32}/c\.html)"', h)
    seen, urls = set(), []
    for rel in rels:
        if rel in seen:
            continue
        seen.add(rel)
        urls.append("http://www.qstheory.cn/" + rel)
    return urls


def fetch(url):
    h = get(url)
    if not h:
        return None
    m = re.search(r"<h1[^>]*>(.*?)</h1>", h, re.S)
    title = re.sub(r"<[^>]+>", "", m.group(1)).strip() if m else ""
    if len(title) < 4:
        return None
    md = re.search(r"(\d{4})[-/年](\d{1,2})[-/月](\d{1,2})", h)
    date = "%s-%02d-%02d" % (md.group(1), int(md.group(2)), int(md.group(3))) if md else ""
    # 正文：优先 <div class="text"> 容器；退而求其次整页 <p>
    block = h
    mt = re.search(r'class="text"[^>]*>(.*?)</div>\s*</div>', h, re.S)
    if mt:
        block = mt.group(1)
    ps = re.findall(r"<p[^>]*>(.*?)</p>", block, re.S)
    paras = [re.sub(r"<[^>]+>", "", p).strip() for p in ps]
    paras = [p for p in paras if len(p) > 5]
    text = "".join(paras)
    if len(text) < 200:   # 太短(列表页/空页)跳过
        return None
    desc = "".join("<p>%s</p>" % su.escape(p) for p in paras)
    return (title, url, date, desc)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-o", "--out", default="qs_comment.xml")
    ap.add_argument("-n", "--limit", type=int, default=0)
    args = ap.parse_args()

    urls = parse_list()
    print("栏目链接数=%d" % len(urls))
    if args.limit:
        urls = urls[: args.limit]
    items = []
    for u in urls:
        a = fetch(u)
        if a:
            items.append(a)
            print("  + %s | %s" % (a[2], a[0][:30]))
        else:
            print("  - 跳过 %s" % u)
        time.sleep(0.3)

    lines = [
        '<?xml version="1.0" encoding="utf-8"?>',
        '<rss version="2.0"><channel>',
        "<title>求是网评</title>",
        "<link>%s</link>" % COL,
        "<description>求是网评栏目近期评论文章</description>",
    ]
    for title, url, date, desc in items:
        lines += [
            "<item>",
            "<title>%s</title>" % su.escape(title),
            "<link>%s</link>" % su.escape(url),
            "<pubDate>%s</pubDate>" % su.escape(date),
            "<description><![CDATA[%s]]></description>" % desc.replace("]]>", "]]]]><![CDATA[>"),
            "</item>",
        ]
    lines.append("</channel></rss>")
    with open(args.out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("抓取 %d 篇 -> %s" % (len(items), args.out))


if __name__ == "__main__":
    main()
