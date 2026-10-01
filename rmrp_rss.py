#!/usr/bin/env python3
# 人民锐评 RSS 生成器（含全文正文）
# 用法:
#   python rmrp_rss.py -o rmrp.xml            # 生成静态 RSS 文件
#   python rmrp_rss.py --serve 8000           # 起本地服务，阅读填 http://电脑局域网IP:8000/ 订阅
#
# 数据源（两路合并、按标题去重）:
#   1) 主源 = 人民网+ App「人民锐评」话题官方接口 3414（api-app.people.cn/api/v2/subjects/3414）
#      —— 永远和你在 App 里看到的同步更新，正文由 articles/detail 接口直接给，最稳。
#   2) 归档 = 人民网观点频道「人民锐评」栏目静态页 436867 的历史文章（翻分页爬）
#      —— 补足 App 话题只保留最近 ~20 篇的不足，做成 ePub 合集时有深度。
import urllib.request, re, ssl, sys, html as ihtml, time, json
from http.server import HTTPServer, BaseHTTPRequestHandler

ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) Mobile/15E148"
ICON = "https://www.people.com.cn/favicon.ico"

# ---- 主源：App 话题接口 ----
API_TOPIC = 3414
API_SUBJECT = f"https://api-app.people.cn/api/v2/subjects/{API_TOPIC}"
API_DETAIL = "https://api-app.people.cn/api/v2/articles/detail/%s"

# ---- 归档：观点频道栏目静态页 ----
COL_BASE = "http://opinion.people.com.cn/GB/436867/"
COL_FIRST = COL_BASE + "index.html"
A_RE = re.compile(r"<a[^>]+href=([\"'])([^\"']+)\1[^>]*>(.*?)</a>", re.S)


def get(url, binary=False, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
        data = r.read()
    return data if binary else data.decode("utf-8", "ignore")


def get_json(url):
    return json.loads(get(url))


def norm_key(title):
    """去重用的归一化：去品牌前缀、标点、空白。"""
    t = title or ""
    t = re.sub(r'^(人民锐评|人民网评|人民时评|人民论坛|人民日报评论|锐评|评论)[：:丨|]?\s*', '', t)
    t = re.sub(r'[^\w一-鿿]', '', t)
    return t.lower()


# ============ 主源：App 话题接口 ============
def fetch_api_items(limit=60):
    """抓 App「人民锐评」话题，返回 [{title, link, date, desc}, ...]（已含全文）"""
    items = []
    try:
        data = get_json(API_SUBJECT)
    except Exception as e:
        print("  [warn] 话题接口失败 %s -> %s" % (API_SUBJECT, e))
        return items
    blocks = data.get("item", {}).get("blocks", [])
    arts = []
    for b in blocks:
        arts.extend(b.get("articles", []))
    print("  [api] 话题返回 %d 篇 (最新: %s)" % (
        len(arts), arts[0].get("date", "?") if arts else "-"))
    for a in arts:
        if len(items) >= limit:
            break
        aid = a.get("articleId")
        title = a.get("title") or a.get("listTitle") or ""
        if not title or not aid:
            continue
        # 日期 2026-10-01T07:02:41+0800 -> 2026-10-01
        date = ""
        dm = re.search(r'(20\d\d-\d\d-\d\d)', a.get("date", "") or "")
        if dm:
            date = dm.group(1)
        # 正文
        desc = ""
        try:
            det = get_json(API_DETAIL % aid)
            item = det.get("item", {})
            content = item.get("content", "") or ""
            if content:
                desc = content
            time.sleep(0.15)
        except Exception as e:
            print("  [warn] 详情失败 %s -> %s" % (aid, e))
        if not desc:
            desc = a.get("summary") or ""
        link = a.get("shareUrl") or a.get("externalUrl") or "http://app.people.cn/h5/topic/subject_normal/%s" % API_TOPIC
        items.append({"title": title, "link": link, "date": date, "desc": desc,
                      "source": a.get("source", "")})
    return items


# ============ 归档：观点频道栏目静态页 ============
def parse_column_page(url, seen):
    try:
        d = get(url)
    except Exception:
        return []
    out = []
    for li in re.findall(r'<li class="clearfix">(.*?)</li>', d, re.S):
        a = A_RE.search(li)
        if not a:
            continue
        href = a.group(2).strip()
        title = re.sub(r"<[^>]+>", "", a.group(3)).strip()
        if "/n1/" not in href and "/GB/" not in href:
            continue
        if href.startswith('/'):
            href = 'http://opinion.people.com.cn' + href
        if not re.search(r'/c\d+-\d+\.html', href):
            continue
        if not title or href in seen:
            continue
        seen.add(href)
        dm = re.search(r'(20\d\d-\d\d-\d\d)', li)
        out.append((title, href, dm.group(1) if dm else ""))
    return out


def fetch_column_items(limit=200):
    items, seen = [], set()
    batch = parse_column_page(COL_FIRST, seen)
    items.extend(batch)
    for p in range(2, 100):
        if len(items) >= limit:
            break
        b = parse_column_page(COL_BASE + f"index{p}.html", seen)
        if not b:
            break
        items.extend(b)
        time.sleep(0.3)
    print("  [column] 栏目归档 %d 篇 (最新: %s)" % (len(items), items[0][2] if items else "-"))
    # 取正文
    out = []
    for title, link, date in items[:limit]:
        try:
            d = get(link)
            zw = re.search(r'<div id="rm_txt_zw">(.*?)</div>\s*</div>', d, re.S)
            paras = []
            if zw:
                for p in re.findall(r"<p[^>]*>(.*?)</p>", zw.group(1), re.S):
                    t = re.sub(r"<[^>]+>", "", p).strip()
                    if len(t) > 5:
                        paras.append(t)
            desc = "".join("<p>%s</p>" % p for p in paras)
            time.sleep(0.2)
        except Exception as e:
            desc = ""
            print("  [warn] 栏目详情失败 %s -> %s" % (link, e))
        out.append({"title": title, "link": link, "date": date, "desc": desc, "source": "人民网-观点频道"})
    return out


# ============ 合并 + 构建 RSS ============
def build_rss():
    merged = {}
    for it in fetch_api_items() + fetch_column_items():
        key = norm_key(it["title"])
        if not key:
            continue
        if key in merged:
            # API 源优先（更新鲜/可能含 10-01），但保留有正文的
            old = merged[key]
            if not old["desc"] and it["desc"]:
                merged[key] = it
            continue
        merged[key] = it
    # 按日期倒序；无日期排最后
    items = sorted(merged.values(),
                   key=lambda x: x["date"] or "0000-00-00", reverse=True)
    out = ['<?xml version="1.0" encoding="utf-8"?>',
           '<rss version="2.0"><channel>',
           '<title>人民锐评</title>',
           '<link>https://app.people.cn/h5/topic/subject_normal/%s</link>' % API_TOPIC,
           '<description>人民网+ App「人民锐评」话题 + 观点频道栏目（含全文正文）</description>',
           '<image><url>%s</url></image>' % ICON]
    for it in items:
        out.append('<item>')
        out.append('<title>%s</title>' % esc(it["title"]))
        out.append('<link>%s</link>' % esc(it["link"]))
        if it["date"]:
            out.append('<pubDate>%s</pubDate>' % it["date"])
        out.append('<description><![CDATA[%s]]></description>' % it["desc"])
        out.append('</item>')
    out.append('</channel></rss>')
    return "\n".join(out)


def esc(s):
    return ihtml.escape(s, quote=True)


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "-o":
        xml = build_rss()
        with open(sys.argv[2], "w", encoding="utf-8") as f:
            f.write(xml)
        n = xml.count("<item>")
        print("written %s (%d bytes, %d items)" % (sys.argv[2], len(xml), n))
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
