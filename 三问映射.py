# -*- coding: utf-8 -*-
"""
终极三问 ↔ 升维四问：映射检验

user 的发现：四问是否就是「我是谁 / 我从哪里来 / 我到哪里去」？

本脚本做三件事：
  ① 逐项检验映射（哪些严格对应、哪些对不上）
  ② 量化「三问框架的预设」在库内被接受／被取消的比例
  ③ 给出五问结构（四问 + 目的轴）与三问的最终关系

运行： python 三问映射.py
"""
import csv
import io
import os
from collections import Counter

ROOT = os.path.dirname(os.path.abspath(__file__))


def load():
    with io.open(os.path.join(ROOT, "坐标表.csv"), encoding="utf-8-sig") as fp:
        return list(csv.DictReader(fp))


def main():
    rows = load()
    n = len(rows)
    g = lambda r, k: r[k]

    print("=" * 76)
    print("终极三问 ↔ 升维四问 · 映射检验")
    print("=" * 76)

    # ── ① 映射检验 ───────────────────────────────────────────────
    print("""
【一】逐项映射

  终极三问                     本文轴系                        判定
  ───────────────────────────────────────────────────────────────────
  我是谁        →   ① 界线 + ① 关系                ✅ 严格对应
  我从哪里来    →   ② 不动层                        ✅ 严格对应（地基即来处）
  我到哪里去    →   ——（原四问无此格）             ❌ 原系统缺位
  ④ 我能改变什么 →  （三问中无对应）                ⚠️ 三问接不住
  ③ 秩序和知识从哪来 →  （三问中无对应）             ⚠️ 三问接不住

  结论：不是「四问 = 三问」，而是四问【分裂成两族】：
        本体三问（我是谁/从哪来/到哪去）  ↔  三问严格对应（前提是补上「目的」）
        运作两问（秩序从哪来/我能改什么）↔  三问接不住——它们问的是"怎么运转"，不是"在哪里"
""")

    # ── ② 三问的预设被接受／被取消 ───────────────────────────────
    print("【二】三问框架的隐藏预设，在库内被接受还是被取消？")
    print("""
  三问不是中立提问，它预设了三件事：
    (P1) 有一个持存的「我」          → 需要明确的自我边界
    (P2) 时间有起点（从哪来）        → 需要"生"这件事成立
    (P3) 时间有终点（到哪去）        → 需要"目的/归宿"这件事成立
""")

    p1_ok = [r for r in rows if r["①界线"] == "二分"]
    p1_no = [r for r in rows if r["①界线"] == "未分"]
    p1_mid = [r for r in rows if r["①界线"] == "统一"]
    print("  P1「持存的独立自我」")
    print("     边界明确（界线=二分）→ 可问「我是谁」      %2d 人（%.0f%%）" % (len(p1_ok), len(p1_ok) / n * 100))
    print("     边界消解（界线=未分）→ 「我是谁」需改写      %2d 人（%.0f%%）" % (len(p1_no), len(p1_no) / n * 100))
    print("     边界统一（界线=统一）→ 「我是谁」含世界      %2d 人（%.0f%%）" % (len(p1_mid), len(p1_mid) / n * 100))

    no_birth = [r for r in rows if r["②不动层"] in ("缘起·空", "道·自然")]
    print("\n  P2「时间有起点（我从哪里来）」")
    print("     承认有来处（不动层为可追溯的地基）         %2d 人" % (n - len(no_birth)))
    print("     取消来处（缘起·空 / 道·自然，无始无生）      %2d 人：%s"
          % (len(no_birth), "、".join(r["人物"] for r in no_birth)))

    no_end = [r for r in rows if r["③目的"] == "当下·无求"]
    print("\n  P3「时间有终点（我到哪里去）」")
    print("     有明确归宿（目的轴 ≠ 当下·无求）           %2d 人（%.0f%%）" % (n - len(no_end), (n - len(no_end)) / n * 100))
    print("     取消归宿（当下·无求）                       %2d 人：%s"
          % (len(no_end), "、".join(r["人物"] for r in no_end)))

    strict = [r for r in rows if r["①界线"] == "二分" and r["①关系"] == "实体"]
    print("\n  → 三项预设【全部接受】的人（三问最正宗的答题者）：%d 人（%.0f%%）" % (len(strict), len(strict) / n * 100))
    print("     " + "、".join(r["人物"] for r in strict))

    # ── ③ 目的轴分布 ─────────────────────────────────────────────
    print("\n【三】新增「目的」轴后的分布（三问的第三问才第一次有答案）")
    c = Counter(r["③目的"] for r in rows)
    for k, v in c.most_common():
        who = [r["人物"] for r in rows if r["③目的"] == k]
        print("  %-12s %2d 人  %s" % (k, v, "、".join(who[:8]) + ("…" if len(who) > 8 else "")))

    # ── ④ 不动层 与 目的 是否正交 ────────────────────────────────
    print("\n【四】正交性检验：「哪一层不动」与「要到哪里去」是两件事吗？")
    cross = {}
    for r in rows:
        cross.setdefault(r["②不动层"], set()).add(r["③目的"])
    multi = {k: v for k, v in cross.items() if len(v) >= 2}
    print("  同一个「不动层」下出现 ≥2 种「目的」的组：%d / %d" % (len(multi), len(cross)))
    for k, v in list(multi.items())[:5]:
        print("    · 不动层=%s → 目的 ∈ {%s}" % (k, "、".join(sorted(v))))
    print("\n  反例（证明两者独立）：")
    for a, b in [("荀子", "苏格拉底"), ("老子", "第欧根尼"), ("笛卡尔", "洛克")]:
        ra = next(r for r in rows if r["人物"] == a)
        rb = next(r for r in rows if r["人物"] == b)
        print("    %s（不动层=%s，目的=%s）  vs  %s（不动层=%s，目的=%s）"
              % (a, ra["②不动层"], ra["③目的"], b, rb["②不动层"], rb["③目的"]))


if __name__ == "__main__":
    main()
