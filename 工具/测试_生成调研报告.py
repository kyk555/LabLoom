# -*- coding: utf-8 -*-
"""生成调研报告.py 的回归测试（纯标准库，python -B 直接跑）。

守住四类不变量：
1. 数据自检：证据字段完整、引用编号存在、权重和为 1、评分不越界。
2. 计算正确：加权分、单实验成本、回本份数可手算复核。
3. 产物自检：无外网 CDN、无占位符残留、表格/div 标签闭合、图表数量与 id 一致。
4. 幂等：同样的数据生成两次，字节完全一致；内容未变时不重写文件。
"""

import io
import json
import os
import re
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import 生成调研报告 as R  # noqa: E402


class TestData(unittest.TestCase):
    def test_verify_data_clean(self):
        self.assertEqual(R.verify_data(), [])

    def test_evidence_ids_unique_and_complete(self):
        ids = [e["id"] for e in R.EVIDENCE]
        self.assertEqual(len(ids), len(set(ids)))
        for e in R.EVIDENCE:
            self.assertTrue(e["url"].startswith("http"))
            self.assertIn(e["level"], ("E1", "E2", "E3", "E4"))
        # 一手来源至少 5 条，否则报告的证据强度不足
        self.assertGreaterEqual(sum(1 for e in R.EVIDENCE if e["level"] == "E1"), 5)

    def test_weights_sum_to_one(self):
        self.assertAlmostEqual(sum(w["w"] for w in R.DATA["weights"]), 1.0, places=9)

    def test_break_verify_on_bad_weight(self):
        saved = R.DATA["weights"][0]["w"]
        try:
            R.DATA["weights"][0]["w"] = saved + 0.1
            self.assertTrue(any("权重和不为 1" in e for e in R.verify_data()))
        finally:
            R.DATA["weights"][0]["w"] = saved

    def test_break_verify_on_bad_score(self):
        saved = R.DATA["positioning"][0]["scores"]["demand"]
        try:
            R.DATA["positioning"][0]["scores"]["demand"] = 9
            self.assertTrue(R.verify_data())
        finally:
            R.DATA["positioning"][0]["scores"]["demand"] = saved


class TestCalc(unittest.TestCase):
    def test_weighted_scores_sorted_and_ranked(self):
        rows = R.weighted_scores()
        self.assertEqual(len(rows), 4)
        totals = [r["total"] for r in rows]
        self.assertEqual(totals, sorted(totals))
        by_id = {r["id"]: r["total"] for r in rows}
        # 原设想 A 必须排在推荐项 B、C 之后
        self.assertLess(by_id["A"], by_id["B"])
        self.assertLess(by_id["A"], by_id["C"])

    def test_weighted_score_hand_calc(self):
        # A: 2*.30 + 1*.25 + 2*.20 + 4*.15 + 3*.10 = 0.6+0.25+0.4+0.6+0.3 = 2.15
        by_id = {r["id"]: r["total"] for r in R.weighted_scores()}
        self.assertAlmostEqual(by_id["A"], 2.15, places=2)

    def test_unit_hours_and_cost(self):
        # 0.5 + 4.0 + 1.0 + 1.5 = 7.0 h；7.0 * 30 = 210 元
        self.assertAlmostEqual(R.unit_hours(1.5), 7.0, places=6)
        self.assertAlmostEqual(R.unit_cost(1.5), 210.0, places=6)

    def test_breakeven_units_ceiling(self):
        # 210 / 9.9 = 21.21 -> 22
        self.assertEqual(R.breakeven_units(1.5, 9.9), 22)
        self.assertEqual(R.breakeven_units(1.5, 49), 5)

    def test_breakeven_monotonic(self):
        rows = R.breakeven_table()
        self.assertEqual(len(rows), len(R.DATA["unit_econ"]["review_hs"]))
        for r in rows:
            # 售价越高，回本所需份数越少（按 prices 升序 => units 降序）
            self.assertEqual(r["units"], sorted(r["units"], reverse=True))
        costs = [r["cost"] for r in rows]
        self.assertEqual(costs, sorted(costs))               # 复核越久，成本越高


class TestHtml(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = R.build_html()

    def test_no_cdn(self):
        # 只允许本地相对路径的 script/link；不允许任何 http(s) 资源引用
        for tag in re.findall(r'<(?:script|link|img)[^>]*>', self.html):
            self.assertNotRegex(tag, r'(?:src|href)\s*=\s*["\']https?://', tag)
        self.assertIn(R.ECHARTS_REL, self.html)

    def test_no_placeholder_left(self):
        for bad in ("%s", "%%", "{trs}", "{be_rows}", "{rows}", "{gap_rows}", "{prices}"):
            self.assertNotIn(bad, self.html)

    def test_key_figures_present(self):
        # 关键结论必须落在页面上，防止模板改动后数字悄悄丢失
        for s in ("1.2 亿", "340%", "30.9%", "1434.4", "各 10 分", "2025-09-01"):
            self.assertIn(s, self.html)

    def test_charts_registered(self):
        self.assertEqual(len(R.CHARTS), 4)
        ids = [c["id"] for c in R.CHARTS]
        self.assertEqual(len(ids), len(set(ids)))
        for cid in ids:
            self.assertIn('id="%s"' % cid, self.html)
            self.assertIn('"%s"' % cid, self.html)  # 已写进初始化脚本

    def test_tables_and_divs_balanced(self):
        for tag in ("table", "tbody", "thead", "div", "tr", "td"):
            opens = len(re.findall(r"<%s[\s>]" % tag, self.html))
            closes = len(re.findall(r"</%s>" % tag, self.html))
            self.assertEqual(opens, closes, "%s 标签未闭合：%d open / %d close" % (tag, opens, closes))

    def test_every_evidence_anchored(self):
        for e in R.EVIDENCE:
            self.assertIn('id="ev-%s"' % e["id"], self.html)

    def test_chart_payload_is_valid_json(self):
        m = re.search(r"var charts = (\[.*?\]);\n", self.html, re.S)
        self.assertIsNotNone(m, "找不到 charts 数据块")
        data = json.loads(m.group(1))
        self.assertEqual(len(data), 4)
        for item in data:
            self.assertIn("id", item)
            self.assertIn("option", item)
            self.assertIn("series", item["option"])

    def test_js_braces_balanced(self):
        script = self.html.split("<script>", 1)[1]
        self.assertEqual(script.count("{"), script.count("}"))
        self.assertEqual(script.count("("), script.count(")"))

    def test_deterministic(self):
        self.assertEqual(self.html.encode("utf-8"), R.build_html().encode("utf-8"))


class TestWrite(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_write_then_skip(self):
        path = os.path.join(self.dir, "sub", "a.html")  # 目录不存在也要能建
        self.assertTrue(R.write_if_changed(path, "中文内容\n"))
        mtime1 = os.path.getmtime(path)
        self.assertFalse(R.write_if_changed(path, "中文内容\n"))
        self.assertEqual(mtime1, os.path.getmtime(path))
        self.assertTrue(R.write_if_changed(path, "改了\n"))
        with io.open(path, encoding="utf-8") as f:
            self.assertEqual(f.read(), "改了\n")


if __name__ == "__main__":
    unittest.main(verbosity=2)
