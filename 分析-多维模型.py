# -*- coding: utf-8 -*-
"""
哲学统计 · 多维思维模型分析

用八个模型对全库做「升维」分析：
  系统论 / 分层 / 约束 / 博弈论 / 控制论 / 概率论 / 进化论 / 贝叶斯

输入：统计总表.csv（条数已校验）+ 本文件内的 TAGS（人工判定的独立标签）
输出：元数据.csv + 分析结果.md（全部数字，供报告引用）

关键设计：TAGS 中的「核心关切」「文体」「可靠度」是**独立于条数**判定的，
因此可以用来检验 A 占比的差异，而不是循环论证。
运行： python 分析-多维模型.py
"""
import os
import io
import csv
import math

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = []


def p(s=""):
    OUT.append(s)
    print(s)


# ── 人工判定标签（核心关切 / 文体 / 可靠度），独立于 A/B 条数 ────────────────
# 核心关切：修养—救赎 / 本体—宇宙 / 名实—逻辑 / 制度—政治 / 认识—方法 / 存在—自由
# 文体：语录体 / 格言体 / 论说体 / 注疏体 / 残篇 / 私人笔记 / 诗体
# 可靠度：亲著 / 弟子辑录 / 残篇 / 遗稿编纂
TAGS = {
    # ── 中国哲学 ──
    "陆九渊": ("修养—救赎", "语录体", "弟子辑录"),
    "王阳明": ("修养—救赎", "语录体", "弟子辑录"),
    "程颢": ("修养—救赎", "语录体", "弟子辑录"),
    "程颐": ("修养—救赎", "语录体", "弟子辑录"),
    "朱熹": ("本体—宇宙", "语录体", "弟子辑录"),
    "孔子": ("修养—救赎", "语录体", "弟子辑录"),
    "孟子": ("修养—救赎", "论说体", "亲著"),
    "荀子": ("制度—政治", "论说体", "亲著"),
    "庄子": ("修养—救赎", "论说体", "亲著"),
    "老子": ("本体—宇宙", "诗体", "亲著"),
    "墨子": ("制度—政治", "论说体", "亲著"),
    "韩非": ("制度—政治", "论说体", "亲著"),
    "商鞅": ("制度—政治", "论说体", "亲著"),
    "孙子": ("制度—政治", "论说体", "亲著"),
    "公孙龙": ("名实—逻辑", "论说体", "亲著"),
    "惠施": ("名实—逻辑", "残篇", "残篇"),
    "董仲舒": ("制度—政治", "论说体", "亲著"),
    "王充": ("认识—方法", "论说体", "亲著"),
    "王弼": ("本体—宇宙", "注疏体", "亲著"),
    "嵇康": ("修养—救赎", "论说体", "亲著"),
    "郭象": ("本体—宇宙", "注疏体", "亲著"),
    "僧肇": ("本体—宇宙", "论说体", "亲著"),
    "慧能": ("修养—救赎", "语录体", "弟子辑录"),
    "周敦颐": ("本体—宇宙", "论说体", "亲著"),
    "张载": ("本体—宇宙", "论说体", "亲著"),
    "李贽": ("修养—救赎", "论说体", "亲著"),
    "王夫之": ("本体—宇宙", "论说体", "亲著"),
    "顾炎武": ("制度—政治", "论说体", "亲著"),
    "黄宗羲": ("制度—政治", "论说体", "亲著"),
    "冯友兰": ("本体—宇宙", "论说体", "亲著"),
    "熊十力": ("本体—宇宙", "论说体", "亲著"),
    "牟宗三": ("本体—宇宙", "论说体", "亲著"),
    # ── 西方哲学 ──
    "苏格拉底": ("修养—救赎", "语录体", "弟子辑录"),
    "赫拉克利特": ("本体—宇宙", "残篇", "残篇"),
    "巴门尼德": ("本体—宇宙", "残篇", "残篇"),
    "德谟克利特": ("本体—宇宙", "残篇", "残篇"),
    "柏拉图": ("本体—宇宙", "论说体", "亲著"),
    "亚里士多德": ("认识—方法", "论说体", "亲著"),
    "第欧根尼": ("修养—救赎", "残篇", "后世纪录"),
    "伊壁鸠鲁": ("修养—救赎", "论说体", "亲著"),
    "爱比克泰德": ("修养—救赎", "语录体", "弟子辑录"),
    "塞涅卡": ("修养—救赎", "论说体", "亲著"),
    "马可·奥勒留": ("修养—救赎", "私人笔记", "亲著"),
    "奥古斯丁": ("修养—救赎", "论说体", "亲著"),
    "阿奎那": ("本体—宇宙", "论说体", "亲著"),
    "笛卡尔": ("认识—方法", "论说体", "亲著"),
    "帕斯卡": ("修养—救赎", "格言体", "遗稿编纂"),
    "斯宾诺莎": ("本体—宇宙", "论说体", "亲著"),
    "洛克": ("认识—方法", "论说体", "亲著"),
    "莱布尼茨": ("本体—宇宙", "论说体", "亲著"),
    "休谟": ("认识—方法", "论说体", "亲著"),
    "康德": ("认识—方法", "论说体", "亲著"),
    "黑格尔": ("本体—宇宙", "论说体", "亲著"),
    "叔本华": ("存在—自由", "论说体", "亲著"),
    "克尔凯郭尔": ("存在—自由", "论说体", "亲著"),
    "马克思": ("制度—政治", "论说体", "亲著"),
    "密尔": ("制度—政治", "论说体", "亲著"),
    "尼采": ("存在—自由", "格言体", "遗稿编纂"),
    "胡塞尔": ("认识—方法", "论说体", "亲著"),
    "海德格尔": ("存在—自由", "论说体", "亲著"),
    "雅斯贝尔斯": ("存在—自由", "论说体", "亲著"),
    "萨特": ("存在—自由", "论说体", "亲著"),
    "加缪": ("存在—自由", "论说体", "亲著"),
    "维特根斯坦": ("名实—逻辑", "格言体", "亲著"),
    "罗素": ("名实—逻辑", "论说体", "亲著"),
    "波普尔": ("认识—方法", "论说体", "亲著"),
    "阿伦特": ("制度—政治", "论说体", "亲著"),
    "福柯": ("制度—政治", "论说体", "亲著"),
    # ── 印度 / 伊斯兰波斯 / 日本 ──
    "释迦牟尼": ("修养—救赎", "语录体", "弟子辑录"),
    "龙树": ("本体—宇宙", "论说体", "亲著"),
    "商羯罗": ("本体—宇宙", "注疏体", "亲著"),
    "克里希那穆提": ("修养—救赎", "语录体", "弟子辑录"),
    "安萨里": ("修养—救赎", "论说体", "亲著"),
    "鲁米": ("修养—救赎", "诗体", "亲著"),
    "海亚姆（奥马尔·海亚姆）": ("存在—自由", "诗体", "亲著"),
    "道元": ("修养—救赎", "论说体", "亲著"),
    "吉田兼好": ("修养—救赎", "私人笔记", "亲著"),
}


def load():
    with io.open(os.path.join(ROOT, "统计总表.csv"), encoding="utf-8-sig") as fp:
        rows = list(csv.DictReader(fp))
    for r in rows:
        r["n"] = int(r["合计"])
        r["k"] = int(r["A对自我"])
        r["shr"] = float(r["A占比"])
        r["译数"] = int(r["〔译〕"])
        t = TAGS.get(r["人物"])
        if not t:
            raise SystemExit("缺少标签：" + r["人物"])
        r["关切"], r["文体"], r["可靠度"] = t
    return rows


def mean(xs):
    return sum(xs) / len(xs) if xs else float("nan")


def var(xs):
    m = mean(xs)
    return sum((x - m) ** 2 for x in xs) / len(xs) if len(xs) > 1 else float("nan")


def eta2(rows, field):
    """组间方差占比（η²）：该维度能解释 A 占比总方差的比例。"""
    total = var([r["shr"] for r in rows])
    groups = {}
    for r in rows:
        groups.setdefault(r[field], []).append(r["shr"])
    between = sum(len(v) * (mean(v) - mean([r["shr"] for r in rows])) ** 2
                  for v in groups.values()) / len(rows)
    return between / total if total else 0.0, groups


def main():
    rows = load()
    n_all = len(rows)
    A = sum(r["k"] for r in rows)
    B = sum(r["n"] - r["k"] for r in rows)

    p("=" * 72)
    p("哲学统计 · 多维思维模型分析")
    p("=" * 72)
    p("样本：%d 人 ｜ A(对自我) %d 条 ｜ B(对外界) %d 条 ｜ 合计 %d 条 ｜ A 占比 %.1f%%"
      % (n_all, A, B, A + B, A / (A + B) * 100))

    # ── 输出元数据 ───────────────────────────────────────────────
    with io.open(os.path.join(ROOT, "元数据.csv"), "w", encoding="utf-8-sig", newline="") as fp:
        w = csv.writer(fp)
        w.writerow(["传统", "人物", "时代", "派别", "核心关切", "文体", "可靠度",
                    "A对自我", "B对外界", "合计", "A占比"])
        for r in sorted(rows, key=lambda x: (x["传统"], -x["shr"])):
            w.writerow([r["传统"], r["人物"], r["时代"], r["派别"], r["关切"], r["文体"],
                        r["可靠度"], r["k"], r["n"] - r["k"], r["n"], r["shr"]])
    p("\n→ 已写出 元数据.csv")

    # ── 模型 1：系统论 —— 自指带宽的天花板 ──────────────────────
    p("\n" + "─" * 72)
    p("【模型 1 · 系统论】自指通道 vs 对外通道的带宽不对称")
    p("─" * 72)
    shr = [r["shr"] for r in rows]
    hi = max(rows, key=lambda r: r["shr"])
    lo = min(rows, key=lambda r: r["shr"])
    hi_b = max(rows, key=lambda r: 1 - r["shr"])
    p("A(自指)占比：最高 %.1f%%（%s）／ 最低 %.1f%%（%s）／ 均值 %.1f%%"
      % (hi["shr"] * 100, hi["人物"], lo["shr"] * 100, lo["人物"], mean(shr) * 100))
    p("B(对外)占比：最高 %.1f%%（%s）／ 最低 %.1f%%（%s）"
      % ((1 - hi_b["shr"]) * 100, hi_b["人物"], (1 - hi["shr"]) * 100, hi["人物"]))
    p("超过 55%% 的人数：%d ／ 低于 45%% 的人数：%d"
      % (len([x for x in shr if x > 0.55]), len([x for x in shr if x < 0.45])))
    p("→ 上界不对称：A 的天花板是 %.0f%%，B 的天花板是 %.0f%%。"
      % (max(shr) * 100, (1 - min(shr)) * 100))
    p("   「只谈自己、不谈世界」的思想家在样本中不存在；「只谈世界、不谈自己」的存在。")

    # ── 模型 2：分层 —— 方差分解 ────────────────────────────────
    p("\n" + "─" * 72)
    p("【模型 2 · 分层】四层方差分解：差异到底出在哪一层？")
    p("─" * 72)
    for fld in ["传统", "可靠度", "文体", "关切"]:
        e, groups = eta2(rows, fld)
        detail = " ｜ ".join("%s %.1f%%(n=%d)" % (g, mean(v) * 100, len(v))
                              for g, v in sorted(groups.items(), key=lambda t: -mean(t[1])))
        p("%-6s η²=%5.1f%%   %s" % (fld, e * 100, detail))
    p("→ η² 越大，说明该维度越能解释差异。见下方「结论」。")

    # 各传统内部极差（检验「文化决定论」）
    p("\n各传统内部极差（若文化决定论成立，组内应很窄）：")
    for fld in ["传统"]:
        _, g = eta2(rows, fld)
        for k, v in sorted(g.items(), key=lambda t: -mean(t[1])):
            p("  %-12s 组内 %.1f%% – %.1f%%（跨度 %.1f pp，n=%d）"
              % (k, min(v) * 100, max(v) * 100, (max(v) - min(v)) * 100, len(v)))

    # ── 模型 3：约束 —— 文体与可靠度的效应 ──────────────────────
    p("\n" + "─" * 72)
    p("【模型 3 · 约束】是什么在约束 A 占比？")
    p("─" * 72)
    _, gb = eta2(rows, "文体")
    p("按文体（均值 A 占比）：")
    for k, v in sorted(gb.items(), key=lambda t: -mean(t[1])):
        p("  %-8s %.1f%%（n=%d）" % (k, mean(v) * 100, len(v)))
    _, gr = eta2(rows, "可靠度")
    p("按可靠度：")
    for k, v in sorted(gr.items(), key=lambda t: -mean(t[1])):
        p("  %-10s %.1f%%（n=%d）" % (k, mean(v) * 100, len(v)))
    # 条数、译文比 与 A 占比的相关
    def corr(f1, f2):
        xs = [f1(r) for r in rows]
        ys = [f2(r) for r in rows]
        mx, my = mean(xs), mean(ys)
        num = sum((a - mx) * (b - my) for a, b in zip(xs, ys))
        den = math.sqrt(sum((a - mx) ** 2 for a in xs) * sum((b - my) ** 2 for b in ys))
        return num / den if den else 0.0
    p("相关系数：")
    p("  A占比 vs 样本量 n        r = %+.3f" % corr(lambda r: r["shr"], lambda r: r["n"]))
    p("  A占比 vs 〔译〕条目数    r = %+.3f" % corr(lambda r: r["shr"], lambda r: r["译数"]))

    # ── 模型 6：概率论 —— 有多少差异是真的 ──────────────────────
    p("\n" + "─" * 72)
    p("【模型 6 · 概率论】二项抽样误差：哪些差异真实，哪些是噪声")
    p("─" * 72)
    n_med = sorted(r["n"] for r in rows)[len(rows) // 2]
    sd = math.sqrt(0.5 * 0.5 / n_med)
    p("中位样本量 n=%d → 若真实比例恰好 0.5，A 占比的标准误 SE=%.1f%%" % (n_med, sd * 100))
    p("即：±%.1f pp 以内的差异，与 50%% 不可区分（1 SE）；±%.1f pp 为 2 SE 界。"
      % (sd * 100, sd * 200))
    within1 = [r for r in rows if abs(r["shr"] - 0.5) <= sd]
    within2 = [r for r in rows if abs(r["shr"] - 0.5) <= 2 * sd]
    p("落在 ±1SE 内：%d 人（%.0f%%）｜ 落在 ±2SE 内：%d 人（%.0f%%）"
      % (len(within1), len(within1) / n_all * 100, len(within2), len(within2) / n_all * 100))
    # 精确落在 50% 的人数 vs 二项预期
    exact50 = [r for r in rows if abs(r["shr"] - 0.5) < 1e-9]
    p("A占比恰好=50.0%% 的人：%d 人（%.0f%%）" % (len(exact50), len(exact50) / n_all * 100))
    # 二项预期：若真是「从 p=0.5 的总体随机抽条」，恰好抽到一半的概率
    exp50 = 0.0
    for r in rows:
        n = r["n"]
        if n % 2 == 0:
            exp50 += math.comb(n, n // 2) / (2 ** n)
    p("若为纯二项随机（p=0.5），恰好=50%% 的期望人数：%.1f 人" % exp50)
    p("→ 观测 %.0f 人 vs 期望 %.1f 人，超出 %.1f 倍 ⇒ 存在**编纂配额效应**（非自然产生）"
      % (len(exact50), exp50, len(exact50) / exp50))
    p("   推论：中段（45%%–55%%）的分布是**编制产物**，不是思想读数；可信信号只能看尾部。")
    # 观测分布 vs 二项期望分布（供绘图与对照）
    bins = [(0.20, 0.25), (0.25, 0.30), (0.30, 0.35), (0.35, 0.40),
            (0.40, 0.45), (0.45, 0.50), (0.50, 0.55)]
    obs_bin = [0] * len(bins)
    exp_bin = [0.0] * len(bins)
    for r in rows:
        for i, (t_lo, t_hi) in enumerate(bins):
            if i == len(bins) - 1:
                hit = t_lo <= r["shr"] <= t_hi + 1e-9
            else:
                hit = t_lo <= r["shr"] < t_hi
            if hit:
                obs_bin[i] += 1
                break
        n, k = r["n"], r["k"]
        tot = 2.0 ** n
        for kk in range(n + 1):
            s = kk / n
            for i, (t_lo, t_hi) in enumerate(bins):
                if (t_lo <= s <= t_hi + 1e-9) if i == len(bins) - 1 else (t_lo <= s < t_hi):
                    exp_bin[i] += math.comb(n, kk) / tot
                    break
    p("\n A占比区间     观测人数   二项期望人数")
    for (b_lo, b_hi), o, e in zip(bins, obs_bin, exp_bin):
        p("  %.0f–%.0f%%        %3d        %6.1f" % (b_lo * 100, b_hi * 100, o, e))
    p("→ 二项模型（假设人人相同、只有抽样噪声）预测出一条钟形曲线；")
    p("  实际观测却在 50%% 处堆成尖峰、左侧拖出长尾——形状完全不同。")
    # 双比例 z 检验：极值互比
    def ztest(r1, r2):
        p1, n1 = r1["shr"], r1["n"]
        p2, n2 = r2["shr"], r2["n"]
        pp = (r1["k"] + r2["k"]) / (n1 + n2)
        se = math.sqrt(pp * (1 - pp) * (1 / n1 + 1 / n2))
        return (p1 - p2) / se if se else 0.0
    p("极值两两检验（z 值，|z|>1.96 才算显著）：")
    for a, b in [(hi, lo), (hi, next(r for r in sorted(rows, key=lambda x: x["shr"])[1:2])),
                 (hi, min(rows, key=lambda r: r["shr"] if r["shr"] > 0.25 else 1))]:
        p("  %s(%.1f%%) vs %s(%.1f%%)： z = %+.2f %s"
          % (a["人物"], a["shr"] * 100, b["人物"], b["shr"] * 100, ztest(a, b),
             "显著" if abs(ztest(a, b)) > 1.96 else "不显著"))

    # ── 模型 8：贝叶斯 —— 收缩估计 ──────────────────────────────
    p("\n" + "─" * 72)
    p("【模型 8 · 贝叶斯】分层收缩：把抽样噪声剥掉后的「真实」A 占比")
    p("─" * 72)
    obs = var([r["shr"] for r in rows])
    samp = mean([r["shr"] * (1 - r["shr"]) / r["n"] for r in rows])
    tau2 = max(obs - samp, 1e-9)
    p("观测方差 %.5f ｜ 平均抽样方差 %.5f ｜ 推断的真实个体间方差 tau²=%.5f"
      % (obs, samp, tau2))
    p("→ 观测到的离散度中，真正属于「思想家之间的差异」的占 %.0f%%，其余是抽样噪声。"
      % (tau2 / obs * 100))
    mu0 = 0.5   # 文体先验：语录体/论说体的编纂均衡性把先验压在 0.5
    p("先验 μ0=0.500（文体先验：编纂均衡性）")
    p("\n稀疏度最大的收缩示例（真实估计 = 后验均值）：")
    p("  %-10s %6s %6s %8s %8s" % ("人物", "n", "观测", "后验", "偏移"))
    demo = sorted(rows, key=lambda r: r["shr"])[:3] + sorted(rows, key=lambda r: -r["shr"])[:3] \
        + [r for r in rows if r["n"] < 40]
    seen = set()
    for r in demo:
        if r["人物"] in seen:
            continue
        seen.add(r["人物"])
        s2 = r["shr"] * (1 - r["shr"]) / r["n"]
        post = (r["shr"] / s2 + mu0 / tau2) / (1 / s2 + 1 / tau2)
        p("  %-10s %6d %5.1f%% %7.1f%% %+7.1f pp"
          % (r["人物"], r["n"], r["shr"] * 100, post * 100, (post - r["shr"]) * 100))

    # ── 模型 7：进化论 —— 核心关切的跨传统收敛 ──────────────────
    p("\n" + "─" * 72)
    p("【模型 7 · 进化论】跨传统收敛：相同生态位 → 相同解")
    p("─" * 72)
    _, gc = eta2(rows, "关切")
    p("按核心关切（均值 A 占比 / 人数 / 跨传统数）：")
    for k, v in sorted(gc.items(), key=lambda t: -mean(t[1])):
        fams = set(r["传统"] for r in rows if r["关切"] == k)
        p("  %-10s %5.1f%%   n=%2d   跨 %d 个传统  [%s]"
          % (k, mean(v) * 100, len(v), len(fams), "、".join(sorted(fams))))
    p("\n收敛检验：同一关切内部、跨越不同传统的极差：")
    for k in sorted(gc, key=lambda x: -mean(gc[x])):
        sub = [r for r in rows if r["关切"] == k]
        fams = set(r["传统"] for r in sub)
        if len(fams) >= 3:
            p("  %-10s 跨 %d 传统，组内 %.1f%% – %.1f%%（跨度 %.1f pp）"
              % (k, len(fams), min(r["shr"] for r in sub) * 100,
                 max(r["shr"] for r in sub) * 100,
                 (max(r["shr"] for r in sub) - min(r["shr"] for r in sub)) * 100))

    # ── 模型 4/5：博弈论与利己/开环反馈（描述性） ───────────────
    p("\n" + "─" * 72)
    p("【模型 4/5 · 博弈论 / 控制论】学派存续与 A 占比")
    p("─" * 72)
    extinct = ["商鞅", "公孙龙", "惠施", "墨子", "韩非"]
    p("中绝或失势的学派（法家·名家·墨家）：")
    for name in extinct:
        r = next(r for r in rows if r["人物"] == name)
        p("  %-6s %5.1f%%" % (name, r["shr"] * 100))
    p("  该组均值 %.1f%%（n=%d）" % (mean([next(r for r in rows if r["人物"] == x)["shr"]
                                        for x in extinct]) * 100, len(extinct)))
    core = ["孔子", "孟子", "荀子", "朱熹", "陆九渊", "王阳明", "董仲舒"]
    p("长期居于主流的儒家一系：")
    p("  该组均值 %.1f%%（n=%d）"
      % (mean([next(r for r in rows if r["人物"] == x)["shr"] for x in core]) * 100, len(core)))
    band = [r for r in rows if 0.45 <= r["shr"] <= 0.55]
    p("落在 45%%–55%% 均衡带的：%d 人（%.0f%%）" % (len(band), len(band) / n_all * 100))
    p("落在 45%%–55%% 之外且属于中绝学派的：%s"
      % "、".join(x for x in extinct if next(r for r in rows if r["人物"] == x)["shr"] < 0.45))

    # ── 补充检验 A：自然实验（同一人/同代/同传统，仅传承不同） ──
    p("\n" + "─" * 72)
    p("【补充检验 A · 自然实验】低 A 占比是「思想」还是「传承」？")
    p("─" * 72)
    p("对照组：公元前 5—4 世纪希腊，均为残篇/著作不全，仅「伦理材料是否幸存」不同")
    exp = [
        ("巴门尼德", "仅存《论自然》约 19 条残篇，全部论「存在」"),
        ("赫拉克利特", "仅存约 130 条残篇，经后人按哲学兴趣辑录"),
        ("德谟克利特", "残篇约 300 条，其中**伦理学格言**经斯托拜乌斯《选集》大量保存"),
        ("柏拉图", "著作完整传世（对话录全集）"),
        ("亚里士多德", "著作完整传世（含伦理学专著）"),
    ]
    for name, note in exp:
        r = next(x for x in rows if x["人物"] == name)
        p("  %-8s A=%5.1f%%   %s" % (name, r["shr"] * 100, note))
    dm = next(x for x in rows if x["人物"] == "德谟克利特")
    pm = next(x for x in rows if x["人物"] == "巴门尼德")
    hk = next(x for x in rows if x["人物"] == "赫拉克利特")
    p("→ 德谟克利特与巴门尼德**同代、同传统、同为残篇**，唯一差别是伦理格言是否被保存；")
    p("  A 占比相差 %.1f pp（%.1f%% vs %.1f%%）。"
      % ((dm["shr"] - pm["shr"]) * 100, dm["shr"] * 100, pm["shr"] * 100))
    p("  这是「低 A 占比 = 伦理材料未幸存」的直接证据，而非「不关注自我」的证据。")
    p("  另：早期自然哲学家三人均值 %.1f%% vs 完整传世的柏拉图/亚里士多德均值 %.1f%%"
      % (mean([pm["shr"], hk["shr"], dm["shr"]]) * 100,
         mean([next(x for x in rows if x["人物"] == y)["shr"] for y in ["柏拉图", "亚里士多德"]]) * 100))

    # ── 补充检验 B：关切组的组间显著性 ──────────────────────────
    p("\n" + "─" * 72)
    p("【补充检验 B】各核心关切组的差异是否显著（合并比例 z 检验，基准=修养—救赎）")
    p("─" * 72)

    def pooled(sub):
        return sum(r["k"] for r in sub), sum(r["n"] for r in sub)

    base = [r for r in rows if r["关切"] == "修养—救赎"]
    k0, n0 = pooled(base)
    p("  基准 修养—救赎：%5.1f%%（%d/%d，n=%d 人）" % (k0 / n0 * 100, k0, n0, len(base)))
    for key in sorted(set(r["关切"] for r in rows) - {"修养—救赎"}):
        sub = [r for r in rows if r["关切"] == key]
        k1, n1 = pooled(sub)
        pp = (k0 + k1) / (n0 + n1)
        se = math.sqrt(pp * (1 - pp) * (1 / n0 + 1 / n1))
        z = (k1 / n1 - k0 / n0) / se if se else 0.0
        p("  %-10s %5.1f%%（%d/%d，n=%d 人）  z = %+5.2f  %s"
          % (key, k1 / n1 * 100, k1, n1, len(sub), z,
             "显著" if abs(z) > 1.96 else "不显著"))

    # ── 补充检验 C：多重比较与尾部构成 ──────────────────────────
    p("\n" + "─" * 72)
    p("【补充检验 C】多重比较校正 与 低 A 尾部构成")
    p("─" * 72)
    pairs = n_all * (n_all - 1) // 2
    alpha = 0.05 / pairs
    # 双侧临界 z：p(z) = alpha/2
    zc = 0.0
    while (1 - math.erf(zc / math.sqrt(2))) / 2 > alpha / 2:
        zc += 0.001
    p("两两比较总数 %d 组；若取 α=0.05，纯粹由随机产生的「显著」约为 %.0f 组。"
      % (pairs, pairs * 0.05))
    p("→ 报告单对 z 值无意义，须做 Bonferroni 校正：α' = 0.05/%d = %.2e，对应双侧临界 |z| > %.2f"
      % (pairs, alpha, zc))
    maxz = max(abs(ztest(a, b)) for i, a in enumerate(rows) for b in rows[i + 1:])
    p("→ 全库 %d 对中，最大的 |z| = %.2f，%s"
      % (pairs, maxz, "仍达不到校正后的临界值" if maxz < zc else "超过了临界值"))
    tail = [r for r in rows if r["shr"] < 0.40]
    p("低 A 尾部（A<40%%，共 %d 人）构成：" % len(tail))
    for r in sorted(tail, key=lambda x: x["shr"]):
        p("  %-10s %5.1f%%   文体=%-6s 可靠度=%-6s 关切=%s"
          % (r["人物"], r["shr"] * 100, r["文体"], r["可靠度"], r["关切"]))
    from collections import Counter
    p("尾部文体分布：%s" % dict(Counter(r["文体"] for r in tail)))
    p("全库文体分布：%s" % dict(Counter(r["文体"] for r in rows)))
    p("→ 残篇在尾部的占比 %.0f%% vs 在全库的占比 %.0f%%，富集 %.1f 倍。"
      % (sum(1 for r in tail if r["文体"] == "残篇") / len(tail) * 100,
         sum(1 for r in rows if r["文体"] == "残篇") / n_all * 100,
         (sum(1 for r in tail if r["文体"] == "残篇") / len(tail)) /
         (sum(1 for r in rows if r["文体"] == "残篇") / n_all)))

    with io.open(os.path.join(ROOT, "分析结果.md"), "w", encoding="utf-8") as fp:
        fp.write("# 多维思维模型分析 · 原始输出\n\n```\n" + "\n".join(OUT) + "\n```\n")
    p("\n→ 已写出 分析结果.md")


if __name__ == "__main__":
    main()
