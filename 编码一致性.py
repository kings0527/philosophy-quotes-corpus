# -*- coding: utf-8 -*-
"""
v2 规则（对象域）的评分者间信度检验

设计：两名独立编码员，盲编码同一批 150 条（看不到现标、看不到人名学派）。
对比基准：v1 规则的评分者间信度 κ = 0.150（句法判据 vs 主题判据，n=3329）

输出：
  ① v2 的 κ、一致率、混淆矩阵
  ② v2 与 v1 的信度对比
  ③ v2 与现标(v1) 的一致性——检验旧标注的系统偏差
  ④ 由 v2 推算的全库 A 占比
运行： python 编码一致性.py
"""
import csv
import io
import os
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.abspath(__file__))
CATS = ["自我", "他者", "世界", "符号", "同一"]


def rd(fn, key="对象域"):
    with io.open(os.path.join(ROOT, fn), encoding="utf-8-sig") as fp:
        return {r["ID"]: r[key] for r in csv.DictReader(fp)}


def kappa_multi(pairs, cats=None):
    pairs = [(a, b) for a, b in pairs if a and b]
    n = len(pairs)
    if not n:
        return None
    if cats is None:
        cats = sorted(set(x for p in pairs for x in p))
    po = sum(1 for a, b in pairs if a == b) / n
    ca, cb = Counter(a for a, _ in pairs), Counter(b for _, b in pairs)
    pe = sum(ca[k] / n * cb[k] / n for k in cats)
    return {"k": (po - pe) / (1 - pe) if pe < 1 else None, "po": po, "pe": pe,
            "n": n, "ca": ca, "cb": cb}


def main():
    jia = rd("编码-甲.csv")
    yi = rd("编码-乙.csv")
    smp = {}
    with io.open(os.path.join(ROOT, "编码样本.csv"), encoding="utf-8-sig") as fp:
        for r in csv.DictReader(fp):
            smp[r["ID"]] = r
    ids = sorted(jia, key=int)
    assert set(ids) == set(yi) and len(ids) == 150, "编码未对齐"

    print("=" * 78)
    print("v2 规则（对象域）· 评分者间信度检验　n = %d 条" % len(ids))
    print("=" * 78)

    # ── ① v2 信度 ──────────────────────────────────────────────
    res = kappa_multi([(jia[i], yi[i]) for i in ids], CATS)
    print("\n【一】两名独立编码员的一致度")
    print("  一致率 po = %.1f%%　｜　随机一致率 pe = %.1f%%　｜　**Cohen κ = %.3f**"
          % (res["po"] * 100, res["pe"] * 100, res["k"]))
    print("\n  编码员甲分布：", " ｜ ".join("%s %d" % (k, v) for k, v in res["ca"].most_common()))
    print("  编码员乙分布：", " ｜ ".join("%s %d" % (k, v) for k, v in res["cb"].most_common()))

    print("\n  混淆矩阵（行=甲，列=乙）：")
    cm = defaultdict(Counter)
    for i in ids:
        cm[jia[i]][yi[i]] += 1
    print("  %-6s %s" % ("甲＼乙", "".join("%7s" % c for c in CATS)))
    for a in CATS:
        print("  %-6s %s" % (a, "".join("%7d" % cm[a][b] for b in CATS)))
    print("  —— 对角线即一致；非对角线上最大的三个误配对：")
    off = sorted(((cm[a][b], a, b) for a in CATS for b in CATS if a != b), reverse=True)[:3]
    for v, a, b in off:
        print("     %s → %s ： %d 条（占全部不一致的 %.0f%%）" % (a, b, v, v / (res["n"] * (1 - res["po"])) * 100))

    # ── ② 与 v1 信度对比 ──────────────────────────────────────
    print("\n【二】与 v1 规则的信度对比")
    print("  %-40s %8s %8s" % ("", "κ", "一致率"))
    print("  %-40s %8.3f %7.1f%%" % ("v1：句法判据 ↔ 主题判据（n=3329）", 0.150, 60.8))
    print("  %-40s %8.3f %7.1f%%" % ("v2：编码员甲 ↔ 编码员乙（n=150）", res["k"], res["po"] * 100))
    delta = res["k"] - 0.150
    print("\n  → κ 提升 %+.3f（%.1f 倍）" % (delta, res["k"] / 0.150))
    verdict = ("v2 仍未达标（κ<0.40），规则还不够硬" if res["k"] < 0.40 else
               "v2 达到「中等可信」（κ≥0.40）" if res["k"] < 0.60 else "v2 达到「良好」（κ≥0.60）")
    print("  → 判定：%s" % verdict)

    # ── ③ v2 vs 现标 ──────────────────────────────────────────
    def toAB(v):
        if v in ("他者", "世界", "符号"):
            return "B"
        if v == "自我":
            return "A"
        return None

    pa = [(toAB(jia[i]), smp[i]["现标v1"]) for i in ids]
    pa = [(a, b) for a, b in pa if a]
    r2 = kappa_multi(pa, ["A", "B"])
    print("\n【三】v2（两名编码员合并）与现标 v1 的一致性")
    print("  κ = %.3f　一致率 %.1f%%　n = %d" % (r2["k"], r2["po"] * 100, r2["n"]))
    n_a = sum(1 for a, _ in pa if a == "A")
    s_a = sum(1 for _, b in pa if b == "A")
    print("  A 类占比：v2 编码 %.1f%% ｜ 现标 v1 %.1f%%（差 %.1f pp）"
          % (n_a / len(pa) * 100, s_a / len(pa) * 100, (s_a - n_a) / len(pa) * 100))
    print("  → %s" % ("现标系统性偏向 A 类" if s_a > n_a else "现标系统性偏向 B 类"))

    # 同一（self-other）的处置对比
    both_same = sum(1 for i in ids if (jia[i] == "同一") + (yi[i] == "同一") >= 1)
    print("\n  「同一」类：甲 %d 条、乙 %d 条，至少一人判为「同一」的共 %d 条"
          % (sum(1 for i in ids if jia[i] == "同一"),
             sum(1 for i in ids if yi[i] == "同一"), both_same))
    sv = [i for i in ids if smp[i]["现标v1"] == "A" and jia[i] == "同一"]
    print("  其中现标标为 A 的 %d 条 —— v1 把「同一」混进了 A 类" % len(sv))

    # ── ④ 全库估计 ────────────────────────────────────────────
    print("\n【四】由 v2 推算的全库 A 占比")
    valid = [i for i in ids if jia[i] != "同一" and yi[i] != "同一"]
    a_share = sum(1 for i in valid if toAB(jia[i]) == "A") / len(valid) * 100
    print("  剔除「同一」后的样本 A 占比 = %.1f%%（n=%d）" % (a_share, len(valid)))
    print("  对照：现标全库 47.3%% ｜ 关键词句法判据 35.0%% ｜ 关键词主题判据 36.6%%")
    print("  → 三套独立方法给出的全库 A 占比区间：%.0f%% – 47%%" % a_share)

    # ── ⑤ 修好尺子后的可检出下限 ──────────────────────────────
    import math
    sd_obs = 0.066          # 跨 76 人的观测标准差（pp 单位见下）
    print("\n【五】尺子修好后，最小可检出差异 MDC 的变化")
    print("  %-28s %10s %10s %10s" % ("", "信度", "SEM", "MDC"))
    for label, rel in [("v1 规则（κ=0.150）", 0.150), ("v2 规则（κ=0.864）", res["k"])]:
        sem = sd_obs * math.sqrt(max(1 - rel, 0))
        mdc = 1.96 * math.sqrt(2) * sem
        print("  %-28s %9.3f %8.1f pp %8.1f pp" % (label, rel, sem * 100, mdc * 100))
    mdc_v1 = 1.96 * math.sqrt(2) * sd_obs * math.sqrt(1 - 0.150)
    mdc_v2 = 1.96 * math.sqrt(2) * sd_obs * math.sqrt(1 - res["k"])
    print("\n  → MDC 从 %.1f pp 降到 %.1f pp（降幅 %.0f%%）"
          % (mdc_v1 * 100, mdc_v2 * 100, (1 - mdc_v2 / mdc_v1) * 100))
    print("\n  用新尺子重新审视各效应：")
    for label, eff in [("传统组间差（中国 45.3%% vs 西方 48.0%%）", 2.7),
                       ("关切最大组间差（修养 50.1%% vs 制度 44.3%%）", 5.8),
                       ("判定规则不确定带宽（v1）", 7.1),
                       ("德谟克利特 vs 巴门尼德（自然实验）", 32.0)]:
        print("    %-42s %5.1f pp  %s" % (label, eff,
              "✓ 现在可检出" if eff >= mdc_v2 * 100 else "✗ 仍在噪声内"))
    print("\n  → 结论：换尺子能救回「接近 7 pp」量级的效应，但 3–6 pp 的组间差依然测不出。")


if __name__ == "__main__":
    main()
