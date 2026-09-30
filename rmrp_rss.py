#!/usr/bin/env python3
# 人民锐评 RSS 生成器（含全文正文）
# 用法:
#   python rmrp_rss.py -o rmrp.xml            # 生成静态 RSS 文件
#   python rmrp_rss.py --serve 8000           # 起本地服务，阅读填 http://电脑局域网IP:8000/ 订阅
# 说明: 列表来自 opinion.people.com.cn/GB/436867 (人民锐评栏目, 静态分页)
#       正文来自每篇详情页 #rm_txt_zw 容器。生成的 RSS item 含完整正文，
#       阅读 App 会用内置阅读器渲染 -> 字号/边距可调 + 划词笔记可用。
import urllib.request, re, ssl, sys, html as ihtml, time
from http.server import HTTPServer, BaseHTTPRequestHandler

ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
UA = "Mozilla/5.0"
LIST_BASE = "http://opinion.people.com.cn/GB/436867/"   # 人民锐评栏目（静态分页）
LIST = LIST_BASE + "index.html"
ICON = "https://www.people.com.cn/favicon.ico"

# 文章 href 可能用单引号或双引号
A_RE = re.compile(r"<a[^>]+href=([\"'])([^\"']+)\1[^>]*>(.*?)</a>", re.S)


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    return urllib.request.urlopen(req, timeout=30, context=ctx).read().decode("utf-8", "ignore")


def parse_list_page(url, seen):
    """解析单个人民锐评列表页，返回 [(title, link, date), ...]"""
    try:
        d = get(url)
    except Exception:
        return []
    items = []
    for li in re.findall(r'<li class="clearfix">(.*?)</li>', d, re.S):
        a = A_RE.search(li)
        if not a:
            continue
        href = a.group(2).strip()
        title = re.sub(r"<[^>]+>", "", a.group(3)).strip()
        if href.startswith('/'):
            href = 'http://opinion.people.com.cn' + href
        # 主栏目 c436867，评论员署名短评栏目 c461529，都是我们要的人民锐评
        if not re.search(r'/c(436867|461529)-\d+\.html', href):
            continue
        if title and href not in seen:
            seen.add(href)
            dm = re.search(r'(20\d\d-\d\d-\d\d)', li)
            items.append((title, href, dm.group(1) if dm else ""))
    return items


def parse_list(limit=200):
    """翻全部分页（index.html, index2.html, index3.html, ...）抓历史文章。"""
    items, seen = [], set()
    # 第 1 页：index.html
    batch = parse_list_page(LIST, seen)
    if batch:
        items.extend(batch)
    # 第 2 页起：index2.html, index3.html, ...
    for page_no in range(2, 100):
        if len(items) >= limit:
            break
        url = LIST_BASE + f"index{page_no}.html"
        batch = parse_list_page(url, seen)
        if not batch:
            break
        items.extend(batch)
        time.sleep(0.3)
    return items[:limit]


def parse_detail(link, date_hint=""):
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
    # 优先用列表页已拿到的日期；没有再用详情页里出现的第一个日期
    date = date_hint
    if not date:
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
