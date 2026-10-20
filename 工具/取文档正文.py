# -*- coding: utf-8 -*-
"""把 Word（.docx）正文取成纯文本，供留痕与人工核对用。

为什么要它：政策正文常常只放在页面附件 .docx 里（例如《中小学实验室规程》正文就挂在
教育部通知页的附件上），不解附件就等于「只拿到转发通知、没拿到规程」。只用标准库，
不需要 python-docx。

用法：
    python -B 工具/取文档正文.py <文件.docx>                 # 打印到屏幕
    python -B 工具/取文档正文.py <文件.docx> -o 正文.txt      # 写文件
    python -B 工具/取文档正文.py <文件.docx> --统计           # 只打印字数与 sha256

限制（写在前面，免得以为了解到的东西比实际多）：
- 只处理 .docx（zip + XML）。旧版 .doc 是二进制格式，本脚本不做，需另找工具；
- 表格单元格按段落顺序输出，合并单元格与版式不还原；
- 不做 OCR、不解析 PDF；图片里的文字取不到。
"""

import argparse
import hashlib
import io
import sys
import zipfile
from xml.etree import ElementTree as ET

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def docx_text(blob):
    """docx 字节流 -> 纯文本：按 w:p 分段，w:tab -> \\t，w:br -> \\n。"""
    zf = zipfile.ZipFile(io.BytesIO(blob))
    root = ET.fromstring(zf.read("word/document.xml"))
    lines = []
    for p in root.iter(W + "p"):
        buf = []
        for node in p.iter():
            if node.tag == W + "t":
                buf.append(node.text or "")
            elif node.tag == W + "tab":
                buf.append("\t")
            elif node.tag == W + "br":
                buf.append("\n")
        line = "".join(buf).strip()
        if line:
            lines.append(line)
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description="把 .docx 正文取成纯文本（纯标准库）")
    ap.add_argument("文件", help=".docx 文件路径")
    ap.add_argument("-o", "--输出", help="写到这个文件（UTF-8）；不给则打印到屏幕")
    ap.add_argument("--统计", action="store_true", help="只打印字数、行数与 sha256")
    args = ap.parse_args(argv)

    if not args.文件.lower().endswith(".docx"):
        print("[拒绝] 只处理 .docx；.doc / .pdf 需另找工具", file=sys.stderr)
        return 2

    with open(args.文件, "rb") as f:
        blob = f.read()
    text = docx_text(blob)

    if args.统计:
        print("字节 %d ｜ 字符 %d ｜ 行 %d ｜ docx sha256 %s ｜ 正文 sha256 %s"
              % (len(blob), len(text), text.count("\n") + 1,
                 hashlib.sha256(blob).hexdigest()[:16],
                 hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]))
        return 0

    if args.输出:
        with open(args.输出, "w", encoding="utf-8") as f:
            f.write(text)
        print("[OK] 已写出 %s（%d 字符）" % (args.输出, len(text)))
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
