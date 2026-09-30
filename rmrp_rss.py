#!/usr/bin/env python3
# 人民锐评 RSS 生成器（含全文正文）
# 用法:
#   python rmrp_rss.py -o rmrp.xml            # 生成静态 RSS 文件
#   python rmrp_rss.py --serve 8000           # 起本地服务，阅读填 http://电脑局域网IP:8000/ 订阅
# 说明: 列表来自 opinion.people.com.cn/GB/436867 (人民锐评栏目, 静态HTML)
#       正文来自每篇详情页 #rm_txt_zw 容器。生成的 RSS item 含完整正文，
#       阅读 App 会用内置阅读器渲染 -> 字号/边距可调 + 划词笔记可用。
import urllib.request, re, ssl, sys, html as ihtml, time
from http.server import HTTPServer, BaseHTTPRequestHandler

ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
UA = "Mozilla/5.0"
LIST = "http://opinion.people.com.cn/GB/436867/index.html"
ICON = "https://www.people.com.cn/favicon.ico"

def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    return urllib.request.urlopen(req, timeout=30, context=ctx).read().decode("utf-8", "ignore")

def parse_list(limit=20):
    d = get(LIST)
    seen, items = set(), []
    # 列表页文章链接形如 <a href="http://opinion.people.com.cn/n1/.../c223228-xxx.html" title="完整标题">
    for m in re.finditer(r'<a[^>]+href="(https?://opinion\.people\.com\.cn/n1/[^\"]+)"[^>]*title="([^"]*)"', d):
        link, title = m.group(1), m.group(2).strip()
        if title and link not in seen:
            seen.add(link); items.append((title, link))
        if len(items) >= limit:
            break
    return items

def parse_detail(link):
    d = get(link)
    mt = re.search(r"<title>(.*?)</title>", d, re.S)
    title = mt.group(1).split("--")[0].strip() if mt else ""
    zw = re.search(r'<div id="rm_txt_zw">(.*?)</div>\s*</div>', d, re.S)
    paras = []
    if zw:
        for p in re.findall(r"<p[^>]*>(.*?)</p>", zw.group(1), re.S):
            t = re.sub(r"<[^>]+>", "", p).strip()
            if len(t) > 5:
                paras.append(t)
    dm = re.search(r"20\d\d[-/]\d\d[-/]\d\d", d)
    date = dm.group(0).replace("/", "-") if dm else ""
    return title, paras, date

def esc(s):
    return ihtml.escape(s, quote=True)

def build_rss():
    items = parse_list()
    out = ['<?xml version="1.0" encoding="utf-8"?>',
           '<rss version="2.0"><channel>',
           '<title>人民锐评</title>', '<link>%s</link>' % LIST,
           '<description>人民网观点频道 · 人民锐评专栏（含全文正文）</description>',
           '<image><url>%s</url></image>' % ICON]
    for title, link in items:
        t, paras, date = parse_detail(link)
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
        print("written %s (%d bytes)" % (sys.argv[2], len(xml)))
    elif len(sys.argv) > 1 and sys.argv[1] == "--serve":
        port = int(sys.argv[2]) if len(sys.argv) > 2 else 8000
        cache = {"xml": None, "ts": 0}
        class H(BaseHTTPRequestHandler):
            def do_GET(self):
                now = time.time()
                if not cache["xml"] or now - cache["ts"] > 1800:
                    cache["xml"] = build_rss(); cache["ts"] = now
                self.send_response(200)
                self.send_header("Content-Type", "application/rss+xml; charset=utf-8")
                self.end_headers()
                self.wfile.write(cache["xml"].encode("utf-8"))
            def log_message(self, *a):
                pass
        print("serving RSS on port %d  (Ctrl+C to stop)" % port)
        HTTPServer(("0.0.0.0", port), H).serve_forever()
    else:
        print("usage:\n  python rmrp_rss.py -o rmrp.xml\n  python rmrp_rss.py --serve [port]")

if __name__ == "__main__":
    main()
