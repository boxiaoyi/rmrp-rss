#!/usr/bin/env python3
# 浙江宣传 RSS 生成器（浙江在线专栏 zjnews.zjol.com.cn/zjxc/，含全文正文）
# 用法: python zjxc_rss.py -o zjxc.xml
# 列表: https://zjnews.zjol.com.cn/zjxc/ (分页 index.shtml / index_1.shtml ...)
# 正文: 每篇详情页 <div class="content"> 容器内 <p> 段落
import urllib.request, re, ssl, sys, html as ihtml, time
from http.server import HTTPServer, BaseHTTPRequestHandler

ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
LIST_BASE = "https://zjnews.zjol.com.cn/zjxc/"
ICON = "https://zjnews.zjol.com.cn/favicon.ico"
A_RE = re.compile(r'<a[^>]+href=([\"\'])([^\"\']+)\1[^>]*>(.*?)</a>', re.S)
ART_RE = re.compile(r'zjxc/(\d{6})/t(\d{8})_(\d+)\.shtml')


def get(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Referer": "https://zjnews.zjol.com.cn/"})
        with urllib.request.urlopen(req, timeout=30, context=ctx) as r:
            return r.read().decode("utf-8", "ignore")
    except Exception as e:
        print("  [warn] 抓取失败 %s -> %s" % (url, e))
        return None


def parse_list_page(url, seen):
    try:
        d = get(url)
    except Exception:
        return []
    items = []
    for m in A_RE.finditer(d):
        href = m.group(2).strip()
        if not ART_RE.search(href):
            continue
        if href.startswith("//"):
            href = "https:" + href
        if href in seen:
            continue
        text = re.sub(r"<[^>]+>", "", m.group(3)).strip()
        text = re.sub(r"^浙江宣传\s*[|｜]\s*", "", text)
        ymd = ART_RE.search(href).group(2)
        date = "%s-%s-%s" % (ymd[:4], ymd[4:6], ymd[6:8])
        if text:
            seen.add(href)
            items.append((text, href, date))
    return items


def parse_list(limit=200):
    items, seen = [], set()
    pages = [LIST_BASE + "index.shtml"] + [LIST_BASE + "index_%d.shtml" % i for i in range(1, 12)]
    for url in pages:
        if len(items) >= limit:
            break
        batch = parse_list_page(url, seen)
        if not batch and "index_1" in url:
            break
        items.extend(batch)
        time.sleep(0.3)
    return items[:limit]


def parse_detail(link, date_hint=""):
    d = get(link)
    if not d:
        return "", [], date_hint
    mt = re.search(r"<title>(.*?)</title>", d, re.S)
    title = (mt.group(1).split("_")[0].split("-")[0].strip() if mt else "")
    title = re.sub(r"^浙江宣传\s*[|｜]\s*", "", title)
    paras = []
    c = re.search(r'<div class="content">(.*?)</div>', d, re.S)
    scope = c.group(1) if c else d
    for p in re.findall(r"<p[^>]*>(.*?)</p>", scope, re.S):
        t = re.sub(r"<[^>]+>", "", p).strip()
        if len(t) > 3:
            paras.append(t)
    if not paras:  # 兜底：抓全页较长 <p>
        for p in re.findall(r"<p[^>]*>(.*?)</p>", d, re.S):
            t = re.sub(r"<[^>]+>", "", p).strip()
            if len(t) > 15:
                paras.append(t)
    date = date_hint
    if not date:
        dm = re.search(r"20\d\d[-/]\d\d[-/]\d\d", d)
        if dm:
            date = dm.group(0).replace("/", "-")
    return title, paras, date


def esc(s):
    return ihtml.escape(s, quote=True)


def build_rss():
    items = parse_list()
    out = ['<?xml version="1.0" encoding="utf-8"?>',
           '<rss version="2.0"><channel>',
           '<title>浙江宣传</title>', '<link>%s</link>' % LIST_BASE,
           '<description>浙江在线 · 浙江宣传专栏（含全文正文）</description>',
           '<image><url>%s</url></image>' % ICON]
    for title, link, date in items:
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
        print("usage: python zjxc_rss.py -o zjxc.xml")


if __name__ == "__main__":
    main()
