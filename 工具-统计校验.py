# -*- coding: utf-8 -*-
"""
哲学统计 · 全库校验与统计工具

用途：
  1. 校验每个语录文件的「A/B 条数」与 frontmatter 声明是否一致
  2. 校验固定标题、出处覆盖率
  3. 导出 统计总表.csv（可直接用 Excel / pandas 打开做量化分析）
  4. 导出 统计总表.md（Markdown 表格，供 README 引用）

运行： python 工具-统计校验.py
"""
import os
import re
import csv
import glob

ROOT = os.path.dirname(os.path.abspath(__file__))
HEADINGS = ["## 二、对自我的认知（A类）", "## 三、对外界的认知（B类）", "## 四、语录统计"]


def get_fm(text, key):
    m = re.search(r"^{}:[ \t]*(.*)$".format(re.escape(key)), text, re.M)
    return m.group(1).strip() if m else ""


def count_section(text, start, end):
    seg = re.search(re.escape(start) + r"(.*?)" + re.escape(end), text, re.S)
    if not seg:
        return 0, []
    items = re.findall(r"^\d+\..*$", seg.group(1), re.M)
    return len(items), items


def main():
    rows = []
    problems = []
    for path in sorted(glob.glob(os.path.join(ROOT, "**", "*.md"), recursive=True)):
        if os.path.basename(path).startswith(("README", "统计总表", "工具")):
            continue
        rel = os.path.relpath(path, ROOT).replace(os.sep, "/")
        with open(path, encoding="utf-8") as fp:
            text = fp.read()

        for h in HEADINGS:
            if h not in text:
                problems.append((rel, "缺少标题：" + h))

        ca, ia = count_section(text, HEADINGS[0], HEADINGS[1])
        cb, ib = count_section(text, HEADINGS[1], HEADINGS[2])

        nosrc = [x for x in ia + ib if "《" not in x]
        if nosrc:
            problems.append((rel, "无出处条目 %d 条" % len(nosrc)))

        warn = [x for x in ia + ib if "⚠️" in x]
        warn_a = len([x for x in ia if "⚠️" in x])
        warn_b = len([x for x in ib if "⚠️" in x])
        trans = [x for x in ia + ib if "〔译〕" in x or "〔意译〕" in x]

        m = re.search(
            r"统计:\s*对自我\s*(\d+)\s*条\s*/\s*对外界\s*(\d+)\s*条\s*/\s*合计\s*(\d+)\s*条", text)
        decl = (int(m.group(1)), int(m.group(2)), int(m.group(3))) if m else None
        if decl != (ca, cb, ca + cb):
            problems.append((rel, "frontmatter 声明 %s，实际 (%d, %d, %d)" % (decl, ca, cb, ca + cb)))

        rows.append({
            "传统": rel.split("/")[0],
            "人物": get_fm(text, "人物") or rel.split("/")[-1].replace(".md", ""),
            "地域": get_fm(text, "地域"),
            "时代": get_fm(text, "时代"),
            "派别": get_fm(text, "派别"),
            "A对自我": ca,
            "B对外界": cb,
            "合计": ca + cb,
            "A占比": round(ca / (ca + cb), 3) if ca + cb else 0,
            "⚠️存疑": len(warn),
            "⚠️A": warn_a,
            "⚠️B": warn_b,
            "〔译〕": len(trans),
            "文件": rel,
        })

    rows.sort(key=lambda r: (r["传统"], -r["A占比"], r["合计"]))

    with open(os.path.join(ROOT, "统计总表.csv"), "w", encoding="utf-8-sig", newline="") as fp:
        w = csv.DictWriter(fp, fieldnames=["传统", "人物", "地域", "时代", "派别",
                                           "A对自我", "B对外界", "合计", "A占比",
                                           "⚠️存疑", "⚠️A", "⚠️B", "〔译〕", "文件"])
        w.writeheader()
        w.writerows(rows)

    ta = sum(r["A对自我"] for r in rows)
    tb = sum(r["B对外界"] for r in rows)

    lines = ["| 传统 | 人物 | 派别 | A·对自我 | B·对外界 | 合计 | A 占比 |",
             "|---|---|---|---|---|---|---|"]
    for r in rows:
        lines.append("| %s | %s | %s | %d | %d | %d | %.0f%% |" % (
            r["传统"], r["人物"], r["派别"], r["A对自我"], r["B对外界"], r["合计"], r["A占比"] * 100))
    lines.append("| **合计** | **%d 人** | — | **%d** | **%d** | **%d** | **%.0f%%** |" % (
        len(rows), ta, tb, ta + tb, ta / (ta + tb) * 100))
    with open(os.path.join(ROOT, "统计总表.md"), "w", encoding="utf-8") as fp:
        fp.write("\n".join(lines) + "\n")

    print("人数 %d ｜ A %d ｜ B %d ｜ 合计 %d ｜ 全库 A 占比 %.1f%%" % (
        len(rows), ta, tb, ta + tb, ta / (ta + tb) * 100))
    tw = sum(r["⚠️存疑"] for r in rows)
    twa = sum(r["⚠️A"] for r in rows)
    twb = sum(r["⚠️B"] for r in rows)
    tt = sum(r["〔译〕"] for r in rows)
    print("标 ⚠️ 的存疑/待核条目 %d 条（%.1f%%）｜ 标 〔译〕/〔意译〕的条目 %d 条（%.1f%%）" % (
        tw, tw / (ta + tb) * 100, tt, tt / (ta + tb) * 100))
    print("→ 剔除 ⚠️ 条目后的严格口径：A %d ／ B %d ／ 合计 %d ／ A 占比 %.1f%%" % (
        ta - twa, tb - twb, ta + tb - tw, (ta - twa) / (ta + tb - tw) * 100))
    print()
    if problems:
        print("发现 %d 个问题：" % len(problems))
        for rel, msg in problems:
            print("  -", rel, msg)
    else:
        print("校验通过：标题规范、出处覆盖率、frontmatter 条数声明 全部一致。")

    print()
    print("A 占比最高 / 最低（自我导向 vs 外向导向）")
    by_ratio = sorted(rows, key=lambda r: r["A占比"])
    print("  最高：", "、".join("%s %.0f%%" % (r["人物"], r["A占比"] * 100) for r in by_ratio[-5:][::-1]))
    print("  最低：", "、".join("%s %.0f%%" % (r["人物"], r["A占比"] * 100) for r in by_ratio[:5]))


if __name__ == "__main__":
    main()
