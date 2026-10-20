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
        # 一手来源至少 14 条（v1.2 再补入 4 条一手公文），否则报告的证据强度不足
        self.assertGreaterEqual(sum(1 for e in R.EVIDENCE if e["level"] == "E1"), 14)

    def test_e5_upgraded_to_full_text_without_overclaim(self):
        """E5 必须是指南全文（E1），且不许把原文「避免」升格成「禁止直接复制」。"""
        e5 = {e["id"]: e for e in R.EVIDENCE}["E5"]
        self.assertEqual(e5["level"], "E1")
        self.assertIn("cse.edu.cn", e5["url"])
        self.assertIn("避免在作业中简单复制", e5["point"])
        self.assertIn("白名单", e5["point"])
        self.assertNotIn("禁止学生直接复制", e5["point"])

    def test_e26_afterclass_gate(self):
        """课后服务通知要进台账，且三条硬门槛写全（刷题禁令 / 遴选招标 / 人员资格）。"""
        e26 = {e["id"]: e for e in R.EVIDENCE}["E26"]
        self.assertEqual(e26["level"], "E1")
        for key in ("刷题备考", "遴选审核", "明显低于", "严禁不符合规定条件的人员"):
            self.assertIn(key, e26["point"])

    def test_beyond_rows_have_primary_source(self):
        """第 12 节的每一条赛道判定都必须有一手依据，不许拿媒体稿定禁区。"""
        lvl = {e["id"]: e["level"] for e in R.EVIDENCE}
        for b in R.DATA["beyond"]:
            refs = [x.strip() for x in b["ev"].split("/") if x.strip()]
            self.assertTrue(refs, b["name"])
            self.assertTrue(any(lvl[r] == "E1" for r in refs), b["name"])

    def test_beyond_verdicts_follow_policy(self):
        by = {b["name"]: b for b in R.DATA["beyond"]}
        self.assertEqual(by["历史"]["pill"], "no")
        self.assertEqual(by["地理"]["pill"], "no")
        self.assertEqual(by["象棋"]["pill"], "mid")
        # 象棋必须写明「不挂钩升学」，否则会被误读成推荐
        self.assertIn("不挂钩升学", by["象棋"]["hard"])
        # 必须保留物化生自己的对照行，否则第 12 节会显得只批评别人
        self.assertIn("物化生实验（本项目对照）", by)

    def test_break_verify_on_beyond_without_e1(self):
        saved = R.DATA["beyond"][2]["ev"]
        try:
            R.DATA["beyond"][2]["ev"] = "E19"  # 只剩媒体转述
            self.assertTrue(any("没有 E1 级依据" in e for e in R.verify_data()))
        finally:
            R.DATA["beyond"][2]["ev"] = saved

    def test_missing_rows_have_primary_source(self):
        """第 13 节每个领域的判定都要有一手依据，且必须写明校内已有什么。"""
        lvl = {e["id"]: e["level"] for e in R.EVIDENCE}
        for m in R.DATA["missing"]:
            refs = [x.strip() for x in m["ev"].split("/") if x.strip()]
            self.assertTrue(refs, m["name"])
            self.assertTrue(any(lvl[r] == "E1" for r in refs), m["name"])
            # 不写「学校已有什么」，结论就会退化成「学校没教」
            self.assertTrue(m["supply"], m["name"])

    def test_missing_verdicts(self):
        by = {m["name"]: m for m in R.DATA["missing"]}
        # 财商是本节核心：只能做工具，且必须承认校内已有
        self.assertEqual(by["财商 / 理财启蒙"]["pill"], "solo")
        self.assertIn("道德与法治", by["财商 / 理财启蒙"]["supply"])
        # 心理与性教育碰专业资质 / 敏感内容，必须判死
        self.assertEqual(by["心理健康 / 情绪管理"]["pill"], "off")
        self.assertEqual(by["青春期 / 性教育"]["pill"], "off")
        # 劳动与职业有课时指标，付费方是学校
        self.assertEqual(by["劳动 / 生活技能"]["pill"], "b2b")
        self.assertEqual(by["职业启蒙 / 生涯规划"]["pill"], "b2b")
        # 六个领域全部没有计分：这是「不能当第二曲线」的根因，不许被改掉
        for m in R.DATA["missing"]:
            self.assertIn("无计分", m["hard"] + m["why"], m["name"])

    def test_break_verify_on_missing_without_e1(self):
        saved = R.DATA["missing"][0]["ev"]
        try:
            R.DATA["missing"][0]["ev"] = "E19"  # 只剩媒体转述
            self.assertTrue(any("没有 E1 级依据" in e for e in R.verify_data()))
        finally:
            R.DATA["missing"][0]["ev"] = saved

    def test_break_verify_on_caishang_without_supply(self):
        """把「学校没教」写回去，自检必须报错。"""
        saved = R.DATA["missing"][0]["supply"]
        try:
            R.DATA["missing"][0]["supply"] = "学校没教，家长只能外面补"
            self.assertTrue(any("道德与法治" in e for e in R.verify_data()))
        finally:
            R.DATA["missing"][0]["supply"] = saved

    def test_toc_rows_have_primary_source(self):
        """第 14 节每个 To C 机会点都要有一手依据，且必须写「什么信号就停」。"""
        lvl = {e["id"]: e["level"] for e in R.EVIDENCE}
        for t in R.DATA["toc"]:
            refs = [x.strip() for x in t["ev"].split("/") if x.strip()]
            self.assertTrue(refs, t["name"])
            self.assertTrue(any(lvl[r] == "E1" for r in refs), t["name"])
            # 没有停手条件的「机会」不叫机会
            self.assertTrue(t["stop"], t["name"])
            self.assertTrue(t["mvp"], t["name"])

    def test_toc_verdicts(self):
        by = {t["name"]: t for t in R.DATA["toc"]}
        # 现在就能试的两个：实验单点卡、场馆任务卡
        self.assertEqual(by["实验操作「单点」考前卡"]["pill"], "go")
        self.assertEqual(by["场馆 / 研学亲子任务卡"]["pill"], "go")
        # 家庭实验包受「小学科学归类不明」限制，只能做亲子活动
        self.assertEqual(by["家庭可做的安全实验包"]["pill"], "mid")
        # 理解型演示：需求侧只有内部讨论、没有用户证据 → 只能「形态受限」
        self.assertEqual(by["抽象概念「理解型」单点演示"]["pill"], "mid")
        # 三个看着像机会的坑必须一直判死
        self.assertEqual(by["拍照搜题 / 答案直出"]["pill"], "no")
        self.assertEqual(by["卖学科课时包 / 押题班"]["pill"], "no")
        self.assertEqual(by["AI 心理测评 / 情绪筛查"]["pill"], "no")
        # 判死的行必须写明理由前缀，避免以后被悄悄改成「可做」
        for t in R.DATA["toc"]:
            if t["pill"] == "no":
                self.assertIn("别碰", t["verdict"], t["name"])

    def test_toc_candidate_count_matches_body(self):
        """候选数由脚本现算：数据里有 8 条，正文就必须写 8，不许手写数字漂移。"""
        self.assertEqual(len(R.DATA["toc"]), 8)
        html = R.render_s14()
        self.assertIn("筛了 8 个候选", html)
        self.assertIn("14.2 8 个候选的筛查结果", html)

    def test_understanding_demo_declares_evidence_gap(self):
        """「理解型演示」的需求证据只有内部讨论：必须标 evidence_gap，且不得判可试。"""
        by = {t["name"]: t for t in R.DATA["toc"]}
        t = by["抽象概念「理解型」单点演示"]
        self.assertTrue(t.get("evidence_gap"), "需求侧无用户证据，必须标 evidence_gap")
        self.assertEqual(t["pill"], "mid")

    def test_break_verify_on_evidence_gap_promoted(self):
        """把标了证据缺口的候选改成「可试」，自检必须报错（防止悄悄升格）。"""
        by = {t["name"]: t for t in R.DATA["toc"]}
        t = by["抽象概念「理解型」单点演示"]
        saved = t["pill"]
        try:
            t["pill"] = "go"
            self.assertTrue(any("证据缺口" in e for e in R.verify_data()))
        finally:
            t["pill"] = saved

    def test_s14_has_ip_copyright_rule(self):
        """§14.1 必须写明 IP 化的著作权边界，否则「用孩子喜欢的 IP」会直接踩侵权。"""
        html = R.render_s14()
        self.assertIn("四条铁律", html)
        self.assertIn("不碰别人的形象", html)
        self.assertIn("著作权", html)

    def test_break_verify_on_toc_without_e1(self):
        saved = R.DATA["toc"][0]["ev"]
        try:
            R.DATA["toc"][0]["ev"] = "E19"  # 只剩媒体转述
            self.assertTrue(any("没有 E1 级依据" in e for e in R.verify_data()))
        finally:
            R.DATA["toc"][0]["ev"] = saved

    def test_break_verify_on_toc_promise_word(self):
        """把「提分」写进最小可交付物，自检必须报错（承诺性表述是红线）。"""
        saved = R.DATA["toc"][0]["mvp"]
        try:
            R.DATA["toc"][0]["mvp"] = "一个实验一张提分清单"
            self.assertTrue(any("承诺性表述" in e for e in R.verify_data()))
        finally:
            R.DATA["toc"][0]["mvp"] = saved

    def test_toc_stop_may_contain_banned_words(self):
        """stop 字段写的就是禁止内容，允许出现禁语；其余字段出现才算违规。"""
        hit = [t["name"] for t in R.DATA["toc"]
               if any(w in t["stop"] for w in ("提分", "包过", "押题"))]
        self.assertTrue(hit, "至少要有一行在 stop 里写清禁止词，否则等于没设边界")
        self.assertEqual([e for e in R.verify_data() if "承诺性表述" in e], [])

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

    def test_铜陵分值必须标届别(self):
        """E6 只代表 2026 届；2027 届起已改。台账里缺届别，等于把旧形态当现状。"""
        ev = {e["id"]: e for e in R.EVIDENCE}
        self.assertIn("2026 届", ev["E6"]["point"])
        self.assertEqual(ev["E27"]["level"], "E1")
        self.assertIn("2027 届", ev["E27"]["point"])
        self.assertIn("随机抽考 1 题", ev["E27"]["point"])
        self.assertIn("30 分调整为 10 分", ev["E27"]["point"])
        # 必须写明冲突来自届别，避免下一轮有人拿 E27 去删 E6
        self.assertIn("届别不同", ev["E27"]["point"])

    def test_安全条款已取一手原文(self):
        """不能只写「E28 里没有」：E29 是规程全文，E1 第 8 条是部级安全管理要求。"""
        ev = {e["id"]: e for e in R.EVIDENCE}
        self.assertIn("第十五条", ev["E29"]["point"])
        self.assertIn("确保教师和学生的人身安全", ev["E29"]["point"])
        self.assertIn("第二十三条", ev["E29"]["point"])          # 操作级细则交地方自定
        self.assertEqual(ev["E29"]["level"], "E1")
        self.assertIn("强化实验教学安全管理", ev["E1"]["point"])
        self.assertIn("有危险性、破坏性和对环境有危害的实验", ev["E1"]["point"])
        # E28 是转发通知，必须指向规程正文；旧结论「不含安全条款」必须已删除
        self.assertIn("见 E29", ev["E28"]["point"])
        self.assertNotIn("不构成任何实验室安全条款的依据", ev["E28"]["point"])

    def test_每条缺口都写了已取到的一手材料(self):
        """缺口表只写「未获取」等于没交代工作：每条都得说清手里已经有什么。"""
        for g in R.DATA["gaps"]:
            self.assertIn("got", g, "缺口「%s」没写已取到的材料" % g["item"])
            self.assertGreater(len(g["got"]), 10, "缺口「%s」的 got 太短" % g["item"])

    def test_法规条款已入库且可核对(self):
        ev = {e["id"]: e for e in R.EVIDENCE}
        self.assertEqual(ev["E31"]["level"], "E1")
        self.assertIn("第二十四条", ev["E31"]["point"])
        self.assertIn("保证性承诺", ev["E31"]["point"])
        self.assertIn("不满十四周岁", ev["E32"]["point"])
        self.assertIn("在线教育网络产品和服务", ev["E32"]["point"])

    def test_装备规范是行业标准不是国家标准(self):
        """曾把 JY/T 0385-2006 记成「国家标准计划」，名称也错成「装备安全规范」。"""
        e30 = {e["id"]: e for e in R.EVIDENCE}["E30"]
        self.assertIn("JY/T 0385-2006", e30["point"])
        self.assertIn("JY/T 0386-2006", e30["point"])
        self.assertIn("2006 年 10 月 1 日起实施", e30["point"])
        # 发布句与更正句各需一处「教育行业标准」，只写一处说明有一处被改回「国家标准」
        self.assertGreaterEqual(e30["point"].count("教育行业标准"), 2,
                                "两处都必须写明是教育行业标准（JY/T），不能写成国家标准")
        self.assertNotIn("GB/T 0385", e30["point"])

    def test_两条新缺口已登记(self):
        gaps = {g["item"]: g for g in R.DATA["gaps"]}
        self.assertTrue(any("区县" in k for k in gaps))
        self.assertTrue(any("操作级安全细则" in k for k in gaps))
        for g in R.DATA["gaps"]:
            self.assertIn(g["status"], ("未获取", "部分获取"))
            self.assertGreater(len(g["why"]), 20)


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

    def test_铜陵届别在页面上可读(self):
        # 「各 10 分」必须在，但必须带届别；裸写法会被读成「铜陵现在就是各 10 分」
        self.assertIn("2026 届", self.html)
        self.assertIn("2027 届", self.html)
        self.assertIn("随机抽考 1 题", self.html)
        self.assertNotIn("铜陵物理、化学各 10 分", self.html)

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
        for s in ("1.2 亿", "340%", "30.9%", "1434.4", "各 10 分", "2025-09-01",
                  "15.6 亿", "91%", "47 项", "学科类", "87.6 亿元",
                  # 第 13 节：财商已在课标、心理每校至少 1 名、综合实践有课时
                  "5720", "财经与生活", "每校至少", "316 号", "每周不少于 2 课时"):
            self.assertIn(s, self.html)

    def test_section_12_present(self):
        self.assertIn('id="s12"', self.html)
        self.assertIn("兴趣类赛道的判定", self.html)

    def test_section_13_present(self):
        self.assertIn('id="s13"', self.html)
        self.assertIn("学校没教", self.html)
        # 「财商」这个前提必须被正文更正，而不是只在数据里
        self.assertIn("道德与法治 4 年级", self.html)
        self.assertIn("设计禁区", self.html)

    def test_section_14_present(self):
        self.assertIn('id="s14"', self.html)
        self.assertIn("表 14-1", self.html)
        # To C 的四条铁律与「停手信号」必须在正文，而不是只在数据里
        self.assertIn("不卖课时", self.html)
        self.assertIn("停手信号", self.html)

    def test_section_14_5_has_b_end_gate(self):
        """§14.5 必须点明 B 端进校的资质门槛，否则读者会以为「不做 To C 就直接进校卖」。"""
        self.assertIn("个人身份不能直接进校提供服务", self.html)
        self.assertIn("#ev-E26", self.html)

    def test_toc_anchors_resolve(self):
        toc = self.html.split('<nav class="toc">', 1)[1].split("</nav>", 1)[0]
        anchors = re.findall(r'href="#([^"]+)"', toc)
        self.assertGreaterEqual(len(anchors), 14)
        for a in anchors:
            self.assertIn('id="%s"' % a, self.html)

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
