# -*- coding: utf-8 -*-
"""把含全文正文的 RSS(人民锐评)转成 ePub，方便导入微信读书等阅读器。
用法: python rss2epub.py -i rmrp.xml -o 人民锐评.epub -n 30
"""
import sys, os, re, html, zipfile, datetime
import xml.dom.minidom as M

try:
    import defusedxml  # noqa  # 若环境有则更安全；没有也不影响
except Exception:
    pass

def strip_tags(s):
    return re.sub(r"<[^>]+>", "", s or "")

def parse_items(path):
    d = M.parse(path)
    out = []
    for it in d.getElementsByTagName("item"):
        def first(tag):
            n = it.getElementsByTagName(tag)
            return n[0].firstChild.data if n and n[0].firstChild else ""
        title = first("title")
        pub = first("pubDate")
        desc = first("description")
        link = first("link")
        if title and desc:
            out.append({"title": strip_tags(title).strip(),
                        "pub": strip_tags(pub).strip(),
                        "desc": desc, "link": strip_tags(link).strip()})
    return out

def build_epub(items, out_path):
    opf_id = "book"
    # 单篇 xhtml 合并，便于微信读书/阅读器连续翻页
    parts = []
    for idx, a in enumerate(items, 1):
        body = a["desc"] if a["desc"].strip().startswith("<") else "<p>%s</p>" % html.escape(a["desc"])
        parts.append(
            f'<section epub:type="chapter">\n'
            f'<h2>{html.escape(a["title"])}</h2>\n'
            f'<p class="meta">发布：{html.escape(a["pub"])}</p>\n'
            f'{body}\n'
            f'<hr/>\n</section>'
        )
    content = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<html xmlns="http://www.w3.org/1999/xhtml" '
        'xmlns:epub="http://www.idpf.org/2007/ops">\n<head>\n'
        '<meta charset="UTF-8"/>\n'
        f'<title>人民锐评（最新{len(items)}篇）</title>\n'
        '<style>body{font-family:"Noto Serif CJK SC",serif;line-height:1.9;'
        'padding:0 1.2em;}.meta{color:#888;font-size:.85em;}</style>\n'
        '</head>\n<body>\n'
        f'<h1>人民锐评（最新{len(items)}篇）</h1>\n'
        "\n".join(parts) +
        "\n</body>\n</html>"
    )
    opf = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid">\n'
        '<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">\n'
        '<dc:identifier id="bookid">urn:uuid:rmrp-2026</dc:identifier>\n'
        '<dc:title>人民锐评（最新合集）</dc:title>\n'
        '<dc:language>zh-CN</dc:language>\n'
        '<dc:creator>rmrp-rss</dc:creator>\n'
        f'<meta property="dcterms:modified">{datetime.datetime.now(datetime.timezone.utc):%Y-%m-%dT%H:%M:%SZ}</meta>\n'
        '</metadata>\n<manifest>\n'
        '<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>\n'
        f'<item id="{opf_id}" href="content.xhtml" media-type="application/xhtml+xml"/>\n'
        '</manifest>\n<spine>\n'
        f'<itemref idref="{opf_id}"/>\n</spine>\n</package>'
    )
    nav = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<html xmlns="http://www.w3.org/1999/xhtml" '
        'xmlns:epub="http://www.idpf.org/2007/ops"><head><meta charset="UTF-8"/></head>\n'
        '<body><nav epub:type="toc"><ol>\n'
        f'<li><a href="content.xhtml">人民锐评（最新{len(items)}篇）</a></li>\n'
        '</ol></nav></body></html>'
    )
    container = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">\n'
        '<rootfiles><rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>'
        '</rootfiles></container>'
    )
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        z.writestr("META-INF/container.xml", container)
        z.writestr("OEBPS/content.opf", opf)
        z.writestr("OEBPS/nav.xhtml", nav)
        z.writestr("OEBPS/content.xhtml", content)
    return out_path

def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("-i", "--in", default="rmrp.xml")
    ap.add_argument("-o", "--out", default="人民锐评.epub")
    ap.add_argument("-n", "--num", type=int, default=30)
    args = ap.parse_args()
    items = parse_items(args.__dict__["in"])[:args.num]
    if not items:
        print("没有可用条目"); sys.exit(1)
    build_epub(items, args.out)
    print(f"已生成 {args.out}（{len(items)} 篇，{os.path.getsize(args.out)//1024} KB）")

if __name__ == "__main__":
    main()
