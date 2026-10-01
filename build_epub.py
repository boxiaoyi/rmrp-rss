# -*- coding: utf-8 -*-
"""通用 RSS(含全文) -> 多章节 ePub 生成器。
用法:
  python build_epub.py -i rmrp.xml -o 人民锐评.epub --title "人民锐评（2026合集）"
  python build_epub.py -i qs_raw.xml -o 求是网.epub --days 30 --title "求是网头条（近30天）"
"""
import sys, os, re, html, zipfile, datetime, argparse
import xml.dom.minidom as M
from email.utils import parsedate_to_datetime

UTC = datetime.timezone.utc

def strip_tags(s):
    return re.sub(r"<[^>]+>", "", s or "")

def parse_items(path):
    d = M.parse(path)
    out = []
    for it in d.getElementsByTagName("item"):
        def first(tag):
            n = it.getElementsByTagName(tag)
            return n[0].firstChild.data if (n and n[0].firstChild) else ""
        title = strip_tags(first("title")).strip()
        pub = strip_tags(first("pubDate")).strip()
        desc = first("description")          # 已是 unescape 后的 HTML 片段
        link = strip_tags(first("link")).strip()
        if title and desc:
            out.append({"title": title, "pub": pub, "desc": desc, "link": link})
    return out

def parse_date(s):
    s = (s or "").strip()
    if not s:
        return None
    try:
        dt = parsedate_to_datetime(s)
        if dt is not None:
            return dt if dt.tzinfo else dt.replace(tzinfo=UTC)
    except Exception:
        pass
    for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%Y/%m/%d", "%Y年%m月%d日"):
        try:
            return datetime.datetime.strptime(s, fmt).replace(tzinfo=UTC)
        except Exception:
            pass
    return None

def filter_items(items, days=None, limit=None):
    if days:
        cutoff = datetime.datetime.now(UTC) - datetime.timedelta(days=days)
        kept = []
        for a in items:
            dt = parse_date(a["pub"])
            if dt is None or dt >= cutoff:
                kept.append(a)
        items = kept
    if limit:
        items = items[:limit]
    return items

def clean_html(s):
    """剥掉原网页的 div 容器、所有标签属性（class/style/id），只留纯 <p>/<br> 等标签，
    避免原网页自带 text-indent 与后续排版叠加导致两本缩进不一致。"""
    s = s or ""
    s = re.sub(r'</?div\b[^>]*>', '', s, flags=re.I)               # 去 div 容器
    s = re.sub(r'</?span\b[^>]*>', '', s, flags=re.I)              # 去 span 包裹
    s = re.sub(r'<img\b[^>]*>', '', s, flags=re.I)                 # 去图片（避免 ePub 破图）
    s = re.sub(r'<([a-zA-Z][a-zA-Z0-9]*)\b[^>]*>', r'<\1>', s)    # 剥其余标签属性
    s = re.sub(r'<p>\s*</p>', '', s)                              # 去空段落
    # 去掉 <p> 段首的全角/半角空白（含 emsp&nbsp;全角空格等），避免与 CSS text-indent 叠加
    # 例：求是网源正文自带「  」全角空格缩进，会导致 Calibre 转换后变成 4 字
    s = re.sub(r'(<p>)([\s\u3000\u2000-\u200b\u00a0\u2028\u2029]+)', r'\1', s)
    return s.strip()

def chapter_xhtml(a, idx):
    body = clean_html(a["desc"])
    if not body.startswith("<"):
        body = "<p>%s</p>" % html.escape(body)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<html xmlns="http://www.w3.org/1999/xhtml" '
        'xmlns:epub="http://www.idpf.org/2007/ops"><head>\n'
        '<meta charset="UTF-8"/>\n'
        f'<title>{html.escape(a["title"])}</title>\n'
        '<style>body{font-family:"Noto Serif CJK SC",serif;line-height:1.9;'
        'padding:0 1.1em;}.article p{text-indent:2em;margin:0 0 .6em;line-height:1.9;}'
        '.meta{color:#888;font-size:.82em;margin:.2em 0 1em;}'
        'hr{border:none;border-top:1px solid #ddd;margin:1.4em 0;}</style>\n'
        '</head>\n<body>\n'
        f'<section epub:type="chapter">\n'
        f'<h2>{html.escape(a["title"])}</h2>\n'
        f'<p class="meta">发布：{html.escape(a["pub"])}　'
        f'<a href="{html.escape(a["link"])}">原文</a></p>\n'
        f'<div class="article">{body}</div>\n'
        f'<hr/></section>\n</body>\n</html>'
    )

def build_epub(items, out_path, book_title):
    n = len(items)
    chap_names = []
    chap_docs = []
    for i, a in enumerate(items, 1):
        name = "chap-%03d.xhtml" % i
        chap_names.append(name)
        chap_docs.append((name, chapter_xhtml(a, i)))

    # nav 目录
    toc_items = "\n".join(
        f'<li><a href="{nm}">{html.escape(it["title"])}</a></li>'
        for nm, it in zip(chap_names, items)
    )
    nav = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<html xmlns="http://www.w3.org/1999/xhtml" '
        'xmlns:epub="http://www.idpf.org/2007/ops"><head><meta charset="UTF-8"/>'
        f'<title>目录</title></head><body><nav epub:type="toc" id="toc">\n'
        f'<h1>{html.escape(book_title)} · 目录</h1>\n<ol>\n{toc_items}\n</ol>\n'
        '</nav></body></html>'
    )
    # 内容起始页（标题 + 简介）
    start = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<html xmlns="http://www.w3.org/1999/xhtml" '
        'xmlns:epub="http://www.idpf.org/2007/ops"><head><meta charset="UTF-8"/>'
        f'<title>{html.escape(book_title)}</title></head><body>\n'
        f'<h1>{html.escape(book_title)}</h1>\n'
        f'<p class="meta">共 {n} 篇</p>\n'
        f'<p><a href="nav.xhtml">查看目录</a></p>\n'
        '</body></html>'
    )
    # opf
    manifest = ['<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>',
                '<item id="start" href="start.xhtml" media-type="application/xhtml+xml"/>']
    spine = ['<itemref idref="start"/>']
    for i, nm in enumerate(chap_names, 1):
        mid = "chap%03d" % i
        manifest.append(f'<item id="{mid}" href="{nm}" media-type="application/xhtml+xml"/>')
        spine.append(f'<itemref idref="{mid}"/>')
    opf = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<package xmlns="http://www.idpf.org/2007/opf" version="3.0" '
        'unique-identifier="bookid" xml:lang="zh-CN">\n<metadata '
        'xmlns:dc="http://purl.org/dc/elements/1.1/">\n'
        '<dc:identifier id="bookid">urn:uuid:%s</dc:identifier>\n'
        f'<dc:title>{html.escape(book_title)}</dc:title>\n'
        '<dc:language>zh-CN</dc:language>\n'
        '<dc:creator>公考评论订阅</dc:creator>\n'
        f'<meta property="dcterms:modified">{datetime.datetime.now(UTC):%Y-%m-%dT%H:%M:%SZ}</meta>\n'
        '</metadata>\n<manifest>\n' + "\n".join(manifest) + '\n</manifest>\n'
        '<spine>\n' + "\n".join(spine) + '\n</spine>\n</package>'
    )
    container = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">\n'
        '<rootfiles><rootfile full-path="OEBPS/content.opf" '
        'media-type="application/oebps-package+xml"/></rootfiles></container>'
    )
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        z.writestr("META-INF/container.xml", container)
        z.writestr("OEBPS/content.opf", opf)
        z.writestr("OEBPS/nav.xhtml", nav)
        z.writestr("OEBPS/start.xhtml", start)
        for nm, doc in chap_docs:
            z.writestr("OEBPS/" + nm, doc)
    return out_path, n

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-i", "--in", required=True)
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("-t", "--title", default="RSS合集")
    ap.add_argument("-d", "--days", type=int, default=None)
    ap.add_argument("-n", "--limit", type=int, default=None)
    args = ap.parse_args()
    items = parse_items(args.__dict__["in"])
    items = filter_items(items, days=args.days, limit=args.limit)
    if not items:
        print("无可用条目"); sys.exit(1)
    out, n = build_epub(items, args.out, args.title)
    # 统计日期范围
    ds = [parse_date(a["pub"]) for a in items]
    ds = [d for d in ds if d]
    rng = "%s ~ %s" % (min(ds).strftime("%Y-%m-%d"), max(ds).strftime("%Y-%m-%d")) if ds else "未知"
    sz = os.path.getsize(out)//1024
    msg = f"已生成 {args.out} | 篇数={n} | 日期范围={rng} | 大小={sz} KB"
    print(msg)
    open(os.path.join(os.path.dirname(os.path.abspath(args.out)) or ".", "build_log.txt"),
         "a", encoding="utf-8").write(msg + "\n")

if __name__ == "__main__":
    main()
