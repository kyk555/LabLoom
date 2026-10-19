# -*- coding: utf-8 -*-
"""GitHub issue 命令行工具：自检 / 列表 / 查看 / 登记 / 回复 / 关闭 / 重开。

输入：命令行参数 + 环境变量 GITHUB_TOKEN（找不到时退到 GH_TOKEN）
输出：终端中文文本；退出码 0 成功、1 请求失败、2 配置缺失
边界：
  - 只调用 GitHub REST API 的 issues 相关端点（不碰 commit / PR / 设置）
  - 不读 Windows 凭据管理器，不打印令牌，不把令牌写进任何文件
  - 无令牌时直接报错退出，不静默降级
怎么跑（PowerShell，仓库根目录；纯标准库，3.8+ 即可）：
  python -B 工具/github_issue.py 自检
  python -B 工具/github_issue.py 列表
  python -B 工具/github_issue.py 列表 --状态 closed --条数 10
  python -B 工具/github_issue.py 查看 3
  python -B 工具/github_issue.py 登记 --类型 需求 --标题 "初中化学·误差分析样本" --正文文件 C:\\tmp\\需求.md
  python -B 工具/github_issue.py 回复 3 --正文文件 C:\\tmp\\回复.md
  python -B 工具/github_issue.py 关闭 3 --原因 completed --评论 "已按验收标准验证" --确认
令牌怎么来：见同目录 README.md（fine-grained PAT，只授 Issues: Read and write）
出处：移植自 allweather 项目同名工具（V1.0），改动仅 UA 与示例路径。

关于请求头：本项目规则要求抓网页伪装浏览器，但这里是**带令牌的官方 API 调用**，
伪装浏览器反而异常且 GitHub 明确要求标识调用方，故只用 UA + API 版本头，不用爬虫头。
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

API = 'https://api.github.com'
超时秒 = 25
UA = 'labloom-issue-cli/1.0'

类型到标签 = {'需求': 'enhancement', 'bug': 'bug'}
类型到前缀 = {'需求': '[需求] ', 'bug': '[Bug] '}


# ────────────────────────── 环境与认证 ──────────────────────────

def 取令牌(必须=True):
    """返回 (令牌, 来源变量名)；找不到就报错退出，不返回空串。

    必须=False 用于 --预演：此时不发送任何请求，令牌可以为空。
    """
    for 名 in ('GITHUB_TOKEN', 'GH_TOKEN'):
        值 = os.environ.get(名, '').strip()
        if 值:
            return 值, 名
    if not 必须:
        return None, '预演模式（无令牌，不发送请求）'
    print('【错误】没有找到 GitHub 令牌。')
    print('  需要先设置环境变量 GITHUB_TOKEN（或 GH_TOKEN），只授 Issues 读写权限。')
    print('  创建与设置步骤见 工具/README.md；设好后重开一个终端再试。')
    sys.exit(2)


def 找仓库(覆盖=None):
    """从 git remote origin 解析 owner/repo；换仓库时用 --仓库 覆盖。"""
    if 覆盖:
        if not re.fullmatch(r'[^/\s]+/[^/\s]+', 覆盖):
            print(f'【错误】--仓库 需要写成 owner/repo，收到：{覆盖}')
            sys.exit(2)
        return 覆盖
    try:
        出 = subprocess.run(['git', 'remote', 'get-url', 'origin'],
                            capture_output=True, text=True, timeout=10)
    except Exception as e:  # git 不存在 / 超时
        print(f'【错误】调 git 失败：{e}')
        sys.exit(2)
    if 出.returncode != 0:
        print('【错误】当前目录不是 git 仓库，或者没有 origin 远程。')
        print(f'  git 说：{出.stderr.strip()}')
        sys.exit(2)
    地址 = 出.stdout.strip()
    命 = re.search(r'github\.com[:/]+([^/]+)/(.+?)(?:\.git)?$', 地址)
    if not 命:
        print(f'【错误】origin 不是 GitHub 地址：{地址}')
        sys.exit(2)
    return f'{命.group(1)}/{命.group(2)}'


def 请求(方法, 路径, 载荷=None, 令牌=None, 预演=False):
    """发一次请求并返回解析后的 JSON；失败时打印中文诊断并退出（不吞异常）。"""
    全网址 = API + 路径
    头 = {
        'User-Agent': UA,
        'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28',
    }
    if 令牌:
        头['Authorization'] = f'Bearer {令牌}'
    数据 = None
    if 载荷 is not None:
        数据 = json.dumps(载荷, ensure_ascii=False).encode('utf-8')
        头['Content-Type'] = 'application/json; charset=utf-8'

    if 预演:
        print('【预演】不发送请求，只打印将要提交的内容：')
        print(f'  {方法} {全网址}')
        if 载荷 is not None:
            print('  ' + json.dumps(载荷, ensure_ascii=False, indent=2).replace('\n', '\n  '))
        return None

    请求对象 = urllib.request.Request(全网址, data=数据, headers=头, method=方法)
    try:
        with urllib.request.urlopen(请求对象, timeout=超时秒) as 响应:
            原文 = 响应.read().decode('utf-8')
        return json.loads(原文) if 原文.strip() else {}
    except urllib.error.HTTPError as 错:
        原文 = 错.read().decode('utf-8', 'replace')
        try:
            体 = json.loads(原文)
        except Exception:
            体 = {'message': 原文[:500]}
        print(f'【失败】{方法} {路径} → HTTP {错.code}')
        print(f'  GitHub 说：{体.get("message", "")}')
        for 条 in (体.get('errors') or []):
            print(f'  · {条}')
        if 错.code == 401:
            print('  → 令牌无效或已过期：重新生成 PAT，再设 GITHUB_TOKEN，然后重开终端')
        elif 错.code == 403:
            print('  → 权限不足（PAT 需要 Issues: Read and write）或触发了限流')
        elif 错.code == 404:
            print('  → 仓库不可见：确认令牌所属账号能访问该仓库，且 owner/repo 拼写正确')
        elif 错.code == 422:
            print('  → 参数被拒：常见原因是标题为空、标签不存在、正文过长')
        sys.exit(1)
    except urllib.error.URLError as 错:
        print(f'【失败】连不上 GitHub：{错.reason}')
        print('  → 检查网络；要走代理就先设 $env:HTTPS_PROXY 再重试')
        sys.exit(1)


def 读正文(参数):
    """--正文文件 优先，其次 --正文；两者都没有返回空串（由调用方决定是否报错）。"""
    if getattr(参数, '正文文件', None):
        路 = Path(参数.正文文件)
        if not 路.is_file():
            print(f'【错误】正文文件不存在：{路}')
            sys.exit(2)
        return 路.read_text(encoding='utf-8').strip()
    return (getattr(参数, '正文', None) or '').strip()


# ────────────────────────── 子命令 ──────────────────────────

def 命令_自检(参数):
    """确认令牌、仓库、Issues 开关、写入权限四件事都就绪。"""
    令牌, 来源 = 取令牌()
    仓库 = 找仓库(参数.仓库)
    print(f'令牌来源：{来源}（{len(令牌)} 字符，内容不打印）')
    print(f'仓库    ：{仓库}')
    信息 = 请求('GET', f'/repos/{仓库}', 令牌=令牌)
    权限 = 信息.get('permissions') or {}
    print(f'可见性  ：{"私有" if 信息.get("private") else "公开"}')
    print(f'Issues  ：{"已开启" if 信息.get("has_issues") else "未开启 ← 去 Settings → Features 勾上"}')
    print(f'写入权限：{权限.get("push")}（True 才能建 / 关 issue）')
    print(f'默认分支：{信息.get("default_branch")}')
    print('-' * 56)
    if not 信息.get('has_issues'):
        print('【未就绪】Issues 功能没开，开了再来。')
        sys.exit(1)
    if not 权限.get('push'):
        print('【未就绪】令牌有读权限但写不了 issue（PAT 需 Issues: Read and write）。')
        sys.exit(1)
    print('【就绪】可以登记 / 回复 / 关闭 issue。')


def 命令_列表(参数):
    令牌, _ = 取令牌()
    仓库 = 找仓库(参数.仓库)
    查询 = [('state', 参数.状态), ('per_page', str(参数.条数))]
    if 参数.标签:
        查询.append(('labels', 参数.标签))
    路径 = f'/repos/{仓库}/issues?' + urllib.parse.urlencode(查询)
    数据 = 请求('GET', 路径, 令牌=令牌)
    真问题 = [x for x in 数据 if 'pull_request' not in x]
    if not 真问题:
        print('（没有匹配的 issue）')
        return
    print(f'{"编号":<6}{"状态":<8}{"更新日":<12}标题')
    print('-' * 72)
    for 条 in 真问题:
        标 = ','.join(x['name'] for x in 条.get('labels', []))
        尾 = f'  [{标}]' if 标 else ''
        print(f'#{条["number"]:<5}{条["state"]:<8}{条["updated_at"][:10]:<12}{条["title"]}{尾}')
    print('-' * 72)
    print(f'共 {len(真问题)} 条（已排除 PR）')


def 命令_查看(参数):
    令牌, _ = 取令牌()
    仓库 = 找仓库(参数.仓库)
    条 = 请求('GET', f'/repos/{仓库}/issues/{参数.编号}', 令牌=令牌)
    print(f'#{条["number"]}  {条["title"]}')
    print(f'状态：{条["state"]}　标签：{",".join(x["name"] for x in 条.get("labels", [])) or "无"}')
    print(f'创建：{条["created_at"][:19]}　更新：{条["updated_at"][:19]}')
    print('=' * 72)
    print(条.get('body') or '（正文为空）')
    评论 = 请求('GET', f'/repos/{仓库}/issues/{参数.编号}/comments?per_page=100', 令牌=令牌)
    if 评论:
        print('=' * 72)
        print(f'评论 {len(评论)} 条：')
        for i, 评 in enumerate(评论, 1):
            print(f'\n── [{i}] {评["user"]["login"]}  {评["created_at"][:19]} ──')
            print(评.get('body') or '（空）')


def 命令_登记(参数):
    正文 = 读正文(参数)
    if not 正文:
        print('【错误】正文是空的。')
        print('  需求至少写清「目标 + 验收标准」，bug 至少写清「复现步骤 + 实际输出」。')
        print('  用 --正文文件 <路径> 或 --正文 "..." 传入。')
        sys.exit(2)

    标题 = (参数.标题 or '').strip()
    if not 标题:
        print('【错误】标题不能为空。')
        sys.exit(2)
    前缀 = '' if 参数.不加上缀 else 类型到前缀[参数.类型]
    if 前缀 and not 标题.startswith(前缀.strip()):
        标题 = 前缀 + 标题

    标签 = [类型到标签[参数.类型]]
    for 项 in (参数.标签 or []):
        项 = 项.strip()
        if 项 and 项 not in 标签:
            标签.append(项)

    仓库 = 找仓库(参数.仓库)
    令牌, _ = 取令牌(必须=not 参数.预演)
    载荷 = {'title': 标题, 'body': 正文, 'labels': 标签}
    结果 = 请求('POST', f'/repos/{仓库}/issues', 载荷, 令牌=令牌, 预演=参数.预演)
    if 参数.预演:
        return
    print(f'【已登记】#{结果["number"]}  {结果["title"]}')
    print(f'  {结果["html_url"]}')


def 命令_回复(参数):
    正文 = 读正文(参数)
    if not 正文:
        print('【错误】回复内容为空，什么都没发。')
        sys.exit(2)
    仓库 = 找仓库(参数.仓库)
    令牌, _ = 取令牌(必须=not 参数.预演)
    结果 = 请求('POST', f'/repos/{仓库}/issues/{参数.编号}/comments',
                {'body': 正文}, 令牌=令牌, 预演=参数.预演)
    if 参数.预演:
        return
    print(f'【已回复】#{参数.编号}  {结果["html_url"]}')


def 命令_关闭(参数):
    if not 参数.确认:
        print('【拒绝】关闭 issue 需要显式加 --确认（避免误关）。')
        print('  例：... 关闭 3 --原因 completed --评论 "已修复" --确认')
        sys.exit(2)
    令牌, _ = 取令牌(必须=not 参数.预演)
    仓库 = 找仓库(参数.仓库)

    评论 = (参数.评论 or '').strip()
    if 参数.评论文件:
        路 = Path(参数.评论文件)
        if not 路.is_file():
            print(f'【错误】评论文件不存在：{路}')
            sys.exit(2)
        评论 = 路.read_text(encoding='utf-8').strip()
    if 评论:
        评论结果 = 请求('POST', f'/repos/{仓库}/issues/{参数.编号}/comments',
                        {'body': 评论}, 令牌=令牌, 预演=参数.预演)
        if not 参数.预演:
            print(f'【已评论】{评论结果["html_url"]}')

    结果 = 请求('PATCH', f'/repos/{仓库}/issues/{参数.编号}',
                {'state': 'closed', 'state_reason': 参数.原因},
                令牌=令牌, 预演=参数.预演)
    if 参数.预演:
        return
    print(f'【已关闭】#{结果["number"]}  {结果["title"]}（原因：{参数.原因}）')


def 命令_重开(参数):
    仓库 = 找仓库(参数.仓库)
    令牌, _ = 取令牌(必须=not 参数.预演)
    结果 = 请求('PATCH', f'/repos/{仓库}/issues/{参数.编号}',
                {'state': 'open'}, 令牌=令牌, 预演=参数.预演)
    if 参数.预演:
        return
    print(f'【已重开】#{结果["number"]}  {结果["title"]}')


# ────────────────────────── 命令行 ──────────────────────────

def 建解析器():
    解析器 = argparse.ArgumentParser(
        prog='github_issue.py',
        description='GitHub issue 命令行工具（登记 / 回复 / 关闭 / 查看）',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='令牌：设 $env:GITHUB_TOKEN（fine-grained PAT，Issues: Read and write）。见 工具/README.md',
    )
    解析器.add_argument('--仓库', default='', help='owner/repo，默认从 git remote origin 解析')
    子 = 解析器.add_subparsers(dest='命令', required=True)

    分 = 子.add_parser('自检', help='检查令牌 / 仓库 / Issues 开关 / 写入权限')
    分.set_defaults(函数=命令_自检)

    分 = 子.add_parser('列表', help='列出 issue（自动排除 PR）')
    分.add_argument('--状态', default='open', choices=['open', 'closed', 'all'])
    分.add_argument('--标签', default='')
    分.add_argument('--条数', type=int, default=20)
    分.set_defaults(函数=命令_列表)

    分 = 子.add_parser('查看', help='看某条 issue 的正文与全部评论')
    分.add_argument('编号', type=int)
    分.set_defaults(函数=命令_查看)

    分 = 子.add_parser('登记', help='新建 issue')
    分.add_argument('--类型', required=True, choices=['需求', 'bug'])
    分.add_argument('--标题', required=True)
    分.add_argument('--正文', default='')
    分.add_argument('--正文文件', default='')
    分.add_argument('--标签', action='append', default=[])
    分.add_argument('--不加上缀', action='store_true', help='不自动加 [需求] / [Bug] 前缀')
    分.add_argument('--预演', action='store_true', help='只打印将要提交的内容，不发送')
    分.set_defaults(函数=命令_登记)

    分 = 子.add_parser('回复', help='给 issue 加一条评论')
    分.add_argument('编号', type=int)
    分.add_argument('--正文', default='')
    分.add_argument('--正文文件', default='')
    分.add_argument('--预演', action='store_true')
    分.set_defaults(函数=命令_回复)

    分 = 子.add_parser('关闭', help='评论（可选）后关闭 issue')
    分.add_argument('编号', type=int)
    分.add_argument('--原因', default='completed', choices=['completed', 'not_planned'])
    分.add_argument('--评论', default='')
    分.add_argument('--评论文件', default='')
    分.add_argument('--确认', action='store_true', help='必填，防误关')
    分.add_argument('--预演', action='store_true')
    分.set_defaults(函数=命令_关闭)

    分 = 子.add_parser('重开', help='把已关闭的 issue 重新打开')
    分.add_argument('编号', type=int)
    分.add_argument('--预演', action='store_true')
    分.set_defaults(函数=命令_重开)

    return 解析器


def main(argv=None):
    try:
        sys.stdout.reconfigure(encoding='utf-8')  # Python 3.7+
    except Exception:
        pass
    参数 = 建解析器().parse_args(argv)
    参数.函数(参数)
    return 0


if __name__ == '__main__':
    sys.exit(main())
