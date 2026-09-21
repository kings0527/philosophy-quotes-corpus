# -*- coding: utf-8 -*-
"""
审查 README §4.4「两维度判定规则」的失效程度

不用重新分类，只做两件可复现的事：
  ① 度量规则的**内部冲突**：同一条目，句法判据与语义判据指向相反的比例
  ② 度量规则的**不确定区**：同时含 A 类线索与 B 类线索、两位读者会分歧的比例

判据（公开、可复核）：
  句法判据 S：条目中出现自称/自指词 我 吾 己 予 余 自
  语义线索 A：自省、修养、欲望、心性、生死 一类词
  语义线索 B：政治、社会、自然、知识、语言 一类词
"""
import glob
import io
import os
import re

ROOT = os.path.dirname(os.path.abspath(__file__))

SELF = set("我吾己予余自")
A_CUE = ["省", "修", "养", "欲", "悔", "耻", "志", "慎", "惧", "畏", "忧",
         "静", "虚", "忘", "独", "反", "心", "性", "身", "情", "意",
         "良知", "浩然", "赤子", "知足", "知止", "寡欲", "生死", "死生", "自省", "自反"]
B_CUE = ["政", "法", "君", "民", "天下", "国", "治", "乱", "礼", "伦", "群",
         "赏", "罚", "刑", "名", "是非", "言", "辩", "学", "知", "天", "道",
         "理", "气", "自然", "物", "阴阳", "五行", "制", "度", "禁", "术"]


def load():
    rows = []
    for f in sorted(glob.glob(os.path.join(ROOT, "**", "*.md"), recursive=True)):
        if os.path.basename(f).startswith(("README", "统计总表", "工具", "升维", "分析", "建站")):
            continue
        text = io.open(f, encoding="utf-8").read()
        name = os.path.basename(f)[:-3]
        cur = None
        for line in text.split("\n"):
            if line.startswith("## 二、"): cur = "A"
            elif line.startswith("## 三、"): cur = "B"
            elif line.startswith("## 四、"): cur = None
            elif cur and re.match(r"^\d+\.\s", line):
                rows.append((name, cur, line.strip()))
    return rows


def main():
    rows = load()
    tot = len(rows)
    ca = sum(1 for r in rows if r[1] == "A")
    cb = tot - ca

    has_self = [r for r in rows if SELF & set(r[2])]
    no_self = [r for r in rows if not (SELF & set(r[2]))]

    # ① 句法判据 vs 语义判据 指向相反
    conflict = []
    for name, side, line in has_self:
        a = sum(line.count(w) for w in A_CUE)
        b = sum(line.count(w) for w in B_CUE)
        if b > a and side == "A":
            conflict.append((name, side, line, a, b))
    # ② 双向线索同时出现（不确定区）
    ambigu = []
    for name, side, line in rows:
        a = sum(line.count(w) for w in A_CUE)
        b = sum(line.count(w) for w in B_CUE)
        if a > 0 and b > 0:
            ambigu.append((name, side, line, a, b))

    print("=" * 74)
    print("§4.4 判定规则 · 失效审计")
    print("=" * 74)
    print("语料条目总数 %d ｜ 现标 A %d（%.1f%%）／ 现标 B %d（%.1f%%）"
          % (tot, ca, ca / tot * 100, cb, cb / tot * 100))

    print("\n【判据一】句法线索的分布")
    print("  含自称/自指词（我吾己予余自）的条目：%d 条（%.1f%%）" % (len(has_self), len(has_self) / tot * 100))
    print("  不含的：%d 条（%.1f%%）" % (len(no_self), len(no_self) / tot * 100))
    print("  → 但 §4.4 说 A 类「主语为『我/吾/心/性』」，而 B 类包含「他人、社会、自然、语言、知识」。")
    print("     含自称词却讲外部事物的句子，被规则的两半同时认领。")

    print("\n【判据二】规则两半互相打架的条目（有自称词 + 主题词偏 B，却被标为 A）")
    print("  数量：%d 条（占 A 类的 %.1f%%）" % (len(conflict), len(conflict) / ca * 100))
    for name, side, line, a, b in conflict[:6]:
        print("   · [%s] A线索%d / B线索%d  %s" % (name, a, b, line[:46]))

    print("\n【判据三】不确定区：同时含两类线索的条目（换个人来判会分歧）")
    print("  数量：%d 条（占全库 %.1f%%）" % (len(ambigu), len(ambigu) / tot * 100))

    print("\n【判据四】`#self-other` 补丁的实际使用")
    so = [r for r in rows if "#self-other" in r[2]]
    print("  标记条目：%d 条" % len(so))
    for name, side, line in so:
        print("   · [%s｜现标 %s] %s" % (name, side, line[:48]))

    print("\n【判据五】「心／性」两字被同时当作 A 类主语和 B 类对象的例证")
    xs = [r for r in rows if ("心" in r[2] or "性" in r[2]) and r[1] == "B"]
    print("  含「心」或「性」却标为 B 的条目：%d 条" % len(xs))
    for name, side, line in xs[:5]:
        print("   · [%s] %s" % (name, line[:54]))


if __name__ == "__main__":
    main()
