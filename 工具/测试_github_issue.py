# -*- coding: utf-8 -*-
"""工具/github_issue.py 的离线单测（unittest，中文测试名）。

覆盖：请求方法 / URL / 载荷 / 请求头 / 令牌不泄露 / 错误分支 / 本地参数校验。
**完全离线**：patch 掉 urllib.request.urlopen，不读真实数据、不发网络请求、不写文件。
怎么跑（仓库根目录）：
    python -B -m unittest 工具/测试_github_issue.py
    & $py -B -m unittest 工具/测试_github_issue.py
"""
from __future__ import annotations

import io
import json
import os
import sys
import unittest
import urllib.error
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import github_issue  # noqa: E402

仓库 = 'test/repo'
令牌 = 'ghp_测试令牌'


class 假响应:
    """够 urlopen 的 with 与 read 用。"""

    def __init__(self, 载荷):
        self.原始 = json.dumps(载荷, ensure_ascii=False).encode('utf-8')

    def read(self):
        return self.原始

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def 造参数(片段):
    return github_issue.建解析器().parse_args(['--仓库', 仓库] + 片段)


def 跑(片段, 返回=(), 有令牌=True):
    """执行一个命令，返回 (stdout 文本, 捕获到的 Request 列表)。

    返回 里按顺序取假响应；给整数表示该次调用抛 HTTPError(该状态码)。
    """
    捕获 = []
    队列 = list(返回)

    def 假urlopen(请求对象, timeout=None):
        捕获.append(请求对象)
        项 = 队列.pop(0) if 队列 else {'number': 1, 'title': 't', 'html_url': 'https://x/1'}
        if isinstance(项, int):
            raise urllib.error.HTTPError(
                url=请求对象.full_url, code=项, msg='err', hdrs=None,
                fp=io.BytesIO(json.dumps({'message': 'boom'}).encode('utf-8')))
        return 假响应(项)

    环境 = {'GITHUB_TOKEN': 令牌} if 有令牌 else {}
    缓冲 = io.StringIO()
    with mock.patch.dict(os.environ, 环境, clear=True), \
            mock.patch.object(github_issue.urllib.request, 'urlopen', 假urlopen), \
            redirect_stdout(缓冲):
        参数 = 造参数(片段)
        参数.函数(参数)
    return 缓冲.getvalue(), 捕获


class 写操作测试(unittest.TestCase):

    def test_登记发出POST并带上标题正文标签(self):
        输出, 捕获 = 跑(['登记', '--类型', '需求', '--标题', '加滚动IC', '--正文', '目标：x'],
                        [{'number': 7, 'title': '[需求] 加滚动IC', 'html_url': 'https://x/7'}])
        self.assertEqual(len(捕获), 1)
        请求 = 捕获[0]
        self.assertEqual(请求.get_method(), 'POST')
        self.assertEqual(请求.full_url, 'https://api.github.com/repos/test/repo/issues')
        体 = json.loads(请求.data.decode('utf-8'))
        self.assertEqual(体['title'], '[需求] 加滚动IC')
        self.assertEqual(体['body'], '目标：x')
        self.assertEqual(体['labels'], ['enhancement'])
        self.assertIn('【已登记】#7', 输出)

    def test_标题已带前缀时不重复加(self):
        _, 捕获 = 跑(['登记', '--类型', 'bug', '--标题', '[Bug] 已有前缀', '--正文', 'b'])
        self.assertEqual(json.loads(捕获[0].data.decode('utf-8'))['title'], '[Bug] 已有前缀')

    def test_需求与bug的默认标签不同(self):
        _, 捕获 = 跑(['登记', '--类型', 'bug', '--标题', 'x', '--正文', 'y'])
        self.assertEqual(json.loads(捕获[0].data.decode('utf-8'))['labels'], ['bug'])

    def test_回复走评论端点(self):
        输出, 捕获 = 跑(['回复', '3', '--正文', '根因是版本'], [{'html_url': 'https://x/3#c1'}])
        self.assertEqual(捕获[0].get_method(), 'POST')
        self.assertEqual(捕获[0].full_url,
                         'https://api.github.com/repos/test/repo/issues/3/comments')
        self.assertEqual(json.loads(捕获[0].data.decode('utf-8'))['body'], '根因是版本')
        self.assertIn('【已回复】#3', 输出)

    def test_关闭先评论再改状态(self):
        _, 捕获 = 跑(['关闭', '3', '--原因', 'completed', '--评论', '已按验收验证', '--确认'],
                    [{'html_url': 'https://x/c'}, {'number': 3, 'title': 't'}])
        self.assertEqual(len(捕获), 2)
        self.assertEqual(捕获[0].get_method(), 'POST')
        self.assertTrue(捕获[0].full_url.endswith('/issues/3/comments'))
        self.assertEqual(捕获[1].get_method(), 'PATCH')
        self.assertTrue(捕获[1].full_url.endswith('/issues/3'))
        体 = json.loads(捕获[1].data.decode('utf-8'))
        self.assertEqual(体['state'], 'closed')
        self.assertEqual(体['state_reason'], 'completed')

    def test_关闭不带确认直接拒绝且不发请求(self):
        with self.assertRaises(SystemExit) as 上下文:
            跑(['关闭', '3'])
        self.assertEqual(上下文.exception.code, 2)

    def test_重开只发一条PATCH(self):
        _, 捕获 = 跑(['重开', '9'], [{'number': 9, 'title': 't'}])
        self.assertEqual(len(捕获), 1)
        self.assertEqual(捕获[0].get_method(), 'PATCH')
        self.assertEqual(json.loads(捕获[0].data.decode('utf-8'))['state'], 'open')


class 请求头与令牌测试(unittest.TestCase):

    def test_请求头符合GitHubApi规范(self):
        _, 捕获 = 跑(['列表'], [[]])
        请求 = 捕获[0]
        self.assertEqual(请求.get_header('User-agent'), github_issue.UA)
        self.assertEqual(请求.get_header('Accept'), 'application/vnd.github+json')
        self.assertEqual(请求.get_header('X-github-api-version'), '2022-11-28')

    def test_令牌只进Authorization不进URL(self):
        _, 捕获 = 跑(['列表'], [[]])
        请求 = 捕获[0]
        self.assertEqual(请求.get_header('Authorization'), f'Bearer {令牌}')
        self.assertNotIn(令牌, 请求.full_url)

    def test_令牌不出现在任何输出里(self):
        完整条 = {'number': 1, 'title': 't', 'state': 'open', 'labels': [],
                  'created_at': '2026-10-19T00:00:00Z',
                  'updated_at': '2026-10-19T00:00:00Z', 'body': 'b'}
        for 片段, 返回 in (
            (['列表'], [[]]),
            (['查看', '1'], [完整条, []]),
            (['登记', '--类型', '需求', '--标题', 'x', '--正文', 'y'], ()),
        ):
            输出, _ = 跑(片段, 返回)
            self.assertNotIn(令牌, 输出, msg=f'{片段} 的输出里出现了令牌')


class 查询与过滤测试(unittest.TestCase):

    def test_列表参数与排除PR(self):
        输出, 捕获 = 跑(['列表', '--状态', 'all', '--条数', '5', '--标签', 'bug'], [[
            {'number': 1, 'title': '真问题', 'state': 'open',
             'updated_at': '2026-10-19T00:00:00Z', 'labels': [{'name': 'bug'}]},
            {'number': 2, 'title': '这是PR', 'state': 'open',
             'updated_at': '2026-10-19T00:00:00Z', 'labels': [],
             'pull_request': {'url': 'x'}},
        ]])
        网址 = 捕获[0].full_url
        self.assertIn('state=all', 网址)
        self.assertIn('per_page=5', 网址)
        self.assertIn('labels=bug', 网址)
        self.assertIn('真问题', 输出)
        self.assertNotIn('这是PR', 输出)
        self.assertIn('共 1 条', 输出)

    def test_查看会读正文和评论(self):
        输出, 捕获 = 跑(['查看', '3'], [
            {'number': 3, 'title': '标题', 'state': 'open', 'labels': [],
             'created_at': '2026-10-19T00:00:00Z', 'updated_at': '2026-10-19T00:00:00Z',
             'body': '正文内容'},
            [{'user': {'login': 'someone'}, 'created_at': '2026-10-19T01:00:00Z',
              'body': '一条评论'}],
        ])
        self.assertEqual(len(捕获), 2)
        self.assertTrue(捕获[1].full_url.endswith('/issues/3/comments?per_page=100'))
        self.assertIn('正文内容', 输出)
        self.assertIn('一条评论', 输出)


class 错误分支测试(unittest.TestCase):

    def test_401提示令牌无效(self):
        with self.assertRaises(SystemExit) as 上下文:
            跑(['列表'], [401])
        self.assertEqual(上下文.exception.code, 1)

    def test_403提示权限不足(self):
        with self.assertRaises(SystemExit) as 上下文:
            跑(['列表'], [403])
        self.assertEqual(上下文.exception.code, 1)

    def test_404提示仓库不可见(self):
        with self.assertRaises(SystemExit) as 上下文:
            跑(['查看', '1'], [404])
        self.assertEqual(上下文.exception.code, 1)

    def test_无令牌报错退出2且不发请求(self):
        with mock.patch.dict(os.environ, {}, clear=True), \
                mock.patch.object(github_issue.urllib.request, 'urlopen',
                                  side_effect=AssertionError('不该发请求')), \
                redirect_stdout(io.StringIO()):
            with self.assertRaises(SystemExit) as 上下文:
                参数 = 造参数(['列表'])
                参数.函数(参数)
        self.assertEqual(上下文.exception.code, 2)

    def test_空正文登记被拒绝(self):
        with self.assertRaises(SystemExit) as 上下文:
            跑(['登记', '--类型', '需求', '--标题', '空'])
        self.assertEqual(上下文.exception.code, 2)

    def test_空回复被拒绝(self):
        with self.assertRaises(SystemExit) as 上下文:
            跑(['回复', '3'])
        self.assertEqual(上下文.exception.code, 2)

    def test_非法仓库格式被拒绝(self):
        with mock.patch.dict(os.environ, {'GITHUB_TOKEN': 令牌}, clear=True), \
                redirect_stdout(io.StringIO()):
            with self.assertRaises(SystemExit) as 上下文:
                参数 = github_issue.建解析器().parse_args(['--仓库', 'nope', '列表'])
                参数.函数(参数)
        self.assertEqual(上下文.exception.code, 2)


class 预演测试(unittest.TestCase):

    def test_预演登记不发请求且打印载荷(self):
        with mock.patch.dict(os.environ, {}, clear=True), \
                mock.patch.object(github_issue.urllib.request, 'urlopen',
                                  side_effect=AssertionError('预演不该发请求')), \
                redirect_stdout(io.StringIO()) as 缓冲:
            参数 = 造参数(['登记', '--类型', '需求', '--标题', 't', '--正文', 'b', '--预演'])
            参数.函数(参数)
        输出 = 缓冲.getvalue()
        self.assertIn('【预演】', 输出)
        self.assertIn('"title": "[需求] t"', 输出)

    def test_预演关闭会打印两步(self):
        with mock.patch.dict(os.environ, {}, clear=True), \
                mock.patch.object(github_issue.urllib.request, 'urlopen',
                                  side_effect=AssertionError('预演不该发请求')), \
                redirect_stdout(io.StringIO()) as 缓冲:
            参数 = 造参数(['关闭', '3', '--评论', 'c', '--确认', '--预演'])
            参数.函数(参数)
        输出 = 缓冲.getvalue()
        self.assertIn('/issues/3/comments', 输出)
        self.assertIn('"state": "closed"', 输出)


if __name__ == '__main__':
    unittest.main(verbosity=2)
