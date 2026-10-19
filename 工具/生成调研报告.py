# -*- coding: utf-8 -*-
"""生成《K12 实验内容工具：可行性调研与定位建议》HTML 报告。

设计原则（对应 .clinerules/03）：
- 报告里的数字只出现在本文件的 DATA / EVIDENCE 里，HTML 一律由它们渲染；
  改口径只改这里，然后重跑本脚本，不手改产物。
- 不写 Markdown 版报告，不做 md + html 双份。
- 不依赖外网 CDN：echarts 走同目录 assets/，页面离线双击可看。

用法：
    python -B 工具/生成调研报告.py          # 生成到 报告/
    python -B 工具/生成调研报告.py --检查    # 只校验不写盘
"""

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_NAME = "2026-10-20-K12实验内容工具-可行性调研与定位建议.html"
OUT_PATH = os.path.join(ROOT, "报告", OUT_NAME)
ECHARTS_REL = "assets/echarts.min.js"

META = {
    "title": "K12 实验内容工具：可行性调研与定位建议",
    "subtitle": "面向「Vibe Coding 生成实验内容 + 家长个性化教学」这一设想的投资前期评估",
    "version": "v1.0",
    "date": "2026-10-20",
    "scope": "内部决策用 · 不构成对外投资建议",
    "author": "LabLoom 项目组",
}

# 证据等级：E1 一手法规/公文原文 > E2 官方媒体政策报道（未取原文）
#           > E3 行业媒体/企业报道 > E4 企业自述/机构预测
EVIDENCE = [
    {
        "id": "E1",
        "title": "教育部《关于加强和改进中小学实验教学的意见》教基〔2019〕16 号",
        "publisher": "中华人民共和国教育部",
        "date": "2019-11-28",
        "level": "E1",
        "url": "http://www.moe.gov.cn/srcsite/A06/s3321/201911/t20191128_409958.html",
        "fetched": "2026-10-20 04:59:40",
        "sha256": "29fb86dd3c5037a1",
        "point": "第 6 条：2023 年前将实验操作纳入初中学业水平考试，成绩纳入高中招生录取依据；有危险性实验可用 AR/VR 呈现。",
    },
    {
        "id": "E2",
        "title": "中办、国办《关于进一步减轻义务教育阶段学生作业负担和校外培训负担的意见》",
        "publisher": "中国政府网（新华社受权发布）",
        "date": "2021-07-24",
        "level": "E1",
        "url": "http://www.gov.cn/zhengce/2021-07/24/content_5627132.htm",
        "fetched": "2026-10-20 05:00:04",
        "sha256": "05c0aa9a054c2ee2",
        "point": "第 13/14 条：不再审批新的学科类机构，非学科机构不得从事学科培训；第 15 条：线上培训不得传播「拍照搜题」等惰化思维的方法。",
    },
    {
        "id": "E3",
        "title": "教育部等十八部门《关于加强新时代中小学科学教育工作的意见》教监管〔2023〕2 号",
        "publisher": "喀左县人民政府（转载全文，发文机关为教育部等十八部门）",
        "date": "2023-05",
        "level": "E1",
        "url": "https://www.kazuo.gov.cn/html/KZXZF/202509/0175671693309870.html",
        "fetched": "2026-10-20 05:00:16",
        "sha256": "f0e2869babec54ca",
        "point": "第 5 条：探索利用 AI、VR 改进和强化实验教学；第 17 条：加强实验考查；第 7 条：科学教育为课后服务必备项目。",
    },
    {
        "id": "E4",
        "title": "《人工智能生成合成内容标识办法》",
        "publisher": "国家网信办等四部门（cac.gov.cn 原文）",
        "date": "2025-03-14 发布 · 2025-09-01 施行",
        "level": "E1",
        "url": "https://www.cac.gov.cn/2025-03/14/c_1743654684782215.htm",
        "fetched": "2026-10-20 05:00:00",
        "sha256": "6cea0803c5703625",
        "point": "第 3/4/5 条：显式 + 隐式标识；提供下载、复制、导出时须确保文件含显式标识。第 14 条：2025-09-01 起施行。",
    },
    {
        "id": "E5",
        "title": "《中小学生成式人工智能使用指南（2025 年版）》政策报道",
        "publisher": "光明网（转教育部基础教育教学指导委员会发布）",
        "date": "2025-05-14",
        "level": "E2",
        "url": "https://tech.gmw.cn/2025-05/14/content_38025442.htm",
        "fetched": "2026-10-20 04:59:24",
        "sha256": "42db06763ca84370",
        "point": "禁止学生直接复制 AI 生成内容作为作业或考试答案；严禁输入试题与个人身份信息；学校建立工具「白名单」；家长承担监督引导责任。",
    },
    {
        "id": "E6",
        "title": "《2026 年初中学业水平实验操作考试工作方案发布》",
        "publisher": "铜陵市人民政府",
        "date": "2026-02-02",
        "level": "E1",
        "url": "https://www.tl.gov.cn/tlsrmzf/zwlb/pc/content/content_2018119394908758016.html",
        "fetched": "2026-10-20 04:54:49",
        "sha256": "8968c6b3ff0dc743",
        "point": "物理、化学各 10 分，成绩全部计入中考录取总分；考前随机抽题、每科 20 分钟、一人一桌独立操作。",
    },
    {
        "id": "E7",
        "title": "《腾讯内测「懂了鸭」，试水 AI 交互式互动内容赛道》（含实测评测）",
        "publisher": "人人都是产品经理 · 作者「读佳」",
        "date": "2026-10（内测期报道）",
        "level": "E3",
        "url": "https://www.woshipm.com/ai/6480468.html",
        "fetched": "2026-10-20 04:59:01",
        "sha256": "ac57534b8c26a2d5",
        "point": "腾讯内测；网页 + 微信小程序；面向亲子、教师与知识创作者；以「奇妙卡」为载体，带内容社区、灵感墙与「改编」；实测可一句话生成五子棋；文末明确「AI 生成内容严谨性需人工校验」「对加载性能与设备有要求」。",
    },
    {
        "id": "E8",
        "title": "飞象老师 3.0 上线：一句话生成教育应用",
        "publisher": "钛媒体 / TechWeb / 扬子晚报 / 同花顺（多源同日互证）",
        "date": "2026-08-24",
        "level": "E3",
        "url": "https://www.tmtpost.com/nictation/8114654.html",
        "fetched": "仅检索摘要，未取正文",
        "sha256": "—",
        "point": "新增「一键生成教育应用」，生成物可直接访问、支持 AI 调用与数据保存；示例含化学学习工具；叙事重心在教师。",
    },
    {
        "id": "E9",
        "title": "《1.2 亿月活，零家盈利：AI 教育的钱烧哪了》",
        "publisher": "新浪财经 · 福布斯中国教育专栏（引 QuestMobile 与各公司财报）",
        "date": "2026-09-13",
        "level": "E3",
        "url": "https://cj.sina.com.cn/articles/view/1765373140/693974d401901kqh8",
        "fetched": "2026-10-20 04:59:03",
        "sha256": "3812239cd223c06a",
        "point": "2025Q3 AI 教育应用 MAU 1.2 亿、同比 +340%；无一家跑通盈利闭环；好未来营销费用率 30.9%、学习机为「战略性亏损」；讯飞批阅机覆盖 5000+ 校、续购率 >90%；有道连续 8 季经营利润为正但规模受限。",
    },
    {
        "id": "E10",
        "title": "NOBOOK 虚拟实验（含「实验加试」产品线）",
        "publisher": "北京乐步教育（企业官网自述）",
        "date": "无发布日期",
        "level": "E4",
        "url": "https://www.nobook.com/web-exam.html",
        "fetched": "仅检索摘要，未取正文",
        "sha256": "—",
        "point": "已覆盖物理、化学、生物与小学科学的仿真实验，并单独设有面向实验操作考试的「实验加试」产品线。",
    },
    {
        "id": "E11",
        "title": "《2026 年一季度 AI 应用价值榜》",
        "publisher": "每日经济新闻（引 QuestMobile 口径）",
        "date": "2026-04-21",
        "level": "E3",
        "url": "https://www.nbd.com.cn/articles/2026-04-21/4350446.html",
        "fetched": "仅检索摘要，未取正文",
        "sha256": "—",
        "point": "豆包爱学 2026Q1 MAU 1434.4 万，位列 AI 教育赛道月活榜首。",
    },
    {
        "id": "E12",
        "title": "艾媒咨询《2024—2025 年中国智能学习机市场趋势研究报告》摘要",
        "publisher": "艾媒咨询（雪球转载摘要）",
        "date": "2024-05",
        "level": "E4",
        "url": "https://xueqiu.com/9582690951/291783323",
        "fetched": "仅检索摘要，未取正文",
        "sha256": "—",
        "point": "预测 2025 年中国教育智能硬件市场规模超 1000 亿元。属预测值，仅作量级参照，不作为测算输入。",
    },
    {
        "id": "E13",
        "title": "河南省 2026 年中招理化生实验操作按满分 30 分计入总成绩",
        "publisher": "南阳本地宝（媒体转述，未见省级原文件）",
        "date": "2026-04-20",
        "level": "E3",
        "url": "http://ny.bendibao.com/edu/2026420/29343.shtm",
        "fetched": "仅检索摘要，未取正文",
        "sha256": "—",
        "point": "物理、化学、生物学实验操作按满分 30 分计入中招录取总成绩。待以省教育厅原文件复核。",
    },
]

# ---------------------------------------------------------------------------
# 数据区：报告里出现的每个数字/评分都来自这里
# ---------------------------------------------------------------------------

DATA = {
    "as_of": "2026-10-20",
    # 政策与考试落地时间轴（全部对应 EVIDENCE 里的编号）
    "policy": [
        {"date": "2019-11", "tag": "政策", "title": "实验操作纳入中考写进部级文件",
         "body": "要求 2023 年前将实验操作纳入初中学业水平考试，成绩纳入高中招生录取依据。", "ev": "E1"},
        {"date": "2021-07", "tag": "政策", "title": "「双减」划出学科/非学科边界",
         "body": "不再审批新的学科类机构；非学科机构不得从事学科培训；线上不得传播「拍照搜题」类方法。", "ev": "E2"},
        {"date": "2023-05", "tag": "政策", "title": "科学教育「加法」明确 AI/VR 路径",
         "body": "探索利用 AI、VR 改进强化实验教学；加强实验考查；科学教育列为课后服务必备项目。", "ev": "E3"},
        {"date": "2025-05", "tag": "合规", "title": "中小学生成式 AI 使用指南",
         "body": "禁止直接复制 AI 生成内容作为作业/答案；严禁输入试题与身份信息；学校建「白名单」。", "ev": "E5"},
        {"date": "2025-09", "tag": "合规", "title": "生成内容标识办法施行",
         "body": "生成内容须带显式/隐式标识；下载、复制、导出时文件内也要有显式标识。", "ev": "E4"},
        {"date": "2026-02", "tag": "落地", "title": "铜陵：物理、化学各 10 分全额计入中考总分",
         "body": "应历届毕业生均须参考；考前随机抽题、每科 20 分钟、一人一桌独立操作。", "ev": "E6"},
        {"date": "2026-04", "tag": "落地", "title": "河南：理化生实验操作 30 分计入总成绩（媒体转述）",
         "body": "郑州考试窗口 4 月 1—24 日。该条为媒体转述，需以省教育厅原文件复核。", "ev": "E13"},
    ],

    # 竞争矩阵：x = 生成自由度（0 保守 → 10 任意生成）；y = 校验与可验证性
    # size = 相对规模（1 最小 → 5 最大），仅作视觉权重，非量化指标
    "competitors": [
        {"name": "腾讯「懂了鸭」", "x": 8.6, "y": 3.0, "size": 4,
         "note": "内测；亲子+教师+创作者；奇妙卡、社区、灵感墙、改编；实测一句话生成五子棋", "ev": "E7"},
        {"name": "飞象老师 3.0", "x": 8.0, "y": 2.6, "size": 4,
         "note": "一句话生成可访问、可调 AI、带数据保存的教育应用；重心在教师", "ev": "E8"},
        {"name": "豆包爱学 / 搜题类", "x": 5.0, "y": 4.2, "size": 5,
         "note": "讲题与搜题为主，2026Q1 MAU 1434.4 万；免费换规模", "ev": "E11"},
        {"name": "学习机（学而思/有道）", "x": 3.2, "y": 6.5, "size": 5,
         "note": "内容自建、教研背书强；但营销费用率 30.9%、硬件品类下滑", "ev": "E9"},
        {"name": "NOBOOK 虚拟实验", "x": 2.0, "y": 9.0, "size": 3,
         "note": "理化生+小学科学仿真实验，另设「实验加试」产品线，长期做 B 端", "ev": "E10"},
        {"name": "LabLoom（建议定位）", "x": 6.2, "y": 8.6, "size": 1,
         "note": "受限生成 + 评分点对齐 + 可验证留痕；不与大厂拼自由度", "ev": "—"},
    ],

    # 定位候选评分（1—5 分，主观判断，方法见「评分口径」）
    "weights": [
        {"key": "demand", "label": "需求真实性", "w": 0.30},
        {"key": "room", "label": "竞争空间", "w": 0.25},
        {"key": "pay", "label": "付费证据", "w": 0.20},
        {"key": "fit", "label": "能力匹配", "w": 0.15},
        {"key": "risk", "label": "合规可控", "w": 0.10},
    ],
    "positioning": [
        {"id": "A", "name": "家长自助生成器（原始设想）",
         "scores": {"demand": 2, "room": 1, "pay": 2, "fit": 4, "risk": 3},
         "verdict": "不建议", "why": "生成是手段不是需求；家长要结果不要创作；与腾讯「懂了鸭」正面重合，且对方免费。"},
        {"id": "B", "name": "中考实验操作「评分点对齐」微练习",
         "scores": {"demand": 4, "room": 3, "pay": 3, "fit": 4, "risk": 4},
         "verdict": "推荐（楔子）", "why": "考试计分是硬约束；地方评分标准与教材版本对齐是脏活，大厂不做的护城河。"},
        {"id": "C", "name": "教师端「章节实验 30 分钟改造」",
         "scores": {"demand": 4, "room": 3, "pay": 4, "fit": 5, "risk": 3},
         "verdict": "推荐（渠道）", "why": "B 端付费已被验证（批阅机续购率 >90%）；教师是信任入口，可反哺内容资产。"},
        {"id": "D", "name": "校验层白标（卖铲子给生成器）",
         "scores": {"demand": 3, "room": 4, "pay": 2, "fit": 5, "risk": 2},
         "verdict": "备选（终局）", "why": "风险最低但要求权威性；需先有 B/C 的内容资产与错误样本库才有说服力。"},
    ],

    # 月活口径（不同时点，仅示量级，不可相加）
    "mau": [
        {"name": "AI 教育应用整体", "value": 12000, "period": "2025Q3", "ev": "E9", "disp": "1.2 亿"},
        {"name": "豆包爱学", "value": 1434.4, "period": "2026Q1", "ev": "E11", "disp": "1434.4 万"},
        {"name": "快对 AI", "value": 646.9, "period": "2025-09", "ev": "E9", "disp": "646.9 万"},
    ],

    # 单实验结果经济：全部为内部假设，仅用于排优先级，不用于定价决策
    "unit_econ": {
        "hourly": 30,          # 元/小时，内部工时估值（假设）
        "gen_h": 0.5,          # 生成初稿
        "rule_h": 4.0,         # 写校验规则（评分点→可判定条件）
        "material_h": 1.0,     # 素材整理（图、器材、记录表）
        "review_hs": [1, 2, 4],# 人工复核工时敏感性
        "prices": [9.9, 19.9, 49],
    },

    # 数据缺口：明确写出来，不用估算冒充实测
    "gaps": [
        {"item": "家庭教育支出 / 单个数字内容 ARPPU",
         "status": "未获取",
         "why": "检索到的均为豆丁、人人文库等 SEO 文档站拼凑内容，无原始抽样与口径，不予采信。"},
        {"item": "「实验内容」细分市场规模",
         "status": "未获取",
         "why": "公开报告中无此口径；教育智能硬件 1000 亿为预测值，与内容层不可直接换算。"},
        {"item": "AI 教育产品的付费转化率 / 留存曲线",
         "status": "未获取",
         "why": "无公开披露；因此本报告不做 LTV / CAC 测算，只做付费意愿的前置验证。"},
        {"item": "各地实验操作考试评分标准全文",
         "status": "部分获取",
         "why": "仅取得铜陵一地的一手方案；河南等地为媒体转述，需逐地取原文件。"},
    ],

    # 验证计划：可量化门槛 + Kill 条件
    "hypotheses": [
        {"id": "H1", "name": "家长愿为「考前实验操作演练」付费",
         "method": "20 位初中家长看 1 个 demo 后报价", "gate": "≥6 位愿付 29—49 元/实验包，或 ≥3 位预付",
         "kill": "连续 10 位无人愿付 → A/B 类 C 端方向暂停"},
        {"id": "H2", "name": "教师愿用「章节实验改造」",
         "method": "访谈 8 位理化生教师并现场试用", "gate": "≥4 位愿在下节课实际使用",
         "kill": "≤1 位愿用 → C 类渠道不成立"},
        {"id": "H3", "name": "内容正确性可被工程化保证",
         "method": "3 个实验写规则校验 + 双人复核", "gate": "评分点规则覆盖 ≥90%；科学性错误 0 处",
         "kill": "出现 1 处安全性/科学性错误且规则无法拦截 → 产品不成立"},
        {"id": "H4", "name": "单位成本可接受",
         "method": "记录 3 个实验全流程工时与 API 费用", "gate": "≤2 小时人工 + ≤5 元 API / 实验",
         "kill": ">6 小时/实验 → 内容资产无法规模化"},
        {"id": "H5", "name": "与地方考试方案对齐",
         "method": "用铜陵官方方案逐条对照", "gate": "覆盖 ≥80% 评分点",
         "kill": "<50% → 放弃「评分点对齐」这一卖点"},
    ],

    # 风险：概率/影响 1—5，均可量化跟踪
    "risks": [
        {"name": "大厂免费覆盖同类功能", "p": 5, "i": 4, "mitigation": "不拼生成自由度，拼本地评分点对齐与可复核证据链"},
        {"name": "生成内容出现科学性/安全性错误", "p": 3, "i": 5, "mitigation": "数值由脚本算、规则正反例成对、双人复核、版本可回滚"},
        {"name": "未成年人合规（标识/信息保护）", "p": 3, "i": 4, "mitigation": "生成物打标；不收集 14 岁以下个人信息；家长账号制"},
        {"name": "地方实验计分政策变动", "p": 2, "i": 4, "mitigation": "保留科学教育/课后服务第二场景，内容不绑定单一考试"},
        {"name": "单点依赖个人、质量不可复制", "p": 3, "i": 3, "mitigation": "模板与校验规则文档化，进 .clinerules 与回归样本"},
    ],
}


# ---------------------------------------------------------------------------
# 计算区：报告里所有派生数字（加权分、成本、回本单量）都在这里算
# ---------------------------------------------------------------------------

def weighted_scores():
    """按 DATA['weights'] 计算各定位候选的加权总分（保留 2 位）。"""
    out = []
    for item in DATA["positioning"]:
        total = 0.0
        for w in DATA["weights"]:
            total += item["scores"][w["key"]] * w["w"]
        row = dict(item)
        row["total"] = round(total, 2)
        out.append(row)
    return sorted(out, key=lambda r: r["total"])


def unit_cost(review_h):
    """单个实验首版的人工工时成本（元）。review_h 为人工复核工时。"""
    u = DATA["unit_econ"]
    hours = u["gen_h"] + u["rule_h"] + u["material_h"] + review_h
    return round(hours * u["hourly"], 1)


def unit_hours(review_h):
    u = DATA["unit_econ"]
    return round(u["gen_h"] + u["rule_h"] + u["material_h"] + review_h, 1)


def breakeven_units(review_h, price):
    """按定价 price 回收单实验首版成本所需销量（向上取整）。"""
    import math
    return int(math.ceil(unit_cost(review_h) / price))


def breakeven_table():
    rows = []
    for h in DATA["unit_econ"]["review_hs"]:
        rows.append({
            "review_h": h,
            "hours": unit_hours(h),
            "cost": unit_cost(h),
            "units": [breakeven_units(h, p) for p in DATA["unit_econ"]["prices"]],
        })
    return rows


def has_cjk(s):
    return any("\u4e00" <= ch <= "\u9fff" for ch in s)


def verify_data():
    """结构性自检：跑不通就不写盘。返回错误列表。"""
    errs = []
    ids = [e["id"] for e in EVIDENCE]
    if len(ids) != len(set(ids)):
        errs.append("EVIDENCE 存在重复 id")
    for e in EVIDENCE:
        for k in ("id", "title", "publisher", "date", "level", "url", "fetched", "point"):
            if not e.get(k):
                errs.append("证据 %s 缺字段 %s" % (e.get("id", "?"), k))
        if e.get("level") not in ("E1", "E2", "E3", "E4"):
            errs.append("证据 %s 等级非法: %s" % (e.get("id"), e.get("level")))
    known = set(ids) | {"—"}
    for p in DATA["policy"]:
        if p["ev"] not in known:
            errs.append("时间轴引用了不存在的证据: %s" % p["ev"])
    for c in DATA["competitors"]:
        if c["ev"] not in known:
            errs.append("竞品引用了不存在的证据: %s" % c["ev"])
    for m in DATA["mau"]:
        if m["ev"] not in known:
            errs.append("MAU 引用了不存在的证据: %s" % m["ev"])
    wsum = round(sum(w["w"] for w in DATA["weights"]), 6)
    if abs(wsum - 1.0) > 1e-9:
        errs.append("权重和不为 1: %s" % wsum)
    for item in DATA["positioning"]:
        for w in DATA["weights"]:
            v = item["scores"].get(w["key"])
            if not isinstance(v, int) or not 1 <= v <= 5:
                errs.append("定位 %s 的 %s 分值越界: %s" % (item["id"], w["key"], v))
    for r in DATA["risks"]:
        for k in ("p", "i"):
            if not 1 <= r[k] <= 5:
                errs.append("风险「%s」的 %s 越界" % (r["name"], k))
    return errs


# ---------------------------------------------------------------------------
# 渲染区
# ---------------------------------------------------------------------------

CSS = """
:root{
  --ink:#15181d; --ink2:#3c4450; --muted:#6b7480; --line:#e3e6ea;
  --bg:#f6f7f9; --card:#fff; --accent:#0f6b5f; --accent2:#c2410c;
  --warn:#b45309; --bad:#b91c1c; --ok:#15803d; --e1:#0f6b5f; --e2:#0e7490;
  --e3:#a16207; --e4:#7c3aed;
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--ink);
  font:16px/1.75 -apple-system,"Segoe UI","Microsoft YaHei","PingFang SC",sans-serif}
.wrap{max-width:1080px;margin:0 auto;padding:0 20px 80px}
header.hero{background:linear-gradient(160deg,#12211f 0%,#0f2f2a 55%,#123a33 100%);
  color:#eef5f3;padding:56px 0 40px;margin-bottom:36px}
header.hero .wrap{padding-bottom:0}
.kicker{font-size:12px;letter-spacing:.18em;text-transform:uppercase;color:#7fc8b8;margin-bottom:14px}
h1{font-size:30px;line-height:1.35;margin:0 0 12px;font-weight:700;letter-spacing:.01em}
.sub{color:#b9d3cc;font-size:15px;max-width:760px;margin:0 0 22px}
.meta{display:flex;flex-wrap:wrap;gap:8px 20px;font-size:13px;color:#9fbcb5}
.meta b{color:#e6f2ee;font-weight:600}
.verdict{margin-top:26px;display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px}
.verdict div{background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.14);
  border-radius:10px;padding:12px 14px}
.verdict span{display:block;font-size:12px;color:#9fbcb5;margin-bottom:4px}
.verdict strong{font-size:17px;color:#fff}
h2{font-size:22px;margin:52px 0 6px;padding-top:8px;border-top:2px solid var(--ink);
  scroll-margin-top:16px}
h2 .num{color:var(--accent);font-variant-numeric:tabular-nums;margin-right:10px}
h3{font-size:17px;margin:30px 0 8px;color:var(--ink)}
h4{font-size:15px;margin:20px 0 6px;color:var(--ink2)}
p{margin:10px 0;color:var(--ink2)}
.lead{font-size:17px;color:var(--ink);border-left:3px solid var(--accent);padding-left:14px}
.small{font-size:13px;color:var(--muted)}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;
  padding:20px 22px;margin:16px 0}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.grid3{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}
@media(max-width:760px){
  .grid2,.grid3{grid-template-columns:1fr}
  h1{font-size:24px} h2{font-size:19px}
  .wrap{padding:0 14px 60px}
}
.callout{border-left:4px solid var(--accent);background:#eff7f5;padding:14px 18px;
  border-radius:0 10px 10px 0;margin:16px 0}
.callout.bad{border-color:var(--bad);background:#fdf2f2}
.callout.warn{border-color:var(--warn);background:#fdf7ec}
.callout.ok{border-color:var(--ok);background:#f0f9f2}
.callout b{color:var(--ink)}
table{width:100%;border-collapse:collapse;margin:14px 0;font-size:14px;
  background:#fff;border:1px solid var(--line);border-radius:10px;overflow:hidden}
caption{caption-side:top;text-align:left;font-size:13px;color:var(--muted);padding:0 0 6px}
th,td{padding:9px 11px;border-bottom:1px solid var(--line);vertical-align:top;text-align:left}
th{background:#f1f4f6;font-weight:600;color:var(--ink);font-size:13px;white-space:nowrap}
tr:last-child td{border-bottom:none}
td.num,th.num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
.tbl-scroll{overflow-x:auto;-webkit-overflow-scrolling:touch}
.badge{display:inline-block;font-size:11px;line-height:1.6;padding:1px 7px;border-radius:999px;
  font-weight:600;letter-spacing:.02em;white-space:nowrap}
.b-E1{background:#e3f3ef;color:var(--e1)} .b-E2{background:#e0f2f7;color:var(--e2)}
.b-E3{background:#fbf1dc;color:var(--e3)} .b-E4{background:#f1eafe;color:var(--e4)}
.tag{display:inline-block;font-size:11px;padding:1px 7px;border:1px solid var(--line);
  border-radius:5px;color:var(--muted);background:#fff}
.tag.policy{color:#0e7490;border-color:#bae6fd;background:#f0f9ff}
.tag.compliance{color:#7c3aed;border-color:#ddd6fe;background:#f5f3ff}
.tag.landing{color:#b45309;border-color:#fde68a;background:#fffbeb}
.chart{width:100%;height:400px;background:#fff;border:1px solid var(--line);
  border-radius:12px;margin:12px 0 4px}
.chart-note{font-size:12px;color:var(--muted);margin:0 0 18px}
details{margin:10px 0}
summary{cursor:pointer;font-size:13px;color:var(--accent);padding:4px 0}
.timeline{position:relative;margin:20px 0 10px;padding-left:26px}
.timeline::before{content:"";position:absolute;left:7px;top:4px;bottom:4px;width:2px;
  background:linear-gradient(#cfe3de,#e6e9ee)}
.tl-item{position:relative;margin-bottom:18px}
.tl-item::before{content:"";position:absolute;left:-24px;top:9px;width:10px;height:10px;
  border-radius:50%;background:#fff;border:2px solid var(--accent)}
.tl-date{font-size:12px;color:var(--muted);font-variant-numeric:tabular-nums}
.tl-title{font-weight:600;margin:2px 0 2px;font-size:15px}
.tl-body{font-size:14px;color:var(--ink2);margin:0}
ul,ol{margin:10px 0;padding-left:22px;color:var(--ink2)}
li{margin:5px 0}
.kv{display:grid;grid-template-columns:120px 1fr;gap:6px 14px;font-size:14px}
.kv dt{color:var(--muted)}
.kv dd{margin:0}
footer{border-top:1px solid var(--line);margin-top:60px;padding-top:18px;
  font-size:12px;color:var(--muted)}
.toc{background:#fff;border:1px solid var(--line);border-radius:12px;padding:16px 20px;margin:0 0 8px}
.toc ol{columns:2;column-gap:28px;margin:6px 0 0;padding-left:20px;font-size:14px}
@media(max-width:760px){.toc ol{columns:1}}
.toc a{color:var(--ink2);text-decoration:none;border-bottom:1px dotted #c9ced6}
.toc a:hover{color:var(--accent);border-bottom-color:var(--accent)}
.pill{display:inline-block;padding:2px 9px;border-radius:999px;font-size:12px;font-weight:600}
.pill.go{background:#e6f6ec;color:var(--ok)} .pill.no{background:#fdecec;color:var(--bad)}
.pill.mid{background:#fdf5e3;color:var(--warn)}
"""


def badge(level):
    return '<span class="badge b-%s">%s</span>' % (level, level)


LEVEL_LABEL = {
    "E1": "一手法规/公文原文",
    "E2": "官方媒体政策报道（未取原文）",
    "E3": "行业媒体/企业报道",
    "E4": "企业自述/机构预测",
}

TAG_CLASS = {"政策": "policy", "合规": "compliance", "落地": "landing"}


def ev_brief(ev_id):
    """把证据编号渲染成可点的小标签。"""
    if ev_id == "—":
        return '<span class="tag">本文判断</span>'
    for e in EVIDENCE:
        if e["id"] == ev_id:
            return '<a class="tag" href="#ev-%s" title="%s">%s</a>' % (
                e["id"], e["title"].replace('"', "&quot;"), e["id"])
    return '<span class="tag">%s</span>' % ev_id


def render_hero():
    return """
<header class="hero">
  <div class="wrap">
    <div class="kicker">可行性调研 · 投资前期评估 · %(date)s</div>
    <h1>%(title)s</h1>
    <p class="sub">%(subtitle)s</p>
    <div class="meta">
      <div>版本 <b>%(version)s</b></div>
      <div>作者 <b>%(author)s</b></div>
      <div>取证截止 <b>%(date)s 05:00（UTC+8）</b></div>
      <div><b>%(scope)s</b></div>
    </div>
    <div class="verdict">
      <div><span>总体结论</span><strong>有条件推进</strong></div>
      <div><span>原设想（家长自助生成）</span><strong>不建议直接做</strong></div>
      <div><span>建议楔子</span><strong>评分点对齐</strong></div>
      <div><span>先验证、后建平台</span><strong>4 周</strong></div>
    </div>
  </div>
</header>
""" % META


def render_toc():
    items = [
        ("s0", "摘要与核心判断"),
        ("s1", "调研方法与证据分级"),
        ("s2", "需求侧：政策把实验变成了计分项"),
        ("s3", "供给侧：谁已经在做，做到哪一步"),
        ("s4", "技术侧：Vibe Coding 能做什么、不能做什么"),
        ("s5", "商业侧：1.2 亿月活与零家盈利"),
        ("s6", "合规侧：四条不能碰的线"),
        ("s7", "定位建议：四个候选与加权评分"),
        ("s8", "推荐方案：内容资产 + 两个出口"),
        ("s9", "验证计划：五个假设与 Kill 条件"),
        ("s10", "风险与对冲"),
        ("s11", "结论与给决策者的三句话"),
        ("sA", "附录 A 证据台账"),
        ("sB", "附录 B 数据缺口与方法局限"),
    ]
    lis = "\n".join('<li><a href="#%s">%s</a></li>' % (i, t) for i, t in items)
    return '<nav class="toc"><b class="small">目录</b><ol>%s</ol></nav>' % lis


def ev_cell(spec):
    """把「E1 / E3 / E6」这类组合渲染成多个可点标签。"""
    return " ".join(ev_brief(x.strip()) for x in spec.split("/") if x.strip())


def render_s0():
    rows = [
        ("政策", "强顺风，但顺风不等于能赚钱",
         "实验操作已进中考计分；AI/VR 被明确写进实验教学改进路径", "E1 / E3 / E6", "可依赖"),
        ("需求", "真实存在，但与原设想错位",
         "家长买的是「孩子会做、不扣分」，不是「我要自己造课件」", "E6 / E7", "需重新定义"),
        ("供给", "已拥挤，且头部免费",
         "腾讯懂了鸭内测、飞象 3.0、NOBOOK 实验加试均已覆盖相邻场景", "E7 / E8 / E10", "不可正面打"),
        ("技术", "「受限生成」可行，「免检生成」不可行",
         "页面可生成；数值、单位、化学式、安全边界必须由规则与人工兜底", "E7", "可工程化"),
        ("商业", "C 端难，B 端有付费证据",
         "1.2 亿 MAU 但无一家跑通盈利闭环；学校侧续购率 >90%", "E9", "先 B 后 C"),
        ("合规", "成本可控，但一项都不能省",
         "生成内容标识、未成年人保护、禁「拍照搜题」类惰化设计", "E2 / E4 / E5", "内建"),
    ]
    trs = "\n".join(
        "<tr><td><b>%s</b></td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>"
        % (a, b, c, ev_cell(d), e) for a, b, c, d, e in rows)
    return """
<h2 id="s0"><span class="num">00</span>摘要与核心判断</h2>
<p class="lead">这个设想值得做，但<b>不是按现在这个做法做</b>。把「家长用 Vibe Coding 给孩子生成实验内容」当成产品主线，会在三个方向上同时吃亏：需求错位、对手免费、质量兜底成本被低估。可行的是把生成能力收进笼子里——做<b>可验证的实验内容</b>，先服务「实验操作计分」这个硬场景。</p>

<div class="card">
<h3 style="margin-top:0">一句话结论</h3>
<p style="margin-bottom:0">用 4 周、3 个实验、1 个地市，验证「家长愿为评分点对齐的实验演练付费」与「教师愿用章节实验改造」两件事；
两条都不过就停，只过一条就按那一条走。<b>不要先建平台。</b></p>
</div>

<h3>六个维度的判断</h3>
<div class="tbl-scroll">
<table>
<caption>表 0-1　维度判断一览（依据列的证据编号见附录 A）</caption>
<thead><tr><th>维度</th><th>判断</th><th>关键事实</th><th>证据</th><th>对决策的含义</th></tr></thead>
<tbody>%s</tbody>
</table>
</div>

<h3>为什么原设想不成立：三条互相独立的理由</h3>
<div class="grid3">
  <div class="card" style="margin:0">
    <h4 style="margin-top:0">① 把创作成本转给了最没空的人</h4>
    <p class="small" style="margin-bottom:0">家长缺的不是「生成工具」，是<b>判断力与时间</b>：生成出来了，对不对、适不适合自己孩子、扣不扣分，仍要家长判断。工具把工作量从「陪做实验」换成了「审 AI 内容」，并没有减少。</p>
  </div>
  <div class="card" style="margin:0">
    <h4 style="margin-top:0">② 形态与大厂免费产品重合</h4>
    <p class="small" style="margin-bottom:0">腾讯「懂了鸭」已把「家长/教师一句话生成可拖拽、可模拟的互动内容 + 社区 + 改编」整套做完并在内测，还额外有内容社区沉淀素材；同类功能做出来即被免费覆盖。</p>
  </div>
  <div class="card" style="margin:0">
    <h4 style="margin-top:0">③ 质量兜底成本随内容量线性增长</h4>
    <p class="small" style="margin-bottom:0">模型能力提升降低的是「生成」成本，不降低「验证」成本。每个实验的数值、单位、化学式、安全边界都要单独校。内容越多，人工越重，规模不经济。</p>
  </div>
</div>

<div class="callout warn">
<b>一个反直觉的推论：</b>正因为「验证」是成本，它才可能是壁垒。大厂愿意做生成、不愿意做逐地逐实验的评分点核对；而这件事恰恰是政策文件要求、学校必须执行、家长真正在意的。
</div>
""" % trs


def render_s1():
    lv_rows = "\n".join(
        "<tr><td>%s</td><td>%s</td><td>%s</td></tr>" % (badge(k), v, note)
        for k, v, note in [
            ("E1", LEVEL_LABEL["E1"], "可直接作为结论依据；引用条款号"),
            ("E2", LEVEL_LABEL["E2"], "仅作方向性依据，措辞需注明「据媒体报道」"),
            ("E3", LEVEL_LABEL["E3"], "只用于判断竞争态势与量级，不用于推算"),
            ("E4", LEVEL_LABEL["E4"], "企业自述/预测值，只作量级参照"),
        ])
    return """
<h2 id="s1"><span class="num">01</span>调研方法与证据分级</h2>

<h3>1.1 做了什么</h3>
<ul>
<li><b>检索</b>：联网检索 14 轮，覆盖政策文件、地方考试方案、竞品功能实测、行业经营数据、市场规模五类。</li>
<li><b>取样</b>：初筛 80 余条结果，人工剔除 SEO 文档站（豆丁、人人文库、360 文库等）与短视频聚合页，保留 13 条进入证据台账。</li>
<li><b>核验</b>：对 8 条关键来源抓取正文并留存 <code>URL + 抓取时间 + 正文 sha256</code>；另有 3 条因 JS 渲染或跳转下载仅取到页面框架，已在台账明确标注「仅检索摘要」。</li>
</ul>

<h3>1.2 证据分级与使用规则</h3>
<div class="tbl-scroll">
<table>
<caption>表 1-1　证据等级（正文中的标记与此一一对应）</caption>
<thead><tr><th>等级</th><th>含义</th><th>使用规则</th></tr></thead>
<tbody>%s</tbody>
</table>
</div>
<p class="small">区分「外部事实」与「本文判断」：带 <span class="tag">E1</span>—<span class="tag">E4</span> 编号的是外部事实，可点回附录 A 复核；
标 <span class="tag">本文判断</span> 的是基于事实的推论，允许被推翻。</p>

<h3>1.3 为什么本报告不做 TAM / SAM / SOM 测算</h3>
<div class="callout bad">
<b>因为拿不到可信分母。</b>检索到的「家庭教育支出」「AI 教育付费率」内容全部来自 SEO 文档站，无抽样方法、无口径、无原始数据；教育智能硬件的千亿规模是<b>预测值</b>且与「内容层」不可换算。
在这种基础上算 TAM，得到的是一位小数都不该信的假精确。本报告改用<b>付费意愿的前置验证</b>替代市场规模推算（见第 9 节）。
</div>

<h3>1.4 已知局限</h3>
<ul>
<li>腾讯「懂了鸭」仍在内测，功能与定价可能变化；本文引用的实测结论来自第三方评测，非官方文档。</li>
<li>河南等地的实验计分规则为媒体转述，未见省级原文件，结论强度弱于铜陵。</li>
<li>未做用户访谈（本轮只做桌面研究），因此「家长愿意付多少」在本文中<b>是待验证假设，不是结论</b>。</li>
</ul>
""" % lv_rows


def render_s2():
    tl = "\n".join(
        """<div class="tl-item">
  <div class="tl-date">%s　<span class="tag %s">%s</span>　%s</div>
  <div class="tl-title">%s</div>
  <p class="tl-body">%s</p>
</div>""" % (p["date"], TAG_CLASS.get(p["tag"], ""), p["tag"], ev_brief(p["ev"]), p["title"], p["body"])
        for p in DATA["policy"])
    return """
<h2 id="s2"><span class="num">02</span>需求侧：政策把实验变成了计分项</h2>

<p class="lead">这个赛道的需求不来自「家长想教」，而来自「考试要考」。政策链条从 2019 年走到 2026 年，已经从「要求开课」走到「按分计入录取总分」。这是本报告认为需求真实存在的<b>唯一硬依据</b>。</p>

<div class="timeline">%s</div>

<h3>2.1 计分带来的到底是什么需求</h3>
<p>铜陵的方案给出了最具体的形态：物理、化学各 10 分，<b>成绩全部计入中考录取总分</b>，考前随机抽题、每科 20 分钟、一人一桌独立操作。这类考试的特征决定了需求的性质：</p>
<div class="tbl-scroll">
<table>
<caption>表 2-1　考试形态 → 需求翻译</caption>
<thead><tr><th>考试特征</th><th>直接后果</th><th>家长/学生真正需要的东西</th></tr></thead>
<tbody>
<tr><td>随机抽题</td><td>不能只练「常考的那一个」</td><td>覆盖全部候选实验的<b>操作要点清单</b></td></tr>
<tr><td>限时 20 分钟、一人一桌</td><td>熟练度与步骤顺序决定得分</td><td><b>步骤级演练</b>与计时训练</td></tr>
<tr><td>按评分点给分</td><td>扣分点集中在细节（仪器选择、读数、收尾）</td><td><b>易错点对照</b>，而不是知识点讲解</td></tr>
<tr><td>成绩计入总分</td><td>家长愿意为此付费</td><td>可量化、可对比的<b>练习结果</b></td></tr>
</tbody>
</table>
</div>

<div class="callout">
<b>关键区分：</b>上表四行没有一行是「帮我生成内容」。它们要的是<b>覆盖度 + 步骤 + 易错点 + 结果反馈</b>。
这说明产品价值在「内容组织与校验」，不在「生成自由度」——这一点直接决定了第 7 节的定位选择。
</div>

<h3>2.2 需求存在，但已经被人免费满足了一部分</h3>
<p>AI 教育应用的月活规模说明「用 AI 学」这件事已被大规模接受：2025 年三季度整体月活 1.2 亿，同比增长 340%%（%s）。
但同一篇分析给出的另一半事实更关键：<b>没有一家跑通盈利闭环</b>（%s）。需求被验证了，付费没被验证。</p>
%s
<p class="chart-note">图 2-1　月活量级对比（单位：万）。三个数据点分别来自 2025Q3 与 2026Q1 的不同口径，只用于判断量级，<b>不可相加或相减</b>。</p>

<h3>2.3 一个必须承认的反证</h3>
<p>如果需求如此明确，为什么已经存在的产品没有出现「家长付费爆发」？目前能给出的解释有三条，且都指向同一个结论：</p>
<ol>
<li><b>免费替代品足够好</b>：豆包爱学等把讲题、批改做成免费入口（%s），家长没有付费动机。</li>
<li><b>真实动手不可替代</b>：政策强调「做中学」，虚拟内容只能做预习/复盘，价值被限定在辅助位（%s）。</li>
<li><b>家长无法评估质量</b>：看不懂内容对不对，就不敢为「内容」付钱，只肯为「结果」付钱（如提分、证书）。</li>
</ol>
<p>这三条把产品逼向一个方向：<b>卖可验证的结果，不卖生成能力。</b></p>
""" % (tl, EVIDENCE[8]["id"], EVIDENCE[8]["id"], render_chart_mau(), "E11", "E3")


def render_s3():
    rows = [
        ("通用内容生成平台", "腾讯「懂了鸭」（内测）",
         "亲子/教师/创作者三侧；奇妙卡可拖拽可模拟；内容社区 + 灵感墙 + 一键改编；微信/QQ 分享链路",
         "内容严谨性靠人工校验；互动模型对加载性能与设备有要求；仍在内测", "形态最接近原设想，正面撞车"),
        ("垂直学科工具", "飞象老师 3.0（2026-08-24）",
         "一句话生成可直接访问、可调 AI、可存数据的教育应用；已有化学学习工具样例",
         "重心在教师而非家长；生成物质量依赖提示词水平", "教师侧已被占位，需差异化"),
        ("虚拟实验厂商", "NOBOOK 虚拟实验",
         "理化生 + 小学科学仿真实验；单独有「实验加试」产品线；长期做 B/G 端",
         "以仿真为主，交互形态偏「软件」而非「轻页面」；C 端触达弱", "最接近「评分点对齐」的既有玩家"),
        ("流量型 AI 学习入口", "豆包爱学 / 快对 AI 等",
         "2026Q1 豆包爱学 MAU 1434.4 万；讲题、批改、搜题体验成熟；免费",
         "教研深度不足；不解决「动手操作」；免费策略压制付费空间", "获客上打不过，只能绕开"),
        ("硬件内嵌内容", "学而思学习机 / 有道",
         "教研背书强、内容自建、家长信任度高",
         "好未来营销费用率 30.9%、学习机为战略性亏损；有道硬件收入同比 -31.5%", "证明「内容+硬件」也不好赚钱"),
    ]
    trs = "\n".join(
        f"<tr><td><b>{a}</b></td><td>{b}</td><td>{c}</td><td>{d}</td><td class='small'>{e}</td></tr>"
        for a, b, c, d, e in rows)
    return f"""
<h2 id="s3"><span class="num">03</span>供给侧：谁已经在做，做到哪一步</h2>

<p class="lead">原设想最致命的不是「做不出来」，而是「已经有人做出来了，还免费」。2026 年 8—10 月这两个月里，两个直接相邻的形态先后落地：飞象老师 3.0（8 月 24 日）与腾讯「懂了鸭」（10 月内测）。</p>

<div class="tbl-scroll">
<table>
<caption>表 3-1　五类竞争者的强项、软肋与对我们的含义</caption>
<thead><tr><th>类别</th><th>代表</th><th>强在哪</th><th>软肋</th><th>对我们的含义</th></tr></thead>
<tbody>{trs}</tbody>
</table>
</div>
<p class="small">证据：{ev_brief('E7')} {ev_brief('E8')} {ev_brief('E10')} {ev_brief('E11')} {ev_brief('E9')}</p>

<h3>3.1 竞争矩阵：右上角是空的，但空不等于机会</h3>
{render_chart_comp()}
<p class="chart-note">图 3-1　横轴 = 生成自由度（越右越开放），纵轴 = 校验与可验证性（越上越可信），气泡大小 = 相对规模。
坐标为本文基于公开信息的判断，不是量化测评；<b>右上角（又自由又可信）目前无人占据</b>。</p>

<div class="callout warn">
<b>为什么右上角空着？</b>因为「自由」与「可信」在工程上互斥：允许任意生成，就无法对每一个输出做穷举校验。
谁声称两者兼得，谁就在某一边偷偷打折。我们的选择是<b>主动放弃自由度</b>，把信任做厚——这正是第 7 节推荐 B 类的理由。
</div>

<h3>3.2 一个容易被忽略的对手：仿真实验软件</h3>
<p>NOBOOK 这类厂商容易被当成「技术老旧」而忽略，但它有两个我们没有的优势：<b>已在教育系统内流通多年</b>，以及<b>已经单列「实验加试」产品线</b>。
这意味着「用软件练实验操作考试」这件事，不是新需求，是<b>存量市场</b>；我们要么做得更轻、更贴合地方评分点，要么就不该进去。</p>
"""


def render_s4():
    return """
<h2 id="s4"><span class="num">04</span>技术侧：Vibe Coding 能做什么、不能做什么</h2>

<p class="lead">Vibe Coding 降低的是「做一个能跑的页面」的门槛，没有降低「保证内容正确」的门槛。把这两件事混为一谈，是这类项目最常见的死法。</p>

<div class="grid2">
  <div class="card" style="margin:0">
    <h4 style="margin-top:0">能做的（已被验证）</h4>
    <ul class="small" style="margin-bottom:0">
      <li>一句话生成可交互页面：拖拽、参数调节、动画、测验（懂了鸭实测生成五子棋小游戏）</li>
      <li>把静态知识点转成操作序列与步骤提示</li>
      <li>生成初版文案、题干、选项与解析草稿</li>
      <li>批量套用模板，把同一实验适配到不同教材版本</li>
    </ul>
  </div>
  <div class="card" style="margin:0">
    <h4 style="margin-top:0">不能做的（必须外部兜底）</h4>
    <ul class="small" style="margin-bottom:0">
      <li><b>数值</b>：斜面摩擦、浓度配比、电学读数——算错一个数，整个实验作废</li>
      <li><b>单位与量纲</b>：mL / L、mol / g 混用是高频错误</li>
      <li><b>化学式与反应条件</b>：配平、条件、现象描述不能靠「看起来对」</li>
      <li><b>安全边界</b>：明火、强酸强碱、有毒气体——生成错了是人身风险</li>
    </ul>
  </div>
</div>

<h3>4.1 可行的技术路线：把生成关进笼子</h3>
<div class="tbl-scroll">
<table>
<caption>表 4-1　「受限生成」四层结构（对应 docs/02-技术构想.md）</caption>
<thead><tr><th>层</th><th>谁负责</th><th>产出</th><th>失败时怎么发现</th></tr></thead>
<tbody>
<tr><td>① 模板槽位</td><td>人（教研）</td><td>实验骨架：器材、步骤、评分点、易错点</td><td>结构校验：缺字段直接拒绝生成</td></tr>
<tr><td>② 数值与公式</td><td><b>脚本</b>（符号计算/常量表）</td><td>结果值、单位、有效数字</td><td>与教材例题对拍；量纲检查</td></tr>
<tr><td>③ 规则校验</td><td>规则引擎</td><td>正例通过 / 反例必须被拦</td><td>正反例成对回归，漏拦即失败</td></tr>
<tr><td>④ 人工签核</td><td>人（双人）</td><td>签核记录 + 版本号</td><td>错误可回滚，历史版本可追溯</td></tr>
</tbody>
</table>
</div>

<div class="callout ok">
<b>这条路线的好处：</b>模型能力越强，第 ① 步越快，成本越低；而第 ②③④ 步的成本是<b>可预算、可复用</b>的（同一模板适配新地市只改评分点映射）。
这正是「内容资产」相对于「生成能力」的商业价值所在。
</div>

<h3>4.2 成本估算：单个实验 7 小时（假设值）</h3>
<p>按生成 0.5 h + 规则 4 h + 素材 1 h + 复核 1.5 h 估算，单个实验首版约 <b>7 小时</b>人工；复核工时放大到 4 h 时约 <b>9.5 小时</b>。
这是内部排期用的假设，不是实测——第 9 节 H4 就是要把这个数测出来。</p>
"""


def render_s5():
    be = breakeven_table()
    be_rows = "\n".join(
        f"<tr><td class='num'>{r['review_h']}</td><td class='num'>{r['hours']}</td>"
        f"<td class='num'>{r['cost']:.1f}</td>"
        f"<td class='num'>{r['units'][0]}</td><td class='num'>{r['units'][1]}</td>"
        f"<td class='num'>{r['units'][2]}</td></tr>" for r in be)
    prices = " / ".join(f"{p:g} 元" for p in DATA["unit_econ"]["prices"])
    return f"""
<h2 id="s5"><span class="num">05</span>商业侧：1.2 亿月活与零家盈利</h2>

<p class="lead">这个赛道最值得记住的一组数字：<b>月活 1.2 亿、同比 +340%，同时没有一家跑通盈利闭环</b>。它说明「用 AI 学」已被大规模接受，但「为 AI 学付钱」尚未被任何一家验证。</p>

<div class="tbl-scroll">
<table>
<caption>表 5-1　四类玩家的经营信号（数据来自公司财报，经媒体汇总）</caption>
<thead><tr><th>公司</th><th>关键数字</th><th>说明什么</th></tr></thead>
<tbody>
<tr><td>好未来</td><td>净收入 8.61 亿美元（+39.1%）；销售与营销费用 1.777 亿美元，占收入 <b>30.9%</b>；学习机被定性为「战略性亏损」</td><td>增长靠投放买来的；硬件本身不赚钱</td></tr>
<tr><td>科大讯飞</td><td>智慧教育收入 34.90 亿元（-1.16%）；扣非净利 -6.37 亿元；批阅机覆盖 5000+ 校、<b>续购率 >90%</b></td><td>C 端教育没起来，<b>B 端续购真实存在</b></td></tr>
<tr><td>网易有道</td><td>连续 8 季经营利润为正；AI 订阅销售额约 1 亿元（+20%）；智能设备收入 -31.5%</td><td>唯一稳定盈利者，但规模天花板明显</td></tr>
<tr><td>字节 / 阿里</td><td>豆包 2026-06 MAU 3.82 亿；豆包爱学 2026Q1 MAU 1434.4 万，大部分功能免费</td><td>教育是流量场景，不是利润中心</td></tr>
</tbody>
</table>
</div>
<p class="small">证据：{ev_brief('E9')} {ev_brief('E11')}</p>

<div class="callout bad">
<b>对原设想的直接含义：</b>连「有教研积累 + 有硬件载体 + 有品牌」的公司，都在用 30% 的收入买流量、并把学习机做成战略性亏损。
一个没有分发、没有品牌、没有内容存量的新项目，去做「面向家长的付费内容工具」，等于<b>在最难的战场用最弱的兵</b>。
</div>

<h3>5.1 单位经济：内容层真正的成本在哪</h3>
<p>下表把「一个实验从生成到可交付」拆成工时，并按三档定价算回本所需销量。<b>全部为内部假设</b>（工时估值 {DATA['unit_econ']['hourly']} 元/小时），只用于判断「这条路能不能规模化」，不构成定价建议。</p>
<div class="tbl-scroll">
<table>
<caption>表 5-2　单实验首版成本与回本销量（售价：{prices}）</caption>
<thead><tr><th class="num">复核工时 h</th><th class="num">总工时 h</th><th class="num">成本 元</th>
<th class="num">9.9 元需销量</th><th class="num">19.9 元需销量</th><th class="num">49 元需销量</th></tr></thead>
<tbody>{be_rows}</tbody>
</table>
</div>
{render_chart_breakeven()}
<p class="chart-note">图 5-1　不同复核工时下，按三档定价回收单实验成本所需的销量。
注意：这是<b>首版</b>成本，不含获客、退款、客服与版本迭代。</p>

<div class="callout">
<b>结论：</b>「一份内容只卖给一个家庭」在数学上就不成立——回本销量对内容复杂度极其敏感，而售价上不去。
要让模型成立，只有两条路：<b>同一份内容多渠道复用</b>（家长 / 教师 / 机构 / 学校），或<b>把内容做成可授权的资产</b>而不是一次性服务。
</div>

<h3>5.2 所以商业模式应该长什么样</h3>
<ol>
<li><b>先 B 后 C</b>：用教师与学校的采购验证内容价值（有续购证据），再用「教师推荐」降低 C 端获客成本。</li>
<li><b>按地市授权，而不是按份卖</b>：评分点对齐的成本主要花在「某地某年某考试方案」，这份成本可以卖给该地所有学校。</li>
<li><b>不做订阅制内容库</b>：内容库意味着持续生产，而续费率未经验证；先做「考试季单品」，交付明确、可结案。</li>
</ol>
"""


def render_s6():
    return f"""
<h2 id="s6"><span class="num">06</span>合规侧：四条不能碰的线</h2>

<p class="lead">这个项目的合规不是「上线前补个协议」，而是<b>会直接改写产品形态</b>。四条线里，有两条会否掉原设想的一部分功能。</p>

<div class="tbl-scroll">
<table>
<caption>表 6-1　四类硬约束、对应动作与后果</caption>
<thead><tr><th>约束</th><th>要求要点</th><th>我们要做的</th><th>不做会怎样</th></tr></thead>
<tbody>
<tr><td><b>生成内容标识</b><br>{ev_brief('E4')}</td>
<td>生成内容须有显式标识；下载、复制、导出时文件里也要有；隐式标识写入元数据</td>
<td>页面固定「AI 辅助生成」角标；导出文件写入元数据与水印；用户协议写明标识义务</td>
<td>应用分发环节被要求补材料；内容被传播后无法自证来源</td></tr>
<tr><td><b>中小学生成式 AI 使用</b><br>{ev_brief('E5')}</td>
<td>禁止学生直接复制 AI 生成内容作为作业或考试答案；严禁输入试题与个人身份信息；学校建白名单</td>
<td>产物定位为<b>演练与自检</b>，不产出「可直接提交的作业」；不接收试题上传；不做学生身份信息采集</td>
<td>被认定为「代做作业」工具，进不了校园，也无法与学校合作</td></tr>
<tr><td><b>双减边界</b><br>{ev_brief('E2')}</td>
<td>非学科机构不得从事学科培训；线上不得传播「拍照搜题」等惰化思维的方法；学科类收费受政府指导价管理</td>
<td>不叫「培训」「辅导」；不做「拍照出答案」；收费定性为内容/工具授权，不按课时收费</td>
<td>被划入学科类培训，直接触碰资质与收费监管</td></tr>
<tr><td><b>实验安全</b><br>{ev_brief('E1')}</td>
<td>实验教学须落实安全管理制度与预案；危险化学品采购、储存、使用、回收有专门办法</td>
<td>所有实验标注风险等级；涉及明火/强酸强碱/有毒气体的，只做「演示与讲解」，不引导家庭复现</td>
<td>一旦发生家庭实验事故，产品方难辞其咎</td></tr>
</tbody>
</table>
</div>

<div class="callout bad">
<b>两条会否掉功能的约束，必须写进产品定义：</b>
<br>① <b>不能做「拍照搜题式」的实验答案直出</b>——这既是双减明令禁止的方法，也会把产品变成「作业代做工具」，与使用指南冲突。
<br>② <b>不能把生成物做成「可直接交的作业」</b>——产物必须是练习、自检、复盘，且带 AI 标识。
</div>

<h3>6.1 数据最小化：一条自我约束</h3>
<ul>
<li>不采集学生姓名、学校、班级、人像；家庭场景只保留家长账号。</li>
<li>不做「能力画像」类功能——画像需要长期行为数据，与最小化原则冲突，且一旦泄露后果不可逆。</li>
<li>练习记录默认本地留存，云端只存聚合计数。</li>
</ul>
"""









CHARTS = []


def chart_div(cid, label, option):
    CHARTS.append({"id": cid, "option": option})
    return '<div id="%s" class="chart" role="img" aria-label="%s"></div>' % (cid, label)


def render_chart_mau():
    items = [{"name": m["name"] + "（" + m["period"] + "）", "value": m["value"], "disp": m["disp"]}
             for m in DATA["mau"]]
    option = {
        "grid": {"left": 8, "right": 84, "top": 16, "bottom": 8, "containLabel": True},
        "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
        "xAxis": {"type": "value", "name": "月活（万）", "nameTextStyle": {"color": "#6b7480"},
                  "splitLine": {"lineStyle": {"color": "#eef1f4"}},
                  "axisLabel": {"color": "#6b7480"}},
        "yAxis": {"type": "category", "data": [i["name"] for i in items],
                  "axisLine": {"show": False}, "axisTick": {"show": False},
                  "axisLabel": {"color": "#3c4450", "fontSize": 12}},
        "series": [{
            "type": "bar", "barWidth": "52%",
            "data": [{"value": i["value"],
                      "label": {"show": True, "position": "right", "formatter": i["disp"],
                                "color": "#15181d", "fontSize": 12},
                      "itemStyle": {"color": "#0f6b5f" if i["value"] > 2000 else "#59a89b",
                                    "borderRadius": [0, 6, 6, 0]}} for i in items],
        }],
    }
    return chart_div("chart-mau", "AI 教育应用月活量级对比", option)


def render_chart_comp():
    pts = []
    for c in DATA["competitors"]:
        mine = c["ev"] == "—"
        pts.append({
            "name": c["name"], "value": [c["x"], c["y"], c["size"]],
            "symbolSize": 14 + c["size"] * 6,
            "itemStyle": {"color": "#c2410c" if mine else "#0f6b5f",
                          "opacity": 0.85, "borderColor": "#fff", "borderWidth": 1.5},
            "label": {"show": True, "position": "right", "formatter": c["name"],
                      "fontSize": 11, "color": "#3c4450",
                      "fontWeight": "bold" if mine else "normal"},
        })
    option = {
        "grid": {"left": 12, "right": 140, "top": 28, "bottom": 40, "containLabel": True},
        "tooltip": {"formatter": "{b}", "trigger": "item"},
        "xAxis": {"min": 0, "max": 10, "name": "生成自由度 →", "nameLocation": "middle",
                  "nameGap": 28, "nameTextStyle": {"color": "#6b7480", "fontSize": 12},
                  "splitLine": {"lineStyle": {"color": "#eef1f4"}},
                  "axisLabel": {"color": "#98a1ac"}},
        "yAxis": {"min": 0, "max": 10, "name": "校验与可验证性 →", "nameLocation": "middle",
                  "nameGap": 40, "nameTextStyle": {"color": "#6b7480", "fontSize": 12},
                  "splitLine": {"lineStyle": {"color": "#eef1f4"}},
                  "axisLabel": {"color": "#98a1ac"}},
        "series": [{"type": "scatter", "data": pts}],
    }
    return chart_div("chart-comp", "竞争矩阵：生成自由度与可验证性", option)


def render_chart_pos():
    rows = weighted_scores()
    option = {
        "grid": {"left": 8, "right": 60, "top": 16, "bottom": 8, "containLabel": True},
        "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
        "xAxis": {"type": "value", "min": 0, "max": 5, "name": "加权总分",
                  "splitLine": {"lineStyle": {"color": "#eef1f4"}},
                  "axisLabel": {"color": "#6b7480"}},
        "yAxis": {"type": "category", "data": [r["id"] + "　" + r["name"] for r in rows],
                  "axisLine": {"show": False}, "axisTick": {"show": False},
                  "axisLabel": {"color": "#3c4450", "fontSize": 12}},
        "series": [{
            "type": "bar", "barWidth": "50%",
            "data": [{"value": r["total"],
                      "itemStyle": {"color": "#0f6b5f" if r["id"] in ("B", "C") else "#b9c2cb",
                                    "borderRadius": [0, 6, 6, 0]}} for r in rows],
            "label": {"show": True, "position": "right", "formatter": "{c}", "color": "#15181d"},
        }],
    }
    return chart_div("chart-pos", "四个定位候选的加权评分", option)


def render_chart_breakeven():
    prices = DATA["unit_econ"]["prices"]
    hs = DATA["unit_econ"]["review_hs"]
    colors = ["#0f6b5f", "#59a89b", "#c2410c"]
    series = []
    for idx, p in enumerate(prices):
        series.append({
            "name": "%g 元/份" % p, "type": "line",
            "symbolSize": 7,
            "itemStyle": {"color": colors[idx % len(colors)]},
            "data": [breakeven_units(h, p) for h in hs],
            "label": {"show": True, "position": "top", "color": "#3c4450", "fontSize": 11},
        })
    option = {
        "grid": {"left": 12, "right": 24, "top": 48, "bottom": 16, "containLabel": True},
        "tooltip": {"trigger": "axis"},
        "legend": {"top": 6, "textStyle": {"color": "#3c4450", "fontSize": 12},
                   "itemWidth": 14, "itemHeight": 8},
        "xAxis": {"type": "category", "data": [str(h) + " h" for h in hs],
                  "name": "人工复核工时", "nameGap": 26,
                  "nameTextStyle": {"color": "#6b7480"},
                  "axisLabel": {"color": "#6b7480"}},
        "yAxis": {"type": "value", "name": "回本所需份数",
                  "nameTextStyle": {"color": "#6b7480"},
                  "splitLine": {"lineStyle": {"color": "#eef1f4"}},
                  "axisLabel": {"color": "#6b7480"}},
        "series": series,
    }
    return chart_div("chart-breakeven", "单实验回本销量敏感性", option)



def render_s7():
    rows = weighted_scores()
    trs = "\n".join(
        f"<tr><td><b>{r['id']}</b></td><td>{r['name']}</td>"
        f"<td class='num'><b>{r['total']:.2f}</b></td>"
        f"<td>{r['verdict']}</td><td class='small'>{r['why']}</td></tr>"
        for r in rows)
    w = "、".join(f"{x['label']} {int(x['w']*100)}%" for x in DATA["weights"])
    t = {r["id"]: r["total"] for r in rows}
    return f"""
<h2 id="s7"><span class="num">07</span>定位建议：四个候选与加权评分</h2>

<p class="lead">把「做什么」拆成四个可选定位，用同一套权重打分。<b>结论是别做 A（原设想），先做 B（楔子），用 C（渠道）放量，D（白盒校验）留作终局。</b></p>

<h3>7.1 评分口径</h3>
<p class="small">权重：{w}。每项 1—5 分，由本文基于第 2—6 节的事实给出，属<b>判断</b>而非测量；换一套权重排序可能变化，因此表中同时给出理由，便于被推翻。</p>

<div class="tbl-scroll">
<table>
<caption>表 7-1　四个定位候选的评分与理由（按加权总分升序）</caption>
<thead><tr><th>编号</th><th>定位</th><th class="num">加权总分</th><th>结论</th><th>理由</th></tr></thead>
<tbody>{trs}</tbody>
</table>
</div>
{render_chart_pos()}
<p class="chart-note">图 7-1　加权总分。绿色为推荐推进项（B、C），灰色为不建议 / 备选（A、D）。满分 5 分。</p>

<div class="callout warn">
<b>读表须知（否则会认为结论自相矛盾）：</b>C 的加权分（{t['C']:.2f}）高于 B（{t['B']:.2f}），原因是「付费证据」一项 C 更强。
之所以仍把 <b>B 放在前面做</b>，有两个理由：① C 的功能面正对飞象老师 3.0，且教师端采购周期长、需要资质与信任；
② B 产出的评分点对齐内容，恰好是 C 的输入——先做 B 不会让 C 白等，反过来则不成立。
一句话：<b>用 C 的付费逻辑，做 B 的内容。</b>
</div>

<h3>7.2 为什么 A 必须被否掉</h3>
<div class="callout bad">
<b>A（家长自助生成器）在「竞争空间」上只拿到 1 分，这不是保守估计，是事实约束：</b>
腾讯「懂了鸭」已经把「一句话生成 + 可拖拽模拟 + 社区 + 改编」做完并在内测，且面向亲子场景；
飞象老师 3.0 已经把「一句话生成教育应用」做成产品并在教师侧铺开。
在这条路上我们唯一能提供的差异是「更懂某一个地市的实验考试」——而这恰好是 B 的定位，不是 A 的。
</div>

<h3>7.3 推荐的三层结构</h3>
<div class="grid3">
  <div class="card" style="margin:0;border-top:3px solid #0f6b5f">
    <h4 style="margin-top:0">楔子 · B</h4>
    <p class="small" style="margin-bottom:0"><b>中考实验操作「评分点对齐」微练习</b><br>
    先做铜陵一地、3 个高频实验。卖点只有一句：<b>每个步骤都对得上评分点</b>。</p>
  </div>
  <div class="card" style="margin:0;border-top:3px solid #59a89b">
    <h4 style="margin-top:0">渠道 · C</h4>
    <p class="small" style="margin-bottom:0"><b>教师端「章节实验 30 分钟改造」</b><br>
    同一个内容资产换个入口给教师。教师带来信任与 B 端采购，也带来真实易错点。</p>
  </div>
  <div class="card" style="margin:0;border-top:3px solid #b9c2cb">
    <h4 style="margin-top:0">终局 · D</h4>
    <p class="small" style="margin-bottom:0"><b>校验层白标</b><br>
    把「实验内容正确性校验」做成服务，卖给正在做生成器的公司。<b>等有了错误样本库再谈。</b></p>
  </div>
</div>
"""



def render_s8():
    return """
<h2 id="s8"><span class="num">08</span>推荐方案：内容资产 + 两个出口</h2>

<div class="card" style="border-left:4px solid #0f6b5f">
<h3 style="margin-top:0">定位陈述（可直接作为对外口径）</h3>
<p style="margin-bottom:0">我们不做「让家长自己生成实验内容」的工具。我们做<b>与地方实验操作考试评分点逐条对齐的轻量实验演练内容</b>：
一页一个实验，可离线打开，按步骤走、按评分点自检，每个结论都能溯源到教材与考试方案。</p>
</div>

<h3>8.1 产品边界：写清楚「不做什么」比「做什么」更重要</h3>
<div class="grid2">
  <div class="card" style="margin:0">
    <h4 style="margin-top:0;color:#0f6b5f">做</h4>
    <ul class="small" style="margin-bottom:0">
      <li>按地市考试方案逐条映射的<b>步骤演练</b>（铜陵 → 河南 → 其他）</li>
      <li>评分点自检清单 + 高频扣分点对照</li>
      <li>教师端「教材章节 → 一页交互」的模板化改造</li>
      <li>每个实验的<b>依据来源 + 版本 + 复核记录</b></li>
      <li>离线可用（单文件 HTML，不依赖网络）</li>
    </ul>
  </div>
  <div class="card" style="margin:0">
    <h4 style="margin-top:0;color:#b91c1c">不做</h4>
    <ul class="small" style="margin-bottom:0">
      <li>任意实验的自由生成（无法穷举校验）</li>
      <li>拍照搜题 / 答案直出（双减明令禁止的方法）</li>
      <li>可直接提交的作业（与使用指南冲突）</li>
      <li>学生身份信息与能力画像采集</li>
      <li>涉及明火/强酸强碱/有毒气体的家庭复现引导</li>
    </ul>
  </div>
</div>

<h3>8.2 最小可行产品：3 个实验、1 个地市、1 个渠道</h3>
<div class="tbl-scroll">
<table>
<caption>表 8-1　MVP 范围（刻意做小，目的是拿到验证数据而不是上线）</caption>
<thead><tr><th>项</th><th>范围</th><th>为什么是这个范围</th><th>验收标准</th></tr></thead>
<tbody>
<tr><td>地市</td><td>铜陵</td><td>唯一拿到<b>一手</b>考试方案（物理、化学各 10 分，全额计入总分）</td><td>10 个候选实验的评分点表落地</td></tr>
<tr><td>实验数</td><td>3 个</td><td>覆盖「力学 / 电学 / 化学基本操作」三类，能测出模板复用率</td><td>每个实验 0 科学性错误、规则覆盖 ≥90%</td></tr>
<tr><td>形态</td><td>单文件 HTML</td><td>教师可直接投屏、家长可微信转发；无部署成本</td><td>手机与教室大屏均可读，离线可用</td></tr>
<tr><td>渠道</td><td>8 位教师 + 20 位家长</td><td>只做能面对面拿到反馈的人，不投广告</td><td>见第 9 节 H1 / H2 门槛</td></tr>
</tbody>
</table>
</div>

<h3>8.3 收入结构（假设，待验证）</h3>
<ul>
<li><b>家长侧</b>：按「考试季单品」卖，不卖年费。定价区间 29—49 元/地市包（<b>待验证</b>，见第 9 节 H1）。</li>
<li><b>教师/学校侧</b>：按地市或按校授权，含更新服务。定价<b>不做假设</b>，用真实询价替代。</li>
<li><b>机构侧（后期）</b>：内容授权 + 白标，按年授权，不参与其招生分成（避免被认定为学科培训链条）。</li>
</ul>
<div class="callout warn">
<b>为什么不给学校定价：</b>本报告没有拿到任何可信的教育软件采购单价数据。编一个「3000—8000 元/校」看起来专业，实则污染决策。
正确做法是在 H2 访谈里直接问「你们去年买过什么，多少钱」，用真实成交价替代假设。
</div>
"""


def render_s9():
    trs = "\n".join(
        f"<tr><td><b>{h['id']}</b></td><td>{h['name']}</td><td class='small'>{h['method']}</td>"
        f"<td>{h['gate']}</td><td class='small'>{h['kill']}</td></tr>"
        for h in DATA["hypotheses"])
    return f"""
<h2 id="s9"><span class="num">09</span>验证计划：五个假设与 Kill 条件</h2>

<p class="lead">这一节是本报告唯一要求「照着做」的部分。<b>每个假设都必须能在一周内被证伪</b>，否则就是假装验证。</p>

<div class="tbl-scroll">
<table>
<caption>表 9-1　五个待验证假设：验证方式、通过门槛与 Kill 条件</caption>
<thead><tr><th>编号</th><th>假设</th><th>怎么验</th><th>通过门槛</th><th>Kill 条件</th></tr></thead>
<tbody>{trs}</tbody>
</table>
</div>

<h3>9.1 决策门（Decision Gate）</h3>
<div class="tbl-scroll">
<table>
<caption>表 9-2　四种结果对应的动作，事先写死，避免事后找理由</caption>
<thead><tr><th>结果组合</th><th>动作</th><th>理由</th></tr></thead>
<tbody>
<tr><td>H1 与 H2 均通过，H3 通过</td><td><span class="pill go">推进</span> 做 10 个实验的铜陵包</td><td>需求与质量双达标，可进入内容生产</td></tr>
<tr><td>H2 通过、H1 不通过</td><td><span class="pill mid">收窄</span> 只做教师/B 端</td><td>付费在 B 端，C 端不碰</td></tr>
<tr><td>H1 通过、H2 不通过</td><td><span class="pill mid">收窄</span> 只做家长考试单品</td><td>单点可做，但不做平台</td></tr>
<tr><td>H1 与 H2 均不通过</td><td><span class="pill no">停止</span> 转 D 类白标或放弃</td><td>没有人为内容付费，产品不成立</td></tr>
<tr><td>H3 不通过（出现无法拦截的错误）</td><td><span class="pill no">停止</span> 不论其他结果</td><td>在未成年人 + 实验场景，内容错误的代价不可承受</td></tr>
</tbody>
</table>
</div>

<div class="callout bad">
<b>一票否决项：</b>H3 是唯一的一票否决。任何一条「无法被规则拦截的科学性或安全性错误」，都足以终止项目——
这不是谨慎，是这个场景的底线（参照 `.clinerules/01-内容准确性与合规红线.md`）。
</div>

<h3>9.2 四周排期</h3>
<div class="tbl-scroll">
<table>
<caption>表 9-3　4 周验证排期（第二周起并行，不串行等待）</caption>
<thead><tr><th>周</th><th>主要动作</th><th>产出</th></tr></thead>
<tbody>
<tr><td>第 1 周</td><td>铜陵评分点表；3 个实验的模板与数值脚本</td><td>评分点映射表 + 校验规则初版</td></tr>
<tr><td>第 2 周</td><td>做出 3 个单文件样本；双人复核；记录工时（H3 / H4）</td><td>3 份可交付样本 + 工时记录</td></tr>
<tr><td>第 3 周</td><td>8 位教师试用（H2）；20 位家长看 demo 并报价（H1）</td><td>访谈记录 + 报价分布</td></tr>
<tr><td>第 4 周</td><td>按决策门出结论；更新 README 与 docs/01</td><td>继续 / 收窄 / 停止 的书面结论</td></tr>
</tbody>
</table>
</div>
<p class="small">与 <code>docs/01-验证计划.md</code> 的关系：本节把该文档的定性描述变成可判定的门槛；执行时以本节为准，回收后回写 docs/01 的进度勾选。</p>
"""


def render_s10():
    trs = "\n".join(
        f"<tr><td>{r['name']}</td><td class='num'>{r['p']}</td><td class='num'>{r['i']}</td>"
        f"<td class='num'>{r['p'] * r['i']}</td><td class='small'>{r['mitigation']}</td></tr>"
        for r in sorted(DATA["risks"], key=lambda x: -x["p"] * x["i"]))
    return f"""
<h2 id="s10"><span class="num">10</span>风险与对冲</h2>
<p>概率与影响各按 1—5 打分，乘积用于排序。<b>打分是本文判断</b>，用于决定先处理哪一个，不代表精确计量。</p>
<div class="tbl-scroll">
<table>
<caption>表 10-1　风险清单（按 概率 × 影响 降序）</caption>
<thead><tr><th>风险</th><th class="num">概率</th><th class="num">影响</th><th class="num">P×I</th><th>对冲动作</th></tr></thead>
<tbody>{trs}</tbody>
</table>
</div>

<div class="callout">
<b>最该先处理的是第一条（大厂免费覆盖），而且它无法被「做得更好」解决。</b>
唯一的解法是换维度竞争：不比生成自由度，比「这个地市今年这张评分表」的对齐精度。
这也是为什么第 8 节把范围压到「1 个地市、3 个实验」——先把一个点做到别人懒得做，再谈复制。
</div>

<div class="callout warn">
<b>一个自我提醒：</b>「评分点对齐」是可被复制的优势，不是护城河。它能撑住前 12 个月，撑不住 3 年。
真正的长期资产是<b>错误样本库 + 复核记录 + 与教研体系的信任关系</b>——这三样都只能靠时间攒。
</div>
"""


def render_s11():
    return """
<h2 id="s11"><span class="num">11</span>结论与给决策者的三句话</h2>

<div class="grid3">
  <div class="card" style="margin:0">
    <h3 style="margin-top:0;font-size:16px">① 需求是真的，但不在「生成」上</h3>
    <p class="small" style="margin-bottom:0">实验操作已按分计入中考，家长会为「孩子做对、不扣分」付钱；不会为「自己造课件」付钱。</p>
  </div>
  <div class="card" style="margin:0">
    <h3 style="margin-top:0;font-size:16px">② 位置已经有人站了，别正面挤</h3>
    <p class="small" style="margin-bottom:0">腾讯懂了鸭、飞象 3.0、NOBOOK 分别占据了「自由生成」「教师生成」「仿真加试」，且前两个免费或低价。</p>
  </div>
  <div class="card" style="margin:0">
    <h3 style="margin-top:0;font-size:16px">③ 能赢的只有「可信」这一件事</h3>
    <p class="small" style="margin-bottom:0">把生成关进笼子，把评分点对齐、把错误拦在发布前——这件事大厂不愿意做，也做不细。</p>
  </div>
</div>

<h3>11.1 建议的下一步（按顺序，不要跳）</h3>
<ol>
<li><b>本周</b>：把铜陵 10 个候选实验的评分点表做出来（纯文档，不写代码）。做不出来，说明「对齐」这件事本身不成立。</li>
<li><b>两周内</b>：做出 3 个单文件样本，跑 H3 / H4。样本拿给教师看，先看他们会不会用，再谈愿不愿买。</li>
<li><b>四周内</b>：完成 H1 / H2 的访谈与报价，按第 9 节的决策门出书面结论。</li>
</ol>

<h3>11.2 什么情况下应该直接放弃</h3>
<ul>
<li>评分点表做不出来（说明地方方案不够细，或我们拿不到）</li>
<li>3 个样本里出现 1 处无法被规则拦截的科学性错误（H3 一票否决）</li>
<li>8 位教师中 ≤1 位愿意在下节课用（说明「教师需要」这个前提是错的）</li>
</ul>

<div class="callout ok">
<b>最后一句：</b>这个项目的价值不在「用 AI 生成实验内容」——那件事 2026 年已经白菜化；
价值在于<b>敢对内容正确性负责</b>。如果做不到这一点，这个项目没有存在的必要。
</div>
"""


def render_appendix_a():
    rows = []
    for e in EVIDENCE:
        sha = e["sha256"]
        sha_html = f"<code>{sha}</code>" if sha != "—" else '<span class="small">—</span>'
        rows.append(f"""
<tr id="ev-{e['id']}">
  <td>{badge(e['level'])}<br><b>{e['id']}</b></td>
  <td><b>{e['title']}</b><br><span class="small">{e['publisher']}　{e['date']}</span></td>
  <td class="small">{e['point']}</td>
  <td class="small"><a href="{e['url']}" rel="noopener noreferrer nofollow" target="_blank">{e['url']}</a></td>
  <td class="small">{e['fetched']}<br>sha256 {sha_html}</td>
</tr>""")
    return f"""
<h2 id="sA"><span class="num">A</span>附录 A　证据台账</h2>
<p>共 {len(EVIDENCE)} 条。sha256 为<b>正文前 16 位</b>，用于校验抓取内容未被改写；标注「仅检索摘要」的条目未取正文，因此无 sha256。
链接可能随站点改版失效，以抓取时间与 sha256 为准。</p>
<div class="tbl-scroll">
<table>
<caption>表 A-1　证据台账（点击编号可在正文间跳转，点击 URL 打开原始页面）</caption>
<thead><tr><th>等级 / 编号</th><th>标题与出处</th><th>与本报告相关的事实</th><th>URL</th><th>抓取时间 / 指纹</th></tr></thead>
<tbody>{''.join(rows)}</tbody>
</table>
</div>
<p class="small">证据等级分布：E1 × {sum(1 for e in EVIDENCE if e['level'] == 'E1')}、
E2 × {sum(1 for e in EVIDENCE if e['level'] == 'E2')}、
E3 × {sum(1 for e in EVIDENCE if e['level'] == 'E3')}、
E4 × {sum(1 for e in EVIDENCE if e['level'] == 'E4')}。</p>
"""


def render_appendix_b():
    gap_rows = "\n".join(
        f"<tr><td>{g['item']}</td><td><b>{g['status']}</b></td><td class='small'>{g['why']}</td></tr>"
        for g in DATA["gaps"])
    return f"""
<h2 id="sB"><span class="num">B</span>附录 B　数据缺口、方法局限与版本</h2>

<h3>B.1 数据缺口（明确列出，不填估算）</h3>
<div class="tbl-scroll">
<table>
<caption>表 B-1　本次调研未能取得的数据</caption>
<thead><tr><th>缺口</th><th>状态</th><th>为什么没有采用替代数据</th></tr></thead>
<tbody>{gap_rows}</tbody>
</table>
</div>

<h3>B.2 方法局限</h3>
<ul>
<li><b>只有桌面研究，没有一手访谈。</b>因此「家长愿付多少」「教师会不会用」在本文中全部是假设，第 9 节即为补这个缺口而设。</li>
<li><b>竞品未做功能实测。</b>懂了鸭仍在内测、飞象 3.0 未亲自跑通，判断依据是第三方评测与官方宣传，可能高估其成熟度。</li>
<li><b>评分是主观的。</b>第 7 节的 1—5 分、第 10 节的概率/影响，均为本文判断；已给出理由，便于他人用同一框架推翻。</li>
<li><b>地域样本极小。</b>政策落地只核到铜陵一地的一手方案，河南为媒体转述，不能代表全国。</li>
</ul>

<h3>B.3 版本历史</h3>
<div class="tbl-scroll">
<table>
<caption>表 B-2　版本记录</caption>
<thead><tr><th>版本</th><th>日期</th><th>变更</th></tr></thead>
<tbody>
<tr><td><b>v1.0</b></td><td><b>{META['date']}</b></td><td><b>首版：完成政策、竞争、技术、商业、合规五个维度的取证与定位建议</b></td></tr>
</tbody>
</table>
</div>

<h3>B.4 可复现性</h3>
<p class="small">本页由 <code>工具/生成调研报告.py</code> 生成，数据全部来自该文件的 <code>EVIDENCE</code> 与 <code>DATA</code> 常量。
重跑命令：<code>python -B 工具/生成调研报告.py</code>。改口径请改常量后重跑，<b>不要手改本文件</b>——手改会在下次生成时被覆盖。</p>
"""





def build_html():
    """拼装整页。每次调用前清空图表注册表，保证多次调用结果一致。"""
    CHARTS.clear()
    sections = [
        render_s0(), render_s1(), render_s2(), render_s3(), render_s4(),
        render_s5(), render_s6(), render_s7(), render_s8(), render_s9(),
        render_s10(), render_s11(), render_appendix_a(), render_appendix_b(),
    ]
    body = "\n".join(sections)
    charts_json = json.dumps(CHARTS, ensure_ascii=False).replace("</", "<\\/")
    footer = """
<footer>
  <p><b>%s</b> · %s · 版本 %s · 取证截止 %s 05:00（UTC+8）</p>
  <p>本页由 <code>工具/生成调研报告.py</code> 从 <code>EVIDENCE</code> / <code>DATA</code> 常量生成，请勿手改。
  数字口径与证据等级见附录 A、B。图表库同目录 <code>assets/echarts.min.js</code>，不依赖外网 CDN。</p>
  <p>%s。文中「本文判断」为推论，可能被证伪；对外引用请以原始来源为准。</p>
</footer>""" % (META["title"], META["author"], META["version"], META["date"], META["scope"])
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{META['title']}｜{META['version']}</title>
<meta name="description" content="K12 实验内容工具的可行性调研与定位建议：政策、竞争、技术、商业、合规五维取证，给出「有条件推进」的结论与 4 周验证计划。">
<meta name="author" content="{META['author']}">
<meta name="color-scheme" content="light">
<style>{CSS}</style>
</head>
<body>
{render_hero()}
<main class="wrap">
{render_toc()}
{body}
{footer}
</main>
<script src="{ECHARTS_REL}"></script>
<script>
(function () {{
  var charts = {charts_json};
  function boot() {{
    if (typeof echarts === "undefined") {{
      var nodes = document.querySelectorAll(".chart");
      for (var i = 0; i < nodes.length; i++) {{
        nodes[i].style.height = "auto";
        nodes[i].innerHTML = '<div style="padding:24px;color:#6b7480;font-size:13px">'
          + '图表库未加载（缺少 assets/echarts.min.js）。本页所有图表对应的数值均在前文表格中给出。'
          + '</div>';
      }}
      return;
    }}
    for (var j = 0; j < charts.length; j++) {{
      var dom = document.getElementById(charts[j].id);
      if (!dom) continue;
      var ins = echarts.init(dom, null, {{ renderer: "canvas" }});
      ins.setOption(charts[j].option);
      window.addEventListener("resize", function (chart) {{
        return function () {{ chart.resize(); }};
      }}(ins));
    }}
  }}
  if (document.readyState === "loading") {{
    document.addEventListener("DOMContentLoaded", boot);
  }} else {{
    boot();
  }}
}})();
</script>
</body>
</html>
"""


def write_if_changed(path, text):
    """内容一致就不落盘，避免无意义的 mtime / diff 变化。"""
    data = text.encode("utf-8")
    if os.path.exists(path):
        with open(path, "rb") as f:
            if f.read() == data:
                return False
    folder = os.path.dirname(path)
    if folder and not os.path.isdir(folder):
        os.makedirs(folder)
    with open(path, "wb") as f:
        f.write(data)
    return True


def main(argv):
    errs = verify_data()
    if errs:
        print("[FAIL] 数据自检未通过，未生成文件：")
        for e in errs:
            print("  - " + e)
        return 1
    html = build_html()
    size = len(html.encode("utf-8"))
    if "--检查" in argv:
        print("[OK] 数据自检通过：证据 %d 条，图表 %d 个，HTML %d 字节（未写盘）"
              % (len(EVIDENCE), len(CHARTS), size))
        return 0
    changed = write_if_changed(OUT_PATH, html)
    print("[OK] %s %s" % ("已生成" if changed else "内容未变，跳过", OUT_PATH))
    print("     证据 %d 条 / 图表 %d 个 / %d 字节" % (len(EVIDENCE), len(CHARTS), size))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
