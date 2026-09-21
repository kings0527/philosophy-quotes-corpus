# -*- coding: utf-8 -*-
"""
把语料库当作测量工具来检验（心理测量学式信度／效度分析）

核心问题：用「自我/外界」这把尺子去量 77 位思想家，这把尺子准吗？

设计：两名【独立评分者】对同一批条目重新分类，与现标比对。
  评分者 A（句法判据）：条目含自称/自指词（我吾己予余自）→ A 类，否则 B 类
  评分者 B（主题判据）：条目 A 线索计数 > B 线索计数 → A 类，反之 B 类，平手则弃权
  现标：库内已有标注（v1 规则）

四个可证伪假设：
  H1 信度  现标与两名评分者的一致性（Cohen's κ）显著高于随机 → 尺子可信
  H2 误差  由信度推算测量标准误 SEM 与最小可检出差异 MDC
  H3 失配  归类不一致度与「①界线」取值相关——界线=未分者不一致度更高
  H4 预设  只接受三问预设者（界线=二分 且 关系=实体）的测量误差更小

反证条件（写死在代码里，结果若不符即假设被否）：
  H1 若 κ < 0.20 → 尺子不可信，全部 A/B 比较作废
  H3 若两组差异 p > 0.05 → 框架失配假说不成立
  H4 若两组 SEM 无差异 → 三问预设与测量误差无关

运行： python 信度检验.py
"""
import glob
import io
import math
import os
import re
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.abspath(__file__))
SKIP = ("README", "统计总表", "工具", "升维", "分析", "审查", "坐标表", "建站", "三问", "信度")
SELF = set("我吾己予余自")
A_CUE = ["省", "修", "养", "欲", "悔", "耻", "志", "慎", "惧", "畏", "忧",
         "静", "虚", "忘", "独", "反", "心", "性", "身", "情", "意",
         "良知", "浩然", "赤子", "知足", "知止", "寡欲", "生死", "死生", "自省", "自反"]
B_CUE = ["政", "法", "君", "民", "天下", "国", "治", "乱", "礼", "伦", "群",
         "赏", "罚", "刑", "名", "是非", "言", "辩", "学", "知", "天", "道",
         "理", "气", "自然", "物", "阴阳", "五行", "制", "度", "禁", "术"]


def load_entries():
    """→ [(人物, 现标, 文本)]"""
    rows = []
    for f in sorted(glob.glob(os.path.join(ROOT, "**", "*.md"), recursive=True)):
        if os.path.basename(f).startswith(SKIP) or (os.sep + "docs" + os.sep) in f:
            continue
        name = os.path.basename(f)[:-3]
        cur = None
        for line in io.open(f, encoding="utf-8").read().split("\n"):
            if line.startswith("## 二、"): cur = "A"
            elif line.startswith("## 三、"): cur = "B"
            elif line.startswith("## 四、"): cur = None
            elif cur and re.match(r"^\d+\.\s", line):
                rows.append((name, cur, line.strip()))
    return rows


def coder_syntax(text):
    return "A" if (SELF & set(text)) else "B"


def coder_theme(text):
    a = sum(text.count(w) for w in A_CUE)
    b = sum(text.count(w) for w in B_CUE)
    if a == b:
        return None
    return "A" if a > b else "B"


def kappa(pairs):
    """pairs: [(x, y)] 两分类。返回 (κ, po, pe, n)"""
    pairs = [(x, y) for x, y in pairs if x and y]
    n = len(pairs)
    if n == 0:
        return None
    po = sum(1 for x, y in pairs if x == y) / n
    cx, cy = Counter(x for x, _ in pairs), Counter(y for _, y in pairs)
    pe = sum(cx[k] / n * cy[k] / n for k in ("A", "B"))
    return ((po - pe) / (1 - pe) if pe < 1 else None), po, pe, n


def mannwhitney(a, b):
    """返回 (U, z, p双尾) —— 秩和检验"""
    if not a or not b:
        return None
    allv = [(v, 0) for v in a] + [(v, 1) for v in b]
    allv.sort()
    ranks, i = {}, 0
    rk = [0.0] * len(allv)
    while i < len(allv):
        j = i
        while j + 1 < len(allv) and allv[j + 1][0] == allv[i][0]:
            j += 1
        avg = (i + j) / 2 + 1
        for k in range(i, j + 1):
            rk[k] = avg
        i = j + 1
    r1 = sum(rk[k] for k in range(len(allv)) if allv[k][1] == 0)
    n1, n2 = len(a), len(b)
    u1 = r1 - n1 * (n1 + 1) / 2
    u2 = n1 * n2 - u1
    u = min(u1, u2)
    mu = n1 * n2 / 2
    sd = math.sqrt(n1 * n2 * (n1 + n2 + 1) / 12)
    z = (u - mu) / sd if sd else 0
    p = 2 * (1 - 0.5 * (1 + math.erf(abs(z) / math.sqrt(2))))
    return u, z, p


def pearson(xs, ys):
    n = len(xs)
    if n < 3:
        return 0.0
    mx, my = sum(xs) / n, sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den = math.sqrt(sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys))
    return num / den if den else 0.0


def main():
    entries = load_entries()
    import csv as _c
    with io.open(os.path.join(ROOT, "坐标表.csv"), encoding="utf-8-sig") as fp:
        coord = {r["人物"]: r for r in _c.DictReader(fp)}
    with io.open(os.path.join(ROOT, "统计总表.csv"), encoding="utf-8-sig") as fp:
        tot_tbl = {r["人物"]: r for r in _c.DictReader(fp)}

    tot = len(entries)
    print("=" * 78)
    print("信度／效度检验：把「自我 / 外界」当作测量工具")
    print("=" * 78)
    print("条目总数 %d ｜ 思想家 %d 人\n" % (tot, len(coord)))

    # ── H1 信度 ────────────────────────────────────────────────
    ps = [(s, coder_syntax(t)) for _, s, t in entries]
    pt = [(s, coder_theme(t)) for _, s, t in entries]
    pt = [(s, c) for s, c in pt if c]
    st = [(coder_syntax(t), coder_theme(t)) for _, _, t in entries]
    st = [(x, y) for x, y in st if y]

    print("【H1】信度：两名独立评分者 vs 现标的一致性")
    print("  %-34s %8s %8s %8s" % ("比对", "κ", "一致率", "n"))
    for label, pr in [("现标 ↔ 句法判据", ps), ("现标 ↔ 主题判据", pt),
                      ("句法判据 ↔ 主题判据（核心）", st)]:
        k = kappa(pr)
        if k and k[0] is not None:
            print("  %-34s %8.3f %7.1f%% %8d" % (label, k[0], k[1] * 100, k[3]))
    k_st = kappa(st)[0]
    print("\n  各判据的 A 类占比（差得越多，κ 越低）：")
    for label, pr in [("现标", ps), ("句法判据", [(coder_syntax(t),) * 2 for _, _, t in entries]),
                      ("主题判据", [(c,) * 2 for c in [coder_theme(t) for _, _, t in entries] if c])]:
        cc = Counter(x for x, _ in [(a, b) for a, b in pr if a])
        nn = sum(cc.values())
        print("    %-10s A 占 %.1f%%（n=%d）" % (label, cc["A"] / nn * 100 if nn else 0, nn))
    print("\n  → κ 判据：<0.20 不可信（尺子作废）／0.20–0.40 勉强／0.40–0.60 中等／>0.60 良好")
    print("  → 两名独立评分者 κ = %.3f ⇒ %s" % (
        k_st, "尺子不可信，A/B 比较作废" if k_st < 0.2 else
        ("勉强可用，须报不确定带" if k_st < 0.4 else
         ("中等可信" if k_st < 0.6 else "良好"))))

    # ── H2 测量误差 ────────────────────────────────────────────
    per = defaultdict(list)
    for n, s, t in entries:
        per[n].append((s, coder_syntax(t), coder_theme(t)))
    shares = []
    for n, v in per.items():
        if n in coord:
            shares.append(int(tot_tbl[n]["A对自我"]) / int(tot_tbl[n]["合计"]))
    sd_obs = math.sqrt(sum((x - sum(shares) / len(shares)) ** 2 for x in shares) / len(shares))
    rel = max(k_st, 0.0)
    sem = sd_obs * math.sqrt(max(1 - rel, 0))
    mdc = 1.96 * math.sqrt(2) * sem
    icc = rel  # 平行测量假设下，观测信度 = 真分数方差占比

    print("\n【H2】测量误差：由信度推出的可检出下限")
    print("  观测标准差 SD            = %.1f pp（跨 %d 人）" % (sd_obs * 100, len(shares)))
    print("  信度系数 reliability      = %.3f" % rel)
    print("  测量标准误 SEM            = %.1f pp" % (sem * 100))
    print("  最小可检出差异 MDC        = %.1f pp   ← 小于此值的任何组间差都在噪声里"
          % (mdc * 100))
    print()
    print("  对照本库已报告的全部效应量：")
    for label, eff in [("关切最大组间差（修养50.1%% vs 制度44.3%%）", 5.8),
                       ("传统组间差（中国45.3%% vs 西方48.0%%）", 2.7),
                       ("判定规则不确定带宽", 7.1),
                       ("单样本标准误 SE", 6.7),
                       ("德谟克利特 vs 巴门尼德（自然实验）", 32.0)]:
        mark = "✗ 不可检出" if eff < mdc * 100 else "✓ 可检出"
        print("    %-42s %5.1f pp   %s" % (label, eff, mark))

    # ── 逐人数据 ───────────────────────────────────────────────
    texts = defaultdict(list)
    for n, s, t in entries:
        texts[n].append((s, t))

    def amb_rate(name):
        v = texts[name]
        both = 0
        for _, t in v:
            a = sum(t.count(w) for w in A_CUE)
            b = sum(t.count(w) for w in B_CUE)
            if a > 0 and b > 0:
                both += 1
        return both / len(v)

    per_rows = []
    for n, v in per.items():
        if n not in coord:
            continue
        a_syn = sum(1 for _, sy, _ in v if sy == "A") / len(v)
        th = [(sy, t) for _, sy, t in v if t]
        a_th = sum(1 for _, t in th if t == "A") / len(th) if th else None
        per_rows.append({
            "name": n, "n": len(v),
            "obs": int(tot_tbl[n]["A对自我"]) / int(tot_tbl[n]["合计"]),
            "syn": a_syn, "th": a_th,
            "gap": abs(a_syn - (a_th if a_th is not None else a_syn)),
            "amb": amb_rate(n),
            "bound": coord[n]["①界线"], "rel": coord[n]["①关系"],
        })

    # ── H3 框架失配 ────────────────────────────────────────────
    g1 = [r["amb"] for r in per_rows if r["bound"] == "二分"]
    g2 = [r["amb"] for r in per_rows if r["bound"] != "二分"]
    res = mannwhitney(g1, g2)
    print("\n【H3】框架失配：归类不确定度 是否随「①界线」而变")
    print("  界线=二分（框架适配，n=%d）  不确定度 中位 %.1f%%" % (len(g1), sorted(g1)[len(g1) // 2] * 100))
    print("  界线≠二分（框架失配，n=%d）  不确定度 中位 %.1f%%" % (len(g2), sorted(g2)[len(g2) // 2] * 100))
    print("  Mann–Whitney U=%.0f  z=%+.2f  p=%.4f  ⇒ %s"
          % (res[0], res[1], res[2], "差异显著，假说成立" if res[2] < 0.05 else "差异不显著，假说不成立"))

    # ── H4 三问预设与误差 ───────────────────────────────────────
    strict = [r for r in per_rows if r["bound"] == "二分" and r["rel"] == "实体"]
    other = [r for r in per_rows if not (r["bound"] == "二分" and r["rel"] == "实体")]

    def grp_sem(rs):
        if len(rs) < 3:
            return None, None
        sh = [r["obs"] for r in rs]
        m = sum(sh) / len(sh)
        sd = math.sqrt(sum((x - m) ** 2 for x in sh) / len(sh))
        kk = [(r["obs"], r["syn"]) for r in rs]
        return sd, abs(pearson([r["obs"] for r in rs], [r["syn"] for r in rs]))

    sd_a, r_a = grp_sem(strict)
    sd_b, r_b = grp_sem(other)
    res4 = mannwhitney([r["gap"] for r in strict], [r["gap"] for r in other])
    print("\n【H4】三问预设：只接受预设者（界线=二分 且 关系=实体）测量误差更小吗")
    print("  接受预设组 n=%d ｜ 不接受组 n=%d" % (len(strict), len(other)))
    print("  组内 A 占比 SD：  接受 %.1f pp ｜ 不接受 %.1f pp" % (sd_a * 100, sd_b * 100))
    print("  判据间距（句法 vs 主题）中位：接受 %.1f pp ｜ 不接受 %.1f pp"
          % (sorted(r["gap"] for r in strict)[len(strict) // 2] * 100,
             sorted(r["gap"] for r in other)[len(other) // 2] * 100))
    print("  Mann–Whitney z=%+.2f  p=%.4f  ⇒ %s"
          % (res4[1], res4[2], "接受预设者误差显著更小，假说成立" if res4[2] < 0.05
             else "两组误差无显著差异，假说不成立"))

    # ── 结论 ───────────────────────────────────────────────────
    print("\n" + "=" * 78)
    print("结论")
    print("=" * 78)
    print("  1. 尺子信度 κ = %.3f —— %s" % (
        k_st, "不可信" if k_st < 0.2 else ("勉强" if k_st < 0.4 else "中等")))
    print("  2. 最小可检出差异 MDC = %.1f pp" % (mdc * 100))
    print("  3. 本库全部已报告效应中，小于 MDC 的一律不可检出。")
    print("  4. 唯一稳稳超过 MDC 的是自然实验（德谟克利特 vs 巴门尼德 32 pp）。")


if __name__ == "__main__":
    main()
