# -*- coding: utf-8 -*-
"""
审查 §4.3「语录条目格式」的实际一致性

规范（v1 定义）：  语句原文。——《文献·篇名》

实测分类（句末标点允许 。？！… 」））：
  A 规范        句末标点 → ——《…》
  B 句读异常    句末不是 。？！…」）之一
  C 出处变体    —— 后不是《，而是括号或标记
  D 出处后缀    出处后还有 〔译〕/⚠️/#self-other/（转引注）  —— 这属正常，需单独统计
  E 无分隔符    条目里没有 ——
  F 标记格式    #self-other 用反引号包裹（不可机读）
  G 句首标记    条目前缀挂了 ⚠️/〔译〕（应在句末）

用 --fix 归一化：标记统一移到出处之后（顺序 〔译〕→⚠️→#self-other），
括号式出处转为《》式，去反引号，统一空格。
运行： python 审查-条目格式.py [--fix]
"""
import glob
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
SKIP = ("README", "统计总表", "工具", "升维", "分析", "建站", "审查", "坐标表")
END = "。？！…）」"
MARK = r"(?:〔译〕|〔意译〕|⚠️|`?#self-other`?)"


def files():
    for f in sorted(glob.glob(os.path.join(ROOT, "**", "*.md"), recursive=True)):
        if os.path.basename(f).startswith(SKIP) or (os.sep + "docs" + os.sep) in f:
            continue
        yield f


def entries(path):
    text = io.open(path, encoding="utf-8").read()
    cur = None
    for i, line in enumerate(text.split("\n")):
        if line.startswith("## 二、"): cur = "A"
        elif line.startswith("## 三、"): cur = "B"
        elif line.startswith("## 四、"): cur = None
        elif cur and re.match(r"^\d+\.\s", line):
            yield i, line.strip()


def split_src(body):
    """找出「出处分隔符」：那些 —— 中，其后（跳过标记后）紧接《 的那一个。
    句子内部本身含 —— 的（如「荒野之中——此即天堂」）会被跳过。"""
    poss = [m.start() for m in re.finditer("——", body)]
    for p in reversed(poss):
        tail = body[p + 2:]
        if tail.lstrip().startswith("《") or re.match(r"^\s*" + MARK + r"*\s*《", tail):
            return body[:p], tail
    return None, None


def classify(line):
    body = re.sub(r"^\d+\.\s*", "", line)
    if "`#self-other`" in body:
        return "F"
    if re.match(r"^\s*" + MARK, body):
        return "G"
    pre, tail = split_src(body)
    if pre is None:
        return "E"
    if re.search(r"——\s*。", pre):
        return "H"
    if not pre.rstrip() or pre.rstrip()[-1] not in END:
        return "B"
    if not re.match(r"^\s*" + MARK + r"*\s*《", tail) and not tail.lstrip().startswith("《"):
        return "C"
    m = re.match(r"^\s*" + MARK + r"*\s*《[^》]*》(.*)$", tail)
    return "D" if (m and m.group(1).strip()) else "A"


def normalize(line):
    num = re.match(r"^(\d+\.)\s*", line).group(1)
    body = re.sub(r"^\d+\.\s*", "", line)
    pre, tail = split_src(body)
    if pre is None:
        return line, False
    head_marks = []
    if re.match(r"^\s*" + MARK, pre):
        head_marks = [m.group(0) for m in re.finditer(MARK, pre)]
        pre = re.sub(r"^\s*" + MARK, "", pre).lstrip()
    prem = [m.group(0) for m in re.finditer(MARK, pre)]
    pre = re.sub(MARK, "", pre)
    tail = tail.lstrip()
    lead = [m.group(0) for m in re.finditer(MARK, tail[:len(tail) - len(re.sub(r"^(?:" + MARK + r")+", "", tail))])] \
        if re.match(r"^(?:" + MARK + r")+", tail) else []
    tail = re.sub(r"^(?:" + MARK + r")+", "", tail).lstrip()
    m = re.match(r"^《([^》]*)》(.*)$", tail)
    if m:
        src, after = "《%s》" % m.group(1), m.group(2)
    else:
        m2 = re.match(r"^（([^《]*)《([^》]*)》(.*?)）(.*)$", tail)
        if m2:
            src = "《%s》" % m2.group(2)
            inner = (m2.group(1) + m2.group(3)).strip()
            after = ("（%s）" % inner if inner else "") + m2.group(4)
        else:
            return line, False
    afm = [m.group(0) for m in re.finditer(MARK, after)]
    after = re.sub(MARK, "", after)
    after = re.sub(r"\s{2,}", " ", after).strip()
    marks = []
    for x in head_marks + prem + lead + afm:
        x = x.replace("`", "")
        if x not in marks:
            marks.append(x)
    pre = re.sub(r"\s+$", "", pre)
    if pre and pre[-1] not in END:
        pre += "。"
    new = "%s %s——%s" % (num, pre, src)
    if after:
        new += after if after[0] in "（(" else " " + after
    if marks:
        new += " " + "".join(marks)
    return new, new.strip() != line.strip()


def main():
    fix = "--fix" in sys.argv
    stat, samples, changed, touched = {}, {}, 0, []
    for f in files():
        lines = io.open(f, encoding="utf-8").read().split("\n")
        dirty = False
        for i, line in entries(f):
            k = classify(line)
            stat[k] = stat.get(k, 0) + 1
            samples.setdefault(k, []).append((os.path.basename(f)[:-3], line[:64]))
            if fix and k in ("B", "C", "E", "F", "G", "H"):
                new, ch = normalize(line)
                if ch:
                    lines[i] = new
                    changed += 1
                    dirty = True
        if dirty:
            io.open(f, "w", encoding="utf-8").write("\n".join(lines))
            touched.append(os.path.basename(f)[:-3])

    total = sum(stat.values())
    name = {"A": "A 规范（句读 → 《》出处）", "B": "B 句读异常", "H": "H 句末多余破折号（——。）",
            "C": "C 出处非《》式", "D": "D 出处后有附注/标记（正常）",
            "E": "E 无分隔符", "F": "F 标记带反引号", "G": "G 标记挂在句首"}
    print("=" * 76)
    print("§4.3 条目格式一致性审计" + ("　【已执行 --fix】" if fix else "　【只读】"))
    print("=" * 76)
    print("条目总数 %d\n" % total)
    for k in ["A", "B", "C", "D", "E", "F", "G", "H"]:
        v = stat.get(k, 0)
        print("  %-30s %5d 条  %5.1f%%" % (name[k], v, v / total * 100))
    print()
    for k in ["B", "C", "E", "F", "G", "H"]:
        if stat.get(k):
            print("─ %s（%d 条）样例：" % (name[k], stat[k]))
            for who, line in samples[k][:3]:
                print("    [%s] %s" % (who, line))
            print()
    if fix:
        print("→ 已归一化 %d 条，涉及 %d 个文件" % (changed, len(touched)))


if __name__ == "__main__":
    main()
