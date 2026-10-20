#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""浏览器抓取（普通人形态）：有界面、用本机 Chrome、配置持久化、遇登录就停下等人。

为什么不用 requests：2026-10-20 本轮实测搜索引擎与静态抓取同时降级（Bing 把长 query 拆成单字、
360 连续空结果页），说明只靠伪造请求头已经拿不到一手页面。规则允许的第二级手段就是真实浏览器：
本机已装 Chrome + 有界面 + 不注入自动化开关 + 持久化配置目录（保留登录态）。

三种用法：

    python -B 工具/浏览器抓取.py --环境
    python -B 工具/浏览器抓取.py --打开 <URL> [--等 120]          # 手动登录用，登录态留在 profile 里
    python -B 工具/浏览器抓取.py --抓取 <URL> --名称 e26-xxx [--等渲染 6] [--截图]

规矩（对齐 .clinerules/01、03）：
  1. 原始返回原样存 `data/raw/<日期>-<名称>/`（.gitignore 已挡，不入库），正文与 HTML 各存一份；
  2. 留痕三件套写进 `meta.json`：来源 URL + 抓取时间（UTC 与北京）+ sha256；
  3. 撞上登录页 / 验证页**不留档、不重试**，提示人手动登完再来（对方明确拒绝就不当天硬打）；
  4. 不猜账号、不绕验证码、不改 UA —— 就是用户自己的浏览器。
"""
import argparse
import hashlib
import json
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote_plus

ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "data" / "浏览器配置"      # 持久化，保留登录态（不入库）
RAW = ROOT / "data" / "raw"                 # 原始留档（不入库）

BJT = timezone(timedelta(hours=8))

# 「拦人」的特征，只在地址 / 标题 / 极短正文里判断，避免误伤正文里的「登录」二字
WALL_IN_URL = ("login", "passport", "signin", "signon", "sso", "captcha", "verify", "auth")
WALL_IN_TITLE = ("登录", "验证", "安全中心", "人机", "Just a moment")

# 普通用户形态：最大化窗口、去掉自动化标记；有界面，绝不无头
LAUNCH_ARGS = ["--start-maximized", "--disable-blink-features=AutomationControlled"]
IGNORE_DEFAULT_ARGS = ["--enable-automation", "--no-sandbox"]


def now_pair():
    """UTC 与北京时间成对返回，避免两处口径漂移。"""
    utc = datetime.now(timezone.utc)
    return utc, utc.astimezone(BJT)


def sha256_hex(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def write_text(path, text):
    """统一 LF 写盘。Python 3.8 的 Path.write_text 没有 newline 参数，故直接 open。"""
    with open(str(path), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def looks_walled(url, title, text):
    """返回命中的原因字符串；空串表示不像登录/验证页。"""
    low = (url or "").lower()
    for key in WALL_IN_URL:
        if key in low:
            return "地址含「%s」" % key
    for key in WALL_IN_TITLE:
        if key in (title or ""):
            return "标题含「%s」" % key
    body = (text or "").strip()
    if len(body) < 200 and "登录" in body:
        return "正文不足 200 字且含「登录」"
    return ""


def open_context():
    """启动有界面的本机 Chrome，配置目录持久化。"""
    from playwright.sync_api import sync_playwright

    PROFILE.mkdir(parents=True, exist_ok=True)
    pw = sync_playwright().start()
    try:
        ctx = pw.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE),
            channel="chrome",              # 用本机已装的 Chrome，不下载 chromium
            headless=False,                # 必须是可见窗口
            ignore_default_args=IGNORE_DEFAULT_ARGS,
            viewport=None,                 # 跟随真实窗口大小，不做固定视口
            args=LAUNCH_ARGS,
            locale="zh-CN",
        )
    except Exception:
        pw.stop()
        raise
    return pw, ctx


def first_page(ctx):
    return ctx.pages[0] if ctx.pages else ctx.new_page()

def cmd_env():
    print("Python      : %s" % sys.version.split()[0])
    try:
        from playwright._repo_version import version as pw_version
        print("Playwright  : %s" % pw_version)
    except Exception as exc:                      # 版本模块改名时不影响其它命令
        print("Playwright  : 已安装（版本未取到：%s）" % exc)
    candidates = [
        Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
        Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
        Path.home() / r"AppData\Local\Google\Chrome\Application\chrome.exe",
    ]
    hit = [p for p in candidates if p.exists()]
    print("本机 Chrome : %s" % (str(hit[0]) if hit else "未找到（channel=chrome 会失败）"))
    print("配置目录    : %s（%s）" % (PROFILE, "已存在" if PROFILE.exists() else "尚未创建"))
    cookies = list(PROFILE.glob("*/Cookies")) + list(PROFILE.glob("*/Network/Cookies"))
    print("登录态      : %s" % ("有 %d 个 Cookies 文件" % len(cookies)
                               if cookies else "无（首次抓需登录的站点要先 --打开 手动登）"))
    print("留档目录    : %s" % RAW)
    return 0 if hit else 2


def cmd_open(url, wait_seconds):
    pw, ctx = open_context()
    try:
        page = first_page(ctx)
        page.goto(url, wait_until="domcontentloaded", timeout=90000)
        print("已打开：%s" % url)
        print("窗口就是普通 Chrome：要登录 / 过验证请自己手动操作，我不碰账号也不绕验证。")
        print("最多等 %d 秒；登录态留在 %s，之后 --抓取 直接复用。" % (wait_seconds, PROFILE))
        deadline = time.time() + wait_seconds
        while time.time() < deadline:
            time.sleep(5)
            try:
                title = page.title()
            except Exception:
                print("窗口已关闭，结束。")
                return 0
            left = int(deadline - time.time())
            print("  还剩 %3ds  当前页：%s" % (max(left, 0), title[:60]))
        print("时间到，关闭。没登完就重跑本命令——已写入的 cookie 会保留。")
        return 0
    finally:
        _shutdown(pw, ctx)


def cmd_fetch(url, name, render_wait, want_shot):
    pw, ctx = open_context()
    try:
        page = first_page(ctx)
        resp = page.goto(url, wait_until="domcontentloaded", timeout=90000)
        page.wait_for_timeout(int(render_wait * 1000))   # 给 JS 渲染留时间，不赌「网络空闲」
        final_url = page.url
        title = page.title()
        html = page.content()
        text = page.inner_text("body")
        wall = looks_walled(final_url, title, text)
        if wall:
            print("[停] 这页像登录 / 验证页（%s），本次不留档、不重试。" % wall)
            print("     先跑：python -B 工具/浏览器抓取.py --打开 \"%s\" --等 120" % url)
            print("     手动登完再回来 --抓取。")
            return 3

        status = resp.status if resp is not None else 0
        utc, bj = now_pair()
        out_dir = _raw_dir(bj, name)
        out_dir.mkdir(parents=True, exist_ok=False)
        ua = page.evaluate("navigator.userAgent")

        write_text(out_dir / "page.html", html)
        write_text(out_dir / "page.txt", text)
        try:
            links = page.eval_on_selector_all(
                "a[href]",
                "els => els.map(e => [e.textContent.trim().replace(/\\s+/g, ' ').slice(0, 100), e.href])")
        except Exception:
            links = []
        write_text(out_dir / "links.txt",
                   "\n".join("%s\t%s" % (t, h) for t, h in links))
        if want_shot:
            try:
                page.screenshot(path=str(out_dir / "page.png"), full_page=True)
            except Exception as exc:                   # 超长页截图可能失败，但不该毁掉正文留档
                print("     截图失败（正文已留档）：%s" % exc)

        meta = {
            "url": url,
            "final_url": final_url,
            "http_status": status,
            "title": title,
            "fetched_at_utc": utc.strftime("%Y-%m-%d %H:%M:%S"),
            "fetched_at_bj": bj.strftime("%Y-%m-%d %H:%M:%S"),
            "sha256_html": sha256_hex(html),
            "sha256_text": sha256_hex(text),
            "bytes_html": len(html.encode("utf-8")),
            "chars_text": len(text),
            "links": len(links),
            "user_agent": ua,
            "viewport": "跟随真实窗口（未固定）",
            "browser": "本机 Chrome（channel=chrome，有界面，非无头）",
            "headless": False,
            "automation_args_removed": IGNORE_DEFAULT_ARGS,
            "profile": str(PROFILE),
            "raw_dir": str(out_dir),
            "note": "原始返回原样保存，未清洗；正文由 inner_text(body) 取，仅供检索，引用以 page.html 为准。",
        }
        write_text(out_dir / "meta.json",
                   json.dumps(meta, ensure_ascii=False, indent=2))

        print("[OK] %s  HTTP %s" % (final_url, status))
        print("     标题：%s" % title[:80])
        print("     时间：%s UTC ｜ %s 北京" % (meta["fetched_at_utc"], meta["fetched_at_bj"]))
        print("     正文：%d 字 ｜ HTML %d 字节" % (len(text), meta["bytes_html"]))
        print("     sha256_html %s" % meta["sha256_html"][:16])
        print("     sha256_text %s" % meta["sha256_text"][:16])
        print("     留档：%s" % out_dir)
        return 0
    finally:
        _shutdown(pw, ctx)


def cmd_search(keyword, name, render_wait):
    """用真浏览器跑 Bing，把结果页（含链接清单）留档，再据此挑一手页面。

    搜索引擎接口在 2026-10-20 本轮被降级过，所以搜索也走浏览器，不调任何 API。
    """
    url = "https://www.bing.com/search?q=" + quote_plus(keyword) + "&setlang=zh-CN&cc=CN"
    print("搜索：%s" % keyword)
    return cmd_fetch(url, name or "search", max(render_wait, 3.0), False)


def _raw_dir(bj, name):
    """留档目录只增不覆盖：同名时追加 -2、-3。"""
    safe = "".join(ch for ch in (name or "page") if ch.isalnum() or ch in "-_")
    base = RAW / ("%s-%s" % (bj.strftime("%Y%m%d"), safe or "page"))
    if not base.exists():
        return base
    i = 2
    while True:
        cand = base.parent / ("%s-%d" % (base.name, i))
        if not cand.exists():
            return cand
        i += 1


def _shutdown(pw, ctx):
    """用户手动关窗口时 close 会抛错，这里只收尾，不掩盖已留档的内容。"""
    try:
        ctx.close()
    except Exception:
        pass
    try:
        pw.stop()
    except Exception:
        pass


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")   # Windows 控制台中文不乱码

    ap = argparse.ArgumentParser(
        description="有界面 Chrome 抓取：本机 Chrome + 持久化配置 + 遇登录停下来等人。")
    ap.add_argument("--环境", action="store_true", help="打印 Python / Playwright / Chrome / 登录态位置")
    ap.add_argument("--打开", metavar="URL", help="打开页面并等 N 秒（用于手动登录），不写留档")
    ap.add_argument("--抓取", metavar="URL", help="抓正文并留档；撞登录页则退出码 3、不留档")
    ap.add_argument("--搜索", metavar="关键词", help="用真浏览器跑 Bing，留档结果页与链接清单")
    ap.add_argument("--名称", default="page", help="留档目录后缀，建议 e26-<主题>")
    ap.add_argument("--等", dest="wait_seconds", type=int, default=120, help="--打开 的等待秒数")
    ap.add_argument("--等渲染", dest="render_wait", type=float, default=5.0, help="--抓取 的 JS 渲染等待秒数")
    ap.add_argument("--截图", action="store_true", help="--抓取 时另存整页截图")
    args = ap.parse_args(argv)

    if args.环境:
        return cmd_env()
    if args.打开:
        return cmd_open(args.打开, max(10, args.wait_seconds))
    if args.抓取:
        return cmd_fetch(args.抓取, args.名称, max(0.0, args.render_wait), args.截图)
    if args.搜索:
        return cmd_search(args.搜索, args.名称, max(0.0, args.render_wait))
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())

