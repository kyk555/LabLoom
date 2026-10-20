# -*- coding: utf-8 -*-
"""样例/ 下两个 HTML 样本的回归测试（纯标准库，python -B 直接跑）。

守三类不变量：
1. 形态：单文件、无外网依赖、9 项字段章节齐全。
2. 事实：关键数值串必须出现在页面上——改了公式就得同时改文本，不允许只改一边。
3. 诚实：依据未核实时必须写明「待核实 / 不得外发」，不许把半成品当成品。
"""
import os
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

PHYS = os.path.join(ROOT, "样例", "初中物理", "阿基米德原理-01.html")
MATH = os.path.join(ROOT, "样例", "候选-理解型演示", "圆面积割补-01.html")


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


class TestSamples(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phys = read(PHYS)
        cls.math = read(MATH)

    def test_两个样本都存在(self):
        self.assertTrue(os.path.isfile(PHYS), PHYS)
        self.assertTrue(os.path.isfile(MATH), MATH)

    def test_不依赖外网资源(self):
        for name, html in (("物理", self.phys), ("数学", self.math)):
            for tag in re.findall(r"<(?:script|link|img)[^>]*>", html):
                self.assertIsNone(
                    re.search(r'(?:src|href)\s*=\s*["\']https?://', tag),
                    "%s 样本引用了外网资源：%s" % (name, tag))

    def test_九项字段章节齐全(self):
        for name, html in (("物理", self.phys), ("数学", self.math)):
            for i in range(1, 10):
                self.assertIn("<h2>%d　" % i, html, "%s 样本缺第 %d 节" % (name, i))

    def test_物理关键数值可复算(self):
        # 50 cm³ 全浸水中、g=10 → 0.500 N；5×10⁻⁵ m³；1 g/cm³ = 1000 kg/m³
        for s in ("0.500", "5.00×10⁻⁵", "F浮 = ρ液 · g · V排", "1×10⁻⁶ m³", "1000 kg/m³"):
            self.assertIn(s, self.phys)

    def test_数学关键数值可复算(self):
        # a=8 → 64.00 / 50.24 / 13.76 / 21.50 %；n=16 → 97.45 % / 99.36 %
        for s in ("64.00", "50.24", "13.76", "21.50 %", "97.45 %", "99.36 %", "πr²"):
            self.assertIn(s, self.math)

    def test_物理结论只能是F浮等于G排(self):
        # 「浮力等于物体重力」只允许出现在纠错条目里，结论区必须写 F浮 = G排 并交代浮沉条件
        self.assertIn("F浮 = G排", self.phys)
        self.assertIn("浮沉条件", self.phys)
        self.assertIn("F浮 与物体本身的重力无关", self.phys)

    def test_数学必须声明不在学科范围内(self):
        self.assertIn("数学不属于本项目的学科范围", self.math)
        self.assertIn("不代表项目要接数学内容", self.math)

    def test_依据未核实必须显式声明(self):
        for name, html in (("物理", self.phys), ("数学", self.math)):
            self.assertIn("依据待核实", html, "%s 样本没标依据状态" % name)
            self.assertIn("不得外发", html, "%s 样本没标不可外发" % name)
            self.assertIn("课标条目", html, "%s 样本缺课标条目一行" % name)

    def test_安全提示不能省(self):
        for name, html in (("物理", self.phys), ("数学", self.math)):
            self.assertIn("无需特殊防护", html, "%s 样本缺安全提示" % name)

    def test_没有占位符残留(self):
        for name, html in (("物理", self.phys), ("数学", self.math)):
            for bad in ("TODO", "FIXME", "{{", "}}", "lorem", "%s"):
                self.assertNotIn(bad, html, "%s 样本残留占位符 %r" % (name, bad))


if __name__ == "__main__":
    unittest.main()
