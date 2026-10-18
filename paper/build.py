"""Build the paper from its sources: Word (.docx), LaTeX (.tex) and PDF, all from the same text.

    python paper/build.py            (from the project root; needs pandoc and xelatex)

Sources
  paper/src/meta.yaml      title, author placeholders, abstract, keywords, declarations
  paper/src/NN_*.md        sections in file-name order; a file whose name starts with "A" opens the appendix
  paper/refs/bib.yaml      bibliography (verified entries), rendered in IEEE style
  paper/build/numbers.json every number used in the text, made by paper/derive.py from results/ (evidence index)

Markup on top of pandoc Markdown
  {{key}} / {{key|fmt}}    a number from numbers.json; fmt: pct (12.3 %), pct0, pp (signed points), int, f1, f2, f3,
                           usd (US$ 0.0012), s (seconds, 1 decimal), raw. Missing keys are rendered as ⟨key⟩ and listed.
  [@key] / [@a; @b]        citations, numbered in order of first use: [1], [2]–[4]
  # Title {#sec:label}     headings; numbers are written into the heading text (1, 1.1, A, A.1) so .docx and .tex agree
  ![caption](file){#fig:x} figures;  "Table: caption {#tbl:x}" after a pipe table
  @sec:x @fig:x @tbl:x     cross-references -> "Section 3.2", "Fig. 4", "Table 2"
  @prop:N                  "Proposition N" (propositions are numbered by hand in the theory section)
The build fails loudly on an unknown citation or cross-reference and writes build/report.json
(missing numbers, citations in order, every number used with its key) for the independent number check.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

P = Path(__file__).resolve().parent
SRC, OUT = P / "src", P / "build"
FIG = P / "figures"


# ------------------------------------------------------------------------------------------------ numbers
def fmt(v, f: str) -> str:
    if v is None:
        return "n/a"
    if f == "raw":
        return str(v)
    if f == "int":
        return f"{int(round(v)):,}"
    if f == "pct":
        return f"{100 * v:.1f}%"
    if f == "pct0":
        return f"{100 * v:.0f}%"
    if f == "word":
        w = "zero one two three four five six seven eight nine ten eleven twelve".split()
        return w[int(v)] if 0 <= int(v) < len(w) else f"{int(v):,}"
    if f == "pp":
        return f"{100 * v:+.1f} pp".replace("-", "−")
    if f == "usd":
        return f"US$ {v:.4f}" if v < 1 else f"US$ {v:.2f}"
    if f == "s":
        return f"{v:.1f} s".replace("-", "−")
    if f in ("f1", "f2", "f3"):
        return f"{v:.{f[1]}f}".replace("-", "−")
    if f == "p":
        return "< 0.001" if v < 0.001 else f"= {v:.3f}"
    return str(v)


def macros(text: str, nums: dict, used: dict, missing: list) -> str:
    def rep(m):
        key, _, f = m.group(1).partition("|")
        key = key.strip()
        if key not in nums:
            missing.append(key)
            return f"⟨{key}⟩"
        val = nums[key]["value"] if isinstance(nums[key], dict) and "value" in nums[key] else nums[key]
        s = fmt(val, f.strip() or "raw")
        used[key] = {"value": val, "shown": s, "source": nums[key].get("source") if isinstance(nums[key], dict) else None}
        return s
    return re.sub(r"\{\{([^}]+)\}\}", rep, text)


# ------------------------------------------------------------------------------------------------ bibliography
def ieee_authors(a: list[str]) -> str:
    if len(a) > 6 or "others" in a:
        return f"{a[0]} et al."
    if len(a) == 1:
        return a[0]
    if len(a) == 2:
        return f"{a[0]} and {a[1]}"
    return ", ".join(a[:-1]) + ", and " + a[-1]


def ieee(e: dict) -> str:
    au, t, y = ieee_authors(e["authors"]), e["title"], e["year"]
    kind = e["type"]
    doi = f", doi: {e['doi']}" if e.get("doi") else ""
    if kind == "preprint":
        where = f"arXiv:{e['arxiv']}" if e.get("arxiv") else e.get("venue", "preprint")
        note = f", {e['note']}" if e.get("note") else ""
        return f"{au}, “{t},” {where}, {y}{note}{doi if not e.get('arxiv') else ''}."
    if kind == "article":
        vol = f", vol. {e['volume']}" if e.get("volume") else ""
        no = f", no. {e['number']}" if e.get("number") else ""
        pp = f", pp. {e['pages'].replace('--', '–')}" if e.get("pages") else ""
        return f"{au}, “{t},” *{e['venue']}*{vol}{no}{pp}, {y}{doi}."
    if kind == "inproceedings":
        vol = f", vol. {e['volume']}" if e.get("volume") else ""
        pp = f", pp. {e['pages'].replace('--', '–')}" if e.get("pages") else ""
        return f"{au}, “{t},” in *{e['venue']}*{vol}, {y}{pp}{doi}."
    if kind == "book-chapter":
        pp = f", pp. {e['pages'].replace('--', '–')}" if e.get("pages") else ""
        return f"{au}, “{t},” in *{e['venue']}*, {y}{pp}{doi}."
    if kind == "software":
        return f"{au}, *{t}*, {y}. [Online]. Available: {e['url']}"
    if kind == "online":
        if not e.get("venue"):
            return f"{au}, “{t}.” [Online]. Available: {e['url']} (accessed {e.get('accessed', '')})."
        v = f" *{e['venue']}*."
        return f"{au}, “{t},”{v} [Online]. Available: {e['url']} (accessed {e.get('accessed', '')})."
    raise ValueError(kind)


def cite(text: str, bib: dict, order: list) -> str:
    def num(k):
        if k not in bib:
            raise SystemExit(f"unknown citation key: {k}")
        if k not in order:
            order.append(k)
        return order.index(k) + 1

    def rep(m):
        keys = [k.strip().lstrip("@") for k in m.group(1).split(";")]
        ns = sorted(num(k) for k in keys)
        parts, i = [], 0
        while i < len(ns):                                    # compress runs: [2]–[4]
            j = i
            while j + 1 < len(ns) and ns[j + 1] == ns[j] + 1:
                j += 1
            parts.append(f"[{ns[i]}]" if j - i < 2 else f"[{ns[i]}]–[{ns[j]}]")
            if 0 < j - i < 2:
                parts += [f"[{n}]" for n in ns[i + 1:j + 1]]
            i = j + 1
        return ", ".join(parts)
    return re.sub(r"\[(@[^\]]+)\]", rep, text)


# ------------------------------------------------------------------------------------------------ structure
def number(files: list[Path]) -> tuple[list[str], dict]:
    """Write section numbers into headings; collect labels for sections, figures and tables."""
    labels, out = {}, []
    sec, app = [0, 0, 0], False
    fig = tab = 0
    for f in files:
        if f.name.startswith("A") and not app:
            app, sec = True, [0, 0, 0]
        lines = f.read_text(encoding="utf-8").splitlines()
        for i, line in enumerate(lines):
            m = re.match(r"^(#{1,3}) (.*?)(\s*\{#(sec:[\w-]+)\})?\s*$", line)
            if m and not line.startswith("####") and not line.rstrip().endswith("{-}"):
                lvl = len(m.group(1))
                sec[lvl - 1] += 1
                for k in range(lvl, 3):
                    sec[k] = 0
                head = (chr(64 + sec[0]) if app else str(sec[0]))
                numtxt = ".".join([head] + [str(x) for x in sec[1:lvl]])
                if lvl == 1 and app:
                    shown = f"Appendix {numtxt}."
                elif lvl == 1:
                    shown = f"{numtxt}."
                else:
                    shown = numtxt
                if m.group(4):
                    labels[m.group(4)] = ("Appendix " if app and lvl == 1 else ("Appendix " if app else "Section ")) + numtxt
                lines[i] = f"{m.group(1)} {shown} {m.group(2)} {{-}}"
                continue
            mf = re.search(r"\{#(fig:[\w-]+)([^}]*)\}", line)
            if mf and line.startswith("!["):
                fig += 1
                labels[mf.group(1)] = f"Fig. {fig}"
                attrs = mf.group(2).strip()
                lines[i] = line.replace("![", f"![**Fig. {fig}.** ", 1).replace(mf.group(0), "{" + attrs + "}" if attrs else "")
                continue
            mt = re.match(r"^Table: (.*?)\s*\{#(tbl:[\w-]+)\}\s*$", line)
            if mt:
                tab += 1
                labels[mt.group(2)] = f"Table {tab}"
                lines[i] = f"Table: **Table {tab}.** {mt.group(1)}"
        out.append("\n".join(lines))
    return out, labels


def xref(text: str, labels: dict) -> str:
    def rep(m):
        k = m.group(1)
        if k.startswith("prop:"):
            return f"Proposition {k.split(':')[1]}"
        if k not in labels:
            raise SystemExit(f"unknown cross-reference: @{k}")
        return labels[k]
    return re.sub(r"@((?:sec|fig|tbl|prop):[\w-]+)", rep, text)


def widths(text: str) -> str:
    """Give every pipe table a separator whose dash counts follow the longest cell of each column, so pandoc's
    relative column widths (used for wide tables in .docx and .tex) fit the content instead of being equal."""
    lines = text.split("\n")
    out, i = [], 0
    while i < len(lines):
        if (i + 1 < len(lines) and lines[i].lstrip().startswith("|")
                and re.match(r"^\s*\|(\s*:?-{3,}:?\s*\|)+\s*$", lines[i + 1])):
            j = i + 2
            while j < len(lines) and lines[j].lstrip().startswith("|"):
                j += 1
            rows = [lines[i]] + lines[i + 2:j]
            cells = [[c.strip() for c in r.strip().strip("|").split("|")] for r in rows]
            n = len(cells[0])
            mx = [max(len(re.sub(r"[*`$]", "", r[k])) if k < len(r) else 0 for r in cells) for k in range(n)]
            mx = [min(max(m, 4), 60) for m in mx]
            out += [lines[i], "|" + "|".join("-" * m for m in mx) + "|"] + lines[i + 2:j]
            i = j
            continue
        out.append(lines[i])
        i += 1
    return "\n".join(out)


# ------------------------------------------------------------------------------------------------ outputs
LATEX_HEADER = r"""
\usepackage{fontspec}
\setmainfont{TeX Gyre Termes}[Scale=1.05]
\setsansfont{TeX Gyre Heros}
\setmonofont{DejaVu Sans Mono}[Scale=0.82]
\usepackage[letterpaper,margin=0.85in,headheight=14pt,headsep=0.2in,footskip=0.38in]{geometry}
\usepackage{booktabs}
\usepackage{colortbl}
\definecolor{cvblue}{HTML}{2E74B5}
\definecolor{cvdark}{HTML}{1F4D78}
\definecolor{cvdeep}{HTML}{1F4E79}
\definecolor{cvbox}{HTML}{8EA9C1}
\definecolor{cvfill}{HTML}{EEF3F8}
\definecolor{cvgrid}{HTML}{A6A6A6}
\definecolor{cvhead}{HTML}{DCE6F1}
\definecolor{cvgrey}{HTML}{595959}
\usepackage{caption}
\captionsetup{font=small,labelformat=empty,skip=4pt,justification=justified,singlelinecheck=false}
\usepackage{microtype}
\usepackage{xurl}
\usepackage{titlesec}
\titleformat{\section}{\fontsize{14}{17}\selectfont\bfseries\color{cvblue}}{}{0pt}{}
\titleformat{\subsection}{\fontsize{12.5}{15}\selectfont\bfseries\color{cvblue}}{}{0pt}{}
\titleformat{\subsubsection}{\normalsize\bfseries\color{cvdark}}{}{0pt}{}
\titlespacing*{\section}{0pt}{12pt plus 2pt minus 2pt}{5pt}
\titlespacing*{\subsection}{0pt}{9pt plus 2pt minus 2pt}{4pt}
\titlespacing*{\subsubsection}{0pt}{8pt plus 2pt minus 2pt}{4pt}
\usepackage{float}
\linespread{1.03}
\setlength{\parindent}{0pt}
\setlength{\parskip}{4pt plus 1pt}
\setlength{\emergencystretch}{3em}
\setlength{\textfloatsep}{12pt plus 2pt minus 2pt}
\setlength{\intextsep}{12pt plus 2pt minus 2pt}
\renewcommand{\arraystretch}{1.12}
\arrayrulecolor{cvgrid}
\usepackage{etoolbox}
\def\tablefont{\fontsize{8.5}{10.4}\selectfont}
\AtBeginEnvironment{longtable}{\tablefont}
\usepackage{fancyhdr}
\usepackage{lastpage}
\fancypagestyle{cave}{\fancyhf{}%
  \fancyhead[R]{\fontsize{9}{11}\selectfont\itshape\color{cvgrey}RUNNINGHEAD}%
  \fancyfoot[C]{\fontsize{9}{11}\selectfont\color{cvgrey}Page \thepage\ of \pageref*{LastPage}}%
  \renewcommand{\headrule}{{\color{cvbox}\hrule height 0.4pt}}\renewcommand{\footrulewidth}{0pt}}
\pagestyle{cave}
\AtBeginDocument{\thispagestyle{cave}}
\fancypagestyle{plain}{\pagestyle{cave}}
\usepackage[most]{tcolorbox}
\renewenvironment{abstract}{\begin{tcolorbox}[enhanced,colback=cvfill,colframe=cvbox,boxrule=0.5pt,arc=0pt,
  left=6pt,right=6pt,top=5pt,bottom=5pt,fontupper=\fontsize{10.5}{12}\selectfont]%
  {\bfseries\color{cvdeep}ABSTRACT}\par\vspace{2pt}}{\end{tcolorbox}}
\makeatletter
\@ifundefined{Highlighting}{}{\RecustomVerbatimEnvironment{Highlighting}{Verbatim}{commandchars=\\\{\},fontsize=\small}}
\renewcommand{\@maketitle}{\newpage\null\vspace{-0.6em}%
  \begin{center}{\fontsize{16}{20}\selectfont\bfseries\@title\par}\vskip 12pt
  {\@author\par}\vskip 2pt{\fontsize{11}{14}\selectfont\@date\par}\end{center}%
  \vskip 2pt{\color{cvdeep}\hrule height 0.8pt}\vskip 10pt}
\makeatother
"""


def _balanced(t: str, i: int) -> int:
    """Index just after the brace group that starts at t[i] == '{'."""
    d = 0
    for j in range(i, len(t)):
        if t[j] == "{":
            d += 1
        elif t[j] == "}":
            d -= 1
            if d == 0:
                return j + 1
    raise ValueError("unbalanced braces")


def twocolumn(tex: str) -> str:
    """Pandoc's single-column LaTeX -> a two-column conference layout: longtables become full-width table*
    floats, wide figures become figure*, narrow ones fill one column, code blocks span both columns."""
    out, pos = [], 0
    while True:
        a = tex.find("\\begin{longtable}", pos)
        if a < 0:
            out.append(tex[pos:])
            break
        out.append(tex[pos:a])
        b = tex.index("\\end{longtable}", a)
        block = tex[a:b]
        k = block.index("[]") + 2
        spec_end = _balanced(block, k)
        spec = block[k + 1:spec_end - 1].replace("\\columnwidth", "\\textwidth")
        rest = block[spec_end:]
        cap = ""
        if "\\caption{" in rest:
            c0 = rest.index("\\caption{")
            c1 = _balanced(rest, c0 + 8)
            cap = rest[c0:c1]
            rest = rest[:c0] + rest[c1:]
            rest = rest.replace("\\tabularnewline", "", 1) if rest.lstrip().startswith("\\tabularnewline") else rest
        head = rest.split("\\endfirsthead")[0] if "\\endfirsthead" in rest else ""
        body = rest.split("\\endlastfoot")[1] if "\\endlastfoot" in rest else rest
        size = "\\scriptsize" if "The census:" in cap else "\\small"
        place = "p" if "The census:" in cap else "!tbp"
        out.append("\\begin{table*}[" + place + "]\\centering" + size + "\n" + cap + "\n\\begin{tabular}{" + spec + "}\n"
                   + head.strip() + "\n" + body.strip() + "\n\\bottomrule\n\\end{tabular}\n\\end{table*}")
        pos = b + len("\\end{longtable}")
    tex = "".join(out)

    def fig(m):
        w = float(m.group(2) or 1)
        inner = m.group(0)
        if w <= 0.65:
            inner = re.sub(r"width=[0-9.]*\\textwidth", "width=\\\\columnwidth", inner)
            return inner.replace("\\begin{figure}", "\\begin{figure}[!tbp]", 1)
        return inner.replace("\\begin{figure}", "\\begin{figure*}[!tbp]", 1).replace("\\end{figure}", "\\end{figure*}")
    tex = re.sub(r"\\begin\{figure\}(.*?)\\end\{figure\}",
                 lambda m: fig(type("M", (), {"group": lambda self, i: (m.group(0) if i == 0 else
                     (re.search(r"width=([0-9.]+)\\textwidth", m.group(0)).group(1)
                      if re.search(r"width=([0-9.]+)\\textwidth", m.group(0)) else "1"))})()),
                 tex, flags=re.S)
    tex = re.sub(r"\\begin\{Shaded\}(.*?)\\end\{Shaded\}",
                 lambda m: "\\begin{figure*}[!tbp]\\small\n\\begin{Shaded}" + m.group(1) + "\\end{Shaded}\n\\end{figure*}",
                 tex, flags=re.S)
    return tex


def docx_schema_order(d) -> None:
    """Put children of a few elements into the order the OOXML schema requires; pandoc 3.1 emits some
    (math delimiters, matrix columns, list paragraphs) out of order, and Word is strict about it."""
    from docx.oxml.ns import qn
    M = "{http://schemas.openxmlformats.org/officeDocument/2006/math}"
    orders = {
        qn("w:pPr"): ["pStyle", "keepNext", "keepLines", "pageBreakBefore", "framePr", "widowControl", "numPr",
                      "suppressLineNumbers", "pBdr", "shd", "tabs", "suppressAutoHyphens", "kinsoku", "wordWrap",
                      "overflowPunct", "topLinePunct", "autoSpaceDE", "autoSpaceDN", "bidi", "adjustRightInd",
                      "snapToGrid", "spacing", "ind", "contextualSpacing", "mirrorIndents", "suppressOverlap", "jc",
                      "textDirection", "textAlignment", "textboxTightWrap", "outlineLvl", "divId", "cnfStyle",
                      "rPr", "sectPr", "pPrChange"],
        M + "dPr": ["begChr", "sepChr", "endChr", "grow", "shp", "ctrlPr"],
        M + "mcPr": ["count", "mcJc"],
    }
    for tag, order in orders.items():
        for el in d.element.body.iter(tag):
            kids = list(el)
            names = [k.tag.split("}")[1] for k in kids]
            if all(n in order for n in names):
                srt = sorted(kids, key=lambda k: order.index(k.tag.split("}")[1]))
                if srt != kids:
                    for k in kids:
                        el.remove(k)
                    for k in srt:
                        el.append(k)


def docx_table_widths(d, total_twips: int = 10080) -> None:
    """Size table columns from their content so that short numeric columns never wrap letter by letter."""
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    for tbl in d.element.body.iter(qn("w:tbl")):
        rows = tbl.findall(qn("w:tr"))
        n = max(len(r.findall(qn("w:tc"))) for r in rows) if rows else 0
        if n == 0:
            continue
        longest, total = [1] * n, [1] * n
        for r in rows:
            for j, tc in enumerate(r.findall(qn("w:tc"))[:n]):
                txt = "".join(t.text or "" for t in tc.iter(qn("w:t")))
                longest[j] = max(longest[j], max((len(w) for w in txt.split()), default=1))
                total[j] = max(total[j], len(txt))
        need = [(l + 1) * 95 for l in longest]                  # ~9 pt Times: 95 twips per character
        want = [max(nd, min(t, 38) * 95) for nd, t in zip(need, total)]
        scale = total_twips / sum(want)
        if scale < 1:                                           # shrink only the wrappable surplus
            surplus = [w - nd for w, nd in zip(want, need)]
            room = total_twips - sum(need)
            want = [nd + (sp * room / sum(surplus) if sum(surplus) and room > 0 else 0)
                    for nd, sp in zip(need, surplus)]
        else:
            want = [w * scale for w in want]
        want = [int(w) for w in want]
        tp = tbl.find(qn("w:tblPr"))
        for old in tp.findall(qn("w:tblW")) + tp.findall(qn("w:tblLayout")):
            tp.remove(old)
        tw = OxmlElement("w:tblW"); tw.set(qn("w:w"), str(sum(want))); tw.set(qn("w:type"), "dxa"); tp.append(tw)
        lay = OxmlElement("w:tblLayout"); lay.set(qn("w:type"), "fixed"); tp.append(lay)
        order = ["tblStyle", "tblpPr", "tblOverlap", "bidiVisual", "tblStyleRowBandSize", "tblStyleColBandSize",
                 "tblW", "jc", "tblCellSpacing", "tblInd", "tblBorders", "shd", "tblLayout", "tblCellMar",
                 "tblLook", "tblCaption", "tblDescription"]
        kids = sorted(list(tp), key=lambda e: order.index(e.tag.split("}")[1]) if e.tag.split("}")[1] in order else 99)
        for e in list(tp):
            tp.remove(e)
        for e in kids:
            if e.tag == qn("w:jc") and e.get(qn("w:val")) == "start":
                e.set(qn("w:val"), "left")
            tp.append(e)
        grid = tbl.find(qn("w:tblGrid"))
        if grid is not None:
            for g in list(grid):
                grid.remove(g)
            for w in want:
                g = OxmlElement("w:gridCol"); g.set(qn("w:w"), str(w)); grid.append(g)
        for r in rows:
            for j, tc in enumerate(r.findall(qn("w:tc"))[:n]):
                pr = tc.find(qn("w:tcPr"))
                if pr is None:
                    pr = OxmlElement("w:tcPr"); tc.insert(0, pr)
                for old in pr.findall(qn("w:tcW")):
                    pr.remove(old)
                w = OxmlElement("w:tcW"); w.set(qn("w:w"), str(want[j])); w.set(qn("w:type"), "dxa"); pr.insert(0, w)


def docx_twocolumn(d, ncols: int = 2) -> None:
    """Conference layout for the Word file: title block full width, body in two columns, tables, wide figures
    and the pseudocode in full-width continuous sections (the Word analogue of table*/figure*)."""
    import copy
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    EMU = 914400
    col_w = int(3.35 * EMU)
    body = d.element.body
    final = body.find(qn("w:sectPr"))
    els = [e for e in body if e is not final]

    def style(e):
        ps = e.find(qn("w:pPr")) if e.tag == qn("w:p") else None
        st = ps.find(qn("w:pStyle")) if ps is not None else None
        return st.get(qn("w:val")) if st is not None else ""

    def wide_img(e):
        ext = e.find(".//" + qn("wp:extent"))
        if ext is None:
            return False
        cx, cy = int(ext.get("cx")), int(ext.get("cy"))
        if cx <= int(0.66 * 6.5 * EMU):                       # narrow figure: fits one column
            if cx > col_w:
                f = col_w / cx
                for x in e.iter(qn("wp:extent")):
                    x.set("cx", str(col_w)); x.set("cy", str(int(cy * f)))
                for x in e.iter("{http://schemas.openxmlformats.org/drawingml/2006/main}ext"):
                    x.set("cx", str(col_w)); x.set("cy", str(int(cy * f)))
            return False
        return True

    borders = final.find(qn("w:pgBorders"))
    margins = final.find(qn("w:pgMar"))

    def sect(n, first=False):
        """A schema-ordered sectPr: type, pgSz, pgMar, pgBorders, cols (Word rejects any other order)."""
        sp = OxmlElement("w:sectPr")
        if not first:
            t = OxmlElement("w:type"); t.set(qn("w:val"), "continuous"); sp.append(t)
        sz = OxmlElement("w:pgSz"); sz.set(qn("w:w"), "12240"); sz.set(qn("w:h"), "15840"); sp.append(sz)
        pm = OxmlElement("w:pgMar")
        for k in ("top", "right", "bottom", "left"):
            pm.set(qn("w:" + k), margins.get(qn("w:" + k)) if margins is not None and margins.get(qn("w:" + k)) else "1224")
        pm.set(qn("w:header"), "720"); pm.set(qn("w:footer"), "720"); pm.set(qn("w:gutter"), "0")
        sp.append(pm)
        if borders is not None:
            sp.append(copy.deepcopy(borders))
        c = OxmlElement("w:cols"); c.set(qn("w:num"), str(n)); c.set(qn("w:space"), "360"); sp.append(c)
        return sp

    if ncols == 1:                                              # single column: one clean section only
        body.replace(final, sect(1, True))
        return
    cols = []
    for i, e in enumerate(els):
        st = style(e)
        if st in ("Title", "Author", "Subtitle", "Date"):
            cols.append(1)
        elif e.tag == qn("w:tbl") or st in ("SourceCode",):
            cols.append(1)
        elif st == "TableCaption" and i + 1 < len(els) and els[i + 1].tag == qn("w:tbl"):
            cols.append(1)
        elif st == "CaptionedFigure" and wide_img(e):
            cols.append(1)
        elif st == "ImageCaption" and i > 0 and cols[i - 1] == 1 and style(els[i - 1]) == "CaptionedFigure":
            cols.append(1)
        else:
            cols.append(2)

    first = True
    for i, e in enumerate(els):
        if i + 1 < len(els) and cols[i + 1] != cols[i]:
            sp = sect(cols[i], first)
            first = False
            if e.tag == qn("w:p"):
                pPr = e.find(qn("w:pPr"))
                if pPr is None:
                    pPr = OxmlElement("w:pPr"); e.insert(0, pPr)
                pPr.append(sp)
            else:                                               # a table ends the section: carrier paragraph
                p = OxmlElement("w:p"); pPr = OxmlElement("w:pPr")
                sz = OxmlElement("w:spacing"); sz.set(qn("w:after"), "0"); sz.set(qn("w:line"), "120")
                sz.set(qn("w:lineRule"), "exact"); pPr.append(sz); pPr.append(sp); p.append(pPr)
                e.addnext(p)
    final_new = sect(cols[-1], first)
    body.replace(final, final_new)


def fix_ooxml(path: Path) -> None:
    """Final schema clean-up of the .docx package. pandoc 3.1 writes a few elements out of schema order (and a
    stray '>' in one style); Word may refuse such files as corrupt, so every part is normalised here."""
    import zipfile
    import lxml.etree as ET
    W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    M = "{http://schemas.openxmlformats.org/officeDocument/2006/math}"
    orders = {
        W + "style": ["name", "aliases", "basedOn", "next", "link", "autoRedefine", "hidden", "uiPriority",
                      "semiHidden", "unhideWhenUsed", "qFormat", "locked", "personal", "personalCompose",
                      "personalReply", "rsid", "pPr", "rPr", "tblPr", "trPr", "tcPr", "tblStylePr"],
        W + "pPr": ["pStyle", "keepNext", "keepLines", "pageBreakBefore", "framePr", "widowControl", "numPr",
                    "suppressLineNumbers", "pBdr", "shd", "tabs", "suppressAutoHyphens", "kinsoku", "wordWrap",
                    "overflowPunct", "topLinePunct", "autoSpaceDE", "autoSpaceDN", "bidi", "adjustRightInd",
                    "snapToGrid", "spacing", "ind", "contextualSpacing", "mirrorIndents", "suppressOverlap", "jc",
                    "textDirection", "textAlignment", "textboxTightWrap", "outlineLvl", "divId", "cnfStyle",
                    "rPr", "sectPr", "pPrChange"],
        W + "tcPr": ["cnfStyle", "tcW", "gridSpan", "hMerge", "vMerge", "tcBorders", "shd", "noWrap", "tcMar",
                     "textDirection", "tcFitText", "vAlign", "hideMark"],
        M + "dPr": ["begChr", "sepChr", "endChr", "grow", "shp", "ctrlPr"],
        M + "mcPr": ["count", "mcJc"],
        M + "rPr": ["lit", "nor", "scr", "sty", "brk", "aln"],
        W + "settings": """writeProtection view zoom removePersonalInformation removeDateAndTime doNotDisplayPageBoundaries displayBackgroundShape printPostScriptOverText printFractionalCharacterWidth printFormsData embedTrueTypeFonts embedSystemFonts saveSubsetFonts saveFormsData mirrorMargins alignBordersAndEdges bordersDoNotSurroundHeader bordersDoNotSurroundFooter gutterAtTop hideSpellingErrors hideGrammaticalErrors activeWritingStyle proofState formsDesign attachedTemplate linkStyles stylePaneFormatFilter stylePaneSortMethod documentType mailMerge revisionView trackRevisions doNotTrackMoves doNotTrackFormatting documentProtection autoFormatOverride styleLockTheme styleLockQFSet defaultTabStop autoHyphenation consecutiveHyphenLimit hyphenationZone doNotHyphenateCaps showEnvelope summaryLength clickAndTypeStyle defaultTableStyle evenAndOddHeaders bookFoldRevPrinting bookFoldPrinting bookFoldPrintingSheets drawingGridHorizontalSpacing drawingGridVerticalSpacing displayHorizontalDrawingGridEvery displayVerticalDrawingGridEvery doNotUseMarginsForDrawingGridOrigin drawingGridHorizontalOrigin drawingGridVerticalOrigin doNotShadeFormData noPunctuationKerning characterSpacingControl printTwoOnOne strictFirstAndLastChars noLineBreaksAfter noLineBreaksBefore savePreviewPicture doNotValidateAgainstSchema saveInvalidXml ignoreMixedContent alwaysShowPlaceholderText doNotDemarcateInvalidXml saveXmlDataOnly useXSLTWhenSaving saveThroughXslt showXMLTags alwaysMergeEmptyNamespace updateFields hdrShapeDefaults footnotePr endnotePr compat docVars rsids mathPr attachedSchema themeFontLang clrSchemeMapping doNotIncludeSubdocsInStats doNotAutoCompressPictures forceUpgrade captions readModeInkLockDown smartTagType schemaLibrary shapeDefaults doNotEmbedSmartTags decimalSymbol listSeparator""".split(),
    }

    def reorder(root):
        for tag, order in orders.items():
            for el in root.iter(tag):
                kids = [k for k in el if isinstance(k.tag, str)]
                names = [ET.QName(k).localname for k in kids]
                if not all(n in order for n in names):
                    continue
                srt = sorted(kids, key=lambda k: order.index(ET.QName(k).localname))
                if srt != kids:
                    for k in kids:
                        el.remove(k)
                    for k in srt:
                        el.append(k)
        for el in root.iter(W + "rPr"):                         # stray character content inside rPr
            if el.text and el.text.strip():
                el.text = None
            for k in el:
                if isinstance(k.tag, str) and k.tail and k.tail.strip():
                    k.tail = None
        for el in root.iter(W + "nsid", W + "tmpl"):            # ST_LongHexNumber: exactly 8 hex digits
            v = el.get(W + "val")
            if v is not None and len(v) < 8:
                el.set(W + "val", v.zfill(8))
        for el in root.iter(M + "rPr"):                         # m:nor and m:sty are alternatives
            if el.find(M + "nor") is not None:
                for k in el.findall(M + "sty") + el.findall(M + "scr"):
                    el.remove(k)

    tmp = path.with_suffix(".tmp.docx")
    with zipfile.ZipFile(path) as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename.startswith("word/") and item.filename.endswith(".xml"):
                root = ET.fromstring(data)
                reorder(root)
                data = ET.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)
            zout.writestr(item, data)
    tmp.replace(path)


FIG_SCALE = 0.85          # all figures at 85 % of their source width
SPLIT_SUPPLEMENT = False   # True: appendices go to a separate supplement.* file
RUNNING_HEAD = "Did the Action Already Happen? Reliable Recovery for AI Agents Under Ambiguous Tool Outcomes"
BLUE, DARKBLUE, DEEP, BOXLINE, BOXFILL, GRIDLINE, HEADFILL, GREY = (
    "2E74B5", "1F4D78", "1F4E79", "8EA9C1", "EEF3F8", "A6A6A6", "DCE6F1", "595959")


def _border(tag: str, sides, val="single", sz="6", color=BOXLINE, space="6"):
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    b = OxmlElement(tag)
    for side in sides:
        e = OxmlElement(f"w:{side}")
        e.set(qn("w:val"), val); e.set(qn("w:sz"), sz); e.set(qn("w:color"), color)
        if space is not None:
            e.set(qn("w:space"), space)
        b.append(e)
    return b


def _ppr_set(par, child):
    """Replace (or add) one pPr child; fix_ooxml() puts the children back into schema order."""
    ppr = par._p.get_or_add_pPr()
    for old in ppr.findall(child.tag):
        ppr.remove(old)
    ppr.append(child)


def _shade(color: str):
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    e = OxmlElement("w:shd")
    e.set(qn("w:val"), "clear"); e.set(qn("w:color"), "auto"); e.set(qn("w:fill"), color)
    return e


def _field(par, instr: str, size, color):
    """Append a PAGE / NUMPAGES field to a paragraph."""
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.shared import RGBColor
    for kind in ("begin", "instr", "separate", "text", "end"):
        r = par.add_run()
        r.font.size, r.font.color.rgb, r.font.name = size, RGBColor.from_string(color), "Times New Roman"
        if kind == "instr":
            t = OxmlElement("w:instrText"); t.set(qn("xml:space"), "preserve"); t.text = instr; r._r.append(t)
        elif kind == "text":
            r.text = "1"
        else:
            f = OxmlElement("w:fldChar"); f.set(qn("w:fldCharType"), kind); r._r.append(f)


def grid_tables(tex: str) -> str:
    """pandoc longtables -> the reference paper's table look: full light-grey grid, a dark rule on top and a shaded,
    bold header row."""
    out, pos = [], 0
    while True:
        a = tex.find("\\begin{longtable}", pos)
        if a < 0:
            out.append(tex[pos:])
            return "".join(out)
        b = tex.index("\\end{longtable}", a)
        out.append(tex[pos:a])
        t = tex[a:b]
        t = t.replace("[]{@{}", "[]{|", 1)
        t = re.sub(r"\}@\{\}\}", "}|}", t, count=1)
        t = t.replace("}\n  >{", "}|\n  >{")
        ncol = t[:t.find("\\caption") if "\\caption" in t else len(t)].count("p{(")
        t = t.replace("(\\columnwidth - ", f"(\\columnwidth - 2\\tabcolsep - {0.4 * (ncol + 1) + 0.5:.1f}pt - ")
        top = ("\\noalign{\\global\\arrayrulewidth=1.1pt}\\arrayrulecolor{cvdeep}\\hline"
               "\\noalign{\\global\\arrayrulewidth=0.4pt}\\arrayrulecolor{cvgrid}\\rowcolor{cvhead}")
        t = t.replace("\\toprule\\noalign{}", top).replace("\\midrule\\noalign{}", "\\hline")
        t = t.replace("\\bottomrule\\noalign{}\n\\endlastfoot", "\\endlastfoot")
        t = t.replace("\\begin{minipage}[b]{\\linewidth}\\raggedright", "\\begin{minipage}[b]{\\linewidth}\\raggedright\\bfseries")
        if "\\endlastfoot" in t:
            head, body = t.split("\\endlastfoot", 1)
            body = re.sub(r" \\\\\s*\n", " \\\\\\\\ \\\\hline\n", body)
            if not body.rstrip().endswith("\\hline"):
                body = body.rstrip() + " \\\\ \\hline\n"
            t = head + "\\endlastfoot" + body
        out.append(t)
        pos = b


def style_docx(path: Path, head: str = RUNNING_HEAD) -> None:
    """House style of the reference paper: Letter, 1-inch margins, Times New Roman 12 pt justified with 1.33 line
    spacing, blue numbered headings, a boxed and shaded abstract, gridded tables with a shaded header row, a running
    head and a "Page X of Y" footer."""
    from docx import Document
    from docx.enum.style import WD_STYLE_TYPE
    from docx.enum.text import WD_ALIGN_PARAGRAPH as AL
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.shared import Inches, Pt, RGBColor
    d = Document(str(path))
    st = {x.name: x for x in d.styles}

    # page: Letter, 1-inch margins, no page border, running head and footer
    for sec in d.sections:
        sec.page_width, sec.page_height = Inches(8.5), Inches(11)
        sec.left_margin = sec.right_margin = sec.top_margin = sec.bottom_margin = Inches(0.85)
        sec.header_distance = sec.footer_distance = Inches(0.42)
        sec.gutter = Inches(0)
        for old in sec._sectPr.findall(qn("w:pgBorders")):
            sec._sectPr.remove(old)
        hp = sec.header.paragraphs[0]
        hp.text = ""
        r = hp.add_run(head)
        r.font.size, r.font.italic, r.font.name = Pt(9), True, "Times New Roman"
        r.font.color.rgb = RGBColor.from_string(GREY)
        hp.alignment = AL.RIGHT
        _ppr_set(hp, _border("w:pBdr", ["bottom"], sz="4", space="4"))
        fp = sec.footer.paragraphs[0]
        fp.text = ""
        fp.alignment = AL.CENTER
        for piece in ("Page ", "PAGE", " of ", "NUMPAGES"):
            if piece in ("PAGE", "NUMPAGES"):
                _field(fp, piece, Pt(9), GREY)
            else:
                r = fp.add_run(piece)
                r.font.size, r.font.name = Pt(9), "Times New Roman"
                r.font.color.rgb = RGBColor.from_string(GREY)

    def fmt_style(name, size, bold=None, italic=None, color=None, align=None, before=None, after=None, line=None,
                  keep=None):
        s = st.get(name)
        if s is None:
            return None
        if name != "Source Code":
            s.font.name = "Times New Roman"
        s.font.size = Pt(size)
        s.font.bold, s.font.italic = bold, italic
        if color:
            s.font.color.rgb = RGBColor.from_string(color)
        for c in s.element.iter(qn("w:color")):               # drop theme colours that override ours
            for a in ("w:themeColor", "w:themeShade", "w:themeTint"):
                c.attrib.pop(qn(a), None)
        for f in s.element.iter(qn("w:rFonts")):              # and theme fonts
            for a in ("w:asciiTheme", "w:hAnsiTheme", "w:eastAsiaTheme", "w:cstheme"):
                f.attrib.pop(qn(a), None)
        pf = s.paragraph_format
        if align is not None:
            pf.alignment = align
        if before is not None:
            pf.space_before = Pt(before)
        if after is not None:
            pf.space_after = Pt(after)
        if line is not None:
            pf.line_spacing = line
        if keep is not None:
            pf.keep_with_next = keep
        return s

    J = AL.JUSTIFY
    for n in ("Normal", "Body Text", "First Paragraph"):
        fmt_style(n, 10.5, align=J, before=0, after=2.5, line=1.0)
    fmt_style("Block Text", 10.5, align=J, before=2, after=4, line=1.05)
    fmt_style("Compact", 8.5, align=AL.LEFT, before=0, after=0, line=1.0)
    fmt_style("Title", 16, bold=True, color="000000", align=AL.CENTER, before=0, after=12, line=1.25)
    fmt_style("Author", 11, align=AL.CENTER, before=0, after=2, line=1.15)
    fmt_style("Date", 11, align=AL.CENTER, before=2, after=10, line=1.15)
    fmt_style("Abstract Title", 11, bold=True, color=DEEP, align=AL.LEFT, before=0, after=0, line=1.15)
    fmt_style("Abstract", 10, align=J, before=0, after=0, line=1.05)
    fmt_style("Heading 1", 14, bold=True, color=BLUE, align=AL.LEFT, before=12, after=5, line=1.1, keep=True)
    fmt_style("Heading 2", 12.5, bold=True, color=BLUE, align=AL.LEFT, before=9, after=4, line=1.1, keep=True)
    fmt_style("Heading 3", 10.5, bold=True, color=DARKBLUE, align=AL.LEFT, before=6, after=3, line=1.1, keep=True)
    fmt_style("Image Caption", 9.5, italic=False, align=J, before=2, after=6, line=1.0)
    fmt_style("Table Caption", 9.5, italic=False, align=J, before=5, after=3, line=1.0, keep=True)
    fmt_style("Captioned Figure", 12, align=AL.CENTER, before=6, after=3, line=1.0, keep=True)
    fmt_style("Source Code", 8.5, align=AL.LEFT, before=3, after=8, line=1.0)
    for name in ("Abstract", "Abstract Title"):                # the abstract may break across pages
        ppr = st[name].element.find(qn("w:pPr"))
        if ppr is not None and name == "Abstract":
            for tag in ("w:keepNext", "w:keepLines"):
                for e in ppr.findall(qn(tag)):
                    ppr.remove(e)
    lc = d.styles.add_style("List Compact", WD_STYLE_TYPE.PARAGRAPH)   # tight lists in body-text size;
    lc.base_style = st["Compact"]                                     # "Compact" itself stays for tables
    lc.font.size = Pt(10.5)
    lc.paragraph_format.alignment = J
    lc.paragraph_format.space_after = Pt(2)
    lc.paragraph_format.line_spacing = 1.0

    paras = d.paragraphs
    in_refs = False
    authors = [p for p in paras if p.style is not None and p.style.name == "Author"]
    for i, p in enumerate(authors):                            # name bold 13 pt, the other lines 11 pt
        for r in p.runs:
            if i == 0:
                r.font.bold, r.font.size = True, Pt(13)
    dates = [p for p in paras if p.style is not None and p.style.name == "Date"]
    rule_par = dates[-1] if dates else (authors[-1] if authors else None)
    if rule_par is not None:                                   # the rule under the author block
        _ppr_set(rule_par, _border("w:pBdr", ["bottom"], sz="8", color=DEEP, space="4"))
    for p in paras:
        sname = p.style.name if p.style is not None else ""
        if sname == "Compact":
            p.style = lc
        if sname == "Source Code":                          # token character styles carry their own size
            for r in p.runs:
                r.font.size = Pt(8.5)
        if sname in ("Abstract Title", "Abstract"):
            _ppr_set(p, _border("w:pBdr", ["top", "left", "bottom", "right"]))
            _ppr_set(p, _shade(BOXFILL))
            ind = OxmlElement("w:ind"); ind.set(qn("w:left"), "120"); ind.set(qn("w:right"), "120")
            _ppr_set(p, ind)
            if sname == "Abstract Title":
                for r in p.runs:
                    r.text = r.text.upper()
        if p.text.startswith("Keywords:"):
            p.paragraph_format.left_indent = p.paragraph_format.right_indent = Pt(6)
            p.paragraph_format.space_before, p.paragraph_format.space_after = Pt(10), Pt(12)
            for r in p.runs:
                r.font.size = Pt(10)
        if sname == "Heading 1":
            in_refs = p.text.strip() == "References"
            continue
        if in_refs and re.match(r"^\[\d+\]\s", p.text):        # IEEE list: hanging number, 10.5 pt
            pf = p.paragraph_format
            pf.left_indent, pf.first_line_indent = Pt(27), Pt(-27)
            pf.space_before, pf.space_after, pf.line_spacing = Pt(0), Pt(2), 1.0
            pf.alignment = AL.LEFT
            tabs = OxmlElement("w:tabs"); t = OxmlElement("w:tab")
            t.set(qn("w:val"), "left"); t.set(qn("w:pos"), "540"); tabs.append(t)
            _ppr_set(p, tabs)
            for r in p.runs:
                r.font.size = Pt(9.5)
            if p.runs:                                          # "[n] text" -> "[n]<tab>text"
                r0 = p.runs[0]
                r0.text = re.sub(r"^(\[\d+\])\s+", "\\1\t", r0.text, count=1)

    # tables: full grid in light grey, shaded header row under a dark top rule, bold header text
    for tbl in d.tables:
        tp = tbl._tbl.tblPr
        for old in tp.findall(qn("w:tblBorders")):
            tp.remove(old)
        tp.append(_border("w:tblBorders", ["top", "left", "bottom", "right", "insideH", "insideV"],
                          sz="4", color=GRIDLINE, space=None))
        mar = OxmlElement("w:tblCellMar")
        for side, w in (("top", "22"), ("left", "70"), ("bottom", "22"), ("right", "70")):
            e = OxmlElement(f"w:{side}"); e.set(qn("w:w"), w); e.set(qn("w:type"), "dxa"); mar.append(e)
        for old in tp.findall(qn("w:tblCellMar")):
            tp.remove(old)
        tp.append(mar)
        if not tbl.rows:
            continue
        for cell in tbl.rows[0].cells:
            pr = cell._tc.get_or_add_tcPr()
            for old in pr.findall(qn("w:shd")) + pr.findall(qn("w:tcBorders")):
                pr.remove(old)
            b = _border("w:tcBorders", ["top"], sz="12", color=DEEP, space=None)
            for side in ("left", "bottom", "right"):
                e = OxmlElement(f"w:{side}"); e.set(qn("w:val"), "single"); e.set(qn("w:sz"), "4")
                e.set(qn("w:color"), GRIDLINE); b.append(e)
            pr.append(b)
            pr.append(_shade(HEADFILL))
            for par in cell.paragraphs:
                for r in par.runs:
                    r.font.bold = True
    body_el = d.element.body                                   # the long census table in 7.5 pt, as in the PDF
    prev = None
    for el in body_el:
        if el.tag == qn("w:tbl") and prev is not None and "The census:" in prev:
            for t in el.iter(qn("w:sz")):
                t.set(qn("w:val"), "15")
            for r in el.iter(qn("w:r")):
                rpr = r.find(qn("w:rPr"))
                if rpr is None:
                    rpr = OxmlElement("w:rPr"); r.insert(0, rpr)
                if rpr.find(qn("w:sz")) is None:
                    sz = OxmlElement("w:sz"); sz.set(qn("w:val"), "15"); rpr.append(sz)
        if el.tag == qn("w:p"):
            prev = "".join(t.text or "" for t in el.iter(qn("w:t")))
    docx_table_widths(d, 9936)
    docx_schema_order(d)
    d.save(str(path))
    fix_ooxml(path)


def render(stem: str, front: dict, body: str, head: str, au: dict) -> None:
    """Markdown -> <stem>.docx (house style) and <stem>.tex -> <stem>.pdf (xelatex)."""
    md = "---\n" + yaml.safe_dump(front, allow_unicode=True, sort_keys=False) + "---\n\n" + body
    (OUT / f"{stem}.md").write_text(md, encoding="utf-8")
    common = ["pandoc", f"{stem}.md", "--from", "markdown+pipe_tables+tex_math_dollars+implicit_figures",
              "--resource-path", f".:{FIG}"]
    subprocess.run(common + ["-o", f"{stem}.docx"], cwd=OUT, check=True)
    style_docx(OUT / f"{stem}.docx", head)
    (OUT / f"{stem}_header.tex").write_text(LATEX_HEADER.replace("RUNNINGHEAD", head), encoding="utf-8")
    subprocess.run(common + ["-s", "-o", f"{stem}.tex", "-H", f"{stem}_header.tex", "-V", "fontsize=10pt",
                             "-V", "documentclass=article", "-V", "colorlinks=true"], cwd=OUT, check=True)
    tex = (OUT / f"{stem}.tex").read_text(encoding="utf-8").replace("\\usepackage{lmodern}\n", "")
    if au.get("name"):                                       # one centred author block instead of pandoc's \and columns
        sm = "\\fontsize{11}{14}\\selectfont "
        blk = "{\\fontsize{13}{16}\\selectfont\\bfseries " + au["name"] + "}"
        if au.get("affiliation"):
            blk += "\\\\[3pt]{" + sm + au["affiliation"] + "}"
        if au.get("email"):
            blk += "\\\\{" + sm + au["email"] + "}"
        if au.get("orcid"):
            blk += "\\\\{" + sm + "ORCID: " + au["orcid"] + "}"
        tex = re.sub(r"\\author\{.*?\}\n(?=\\date)", lambda m: "\\author{" + blk + "}\n", tex, count=1, flags=re.S)
    tex = grid_tables(tex)
    tex = re.sub(r"Available:\s+(https?://\S+?)(\s|$)", lambda m: "Available: \\url{" + m.group(1) + "}" + m.group(2), tex)
    (OUT / f"{stem}.tex").write_text(tex, encoding="utf-8")
    for _ in range(2):
        r = subprocess.run(["xelatex", "-interaction=nonstopmode", "-halt-on-error", f"{stem}.tex"], cwd=OUT,
                           capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stdout[-3000:])
        raise SystemExit(f"xelatex failed for {stem}")


def main() -> None:
    OUT.mkdir(exist_ok=True)
    meta = yaml.safe_load((SRC / "meta.yaml").read_text(encoding="utf-8"))
    bib = yaml.safe_load((P / "refs" / "bib.yaml").read_text(encoding="utf-8"))
    nf = OUT / "numbers.json"
    nums = json.loads(nf.read_text(encoding="utf-8")) if nf.exists() else {}
    for xf in (P / "exploratory" / "numbers_extra.json",       # exploratory analyses (API census, horizon replay)
               P / "followup" / "numbers_followup.json"):      # pre-registered follow-up study
        if xf.exists():
            nums.update(json.loads(xf.read_text(encoding="utf-8")))
    files = sorted(f for f in SRC.glob("*.md"))
    parts, labels = number(files)
    used, missing, order = {}, [], []
    body = "\n\n".join(parts)
    abstract = meta["abstract"]
    body = xref(body, labels)
    abstract = macros(abstract, nums, used, missing)
    body = macros(body, nums, used, missing)
    body = cite(body, bib, order)
    body = widths(body)
    body = re.sub(r"width=(\d+)%", lambda m: f"width={round(int(m.group(1)) * FIG_SCALE)}%", body)
    # references and the main/appendix split: references go after the main text, before the appendix
    refs = "\n\n".join(f"[{i + 1}] {ieee(bib[k])}" for i, k in enumerate(order))
    m = re.search(r"^# Appendix A", body, flags=re.M)
    ref_block = ("\n\n# References {-}\n\n```{=latex}\n\\begingroup\\small\\linespread{1.08}\\selectfont\\setlength{\\parskip}{3pt}\\everypar{\\hangindent=2.4em\\hangafter=1}\n```\n\n::: {.references}\n" + refs
                 + "\n:::\n\n```{=latex}\n\\endgroup\n```\n\n")
    body = body[:m.start()] + ref_block + body[m.start():] if m else body + ref_block
    decl = "\n\n".join(f"**{k}:** {v}" for k, v in (meta.get("declarations") or {}).items())
    decl = macros(decl, nums, used, missing)
    if decl:
        body = body.replace("# References {-}", "# Declarations {-}\n\n" + decl + "\n\n# References {-}", 1)
    au = meta.get("author") or {}
    au_lines = [x for x in (au.get("name"), au.get("affiliation"), au.get("email"),
                            ("ORCID: " + au["orcid"]) if au.get("orcid") else None) if x]
    for f in FIG.glob("*.png"):
        shutil.copy(f, OUT / f.name)
    m = re.search(r"^# Appendix A", body, flags=re.M)
    main_body, app_body = (body[:m.start()], body[m.start():]) if (m and SPLIT_SUPPLEMENT) else (body, "")
    kw = f"**Keywords:** {'; '.join(meta['keywords'])}\n\n" if meta.get("keywords") else ""
    front = {"title": meta["title"], "author": au_lines or meta.get("authors"), "date": meta.get("date"),
             "abstract": abstract, "lang": "en-US", "link-citations": False}
    render("paper", front, kw + main_body, RUNNING_HEAD, au)
    if app_body:
        sfront = {"title": "Supplementary Material for “" + meta["title"] + "”",
                  "author": au_lines or meta.get("authors"), "date": meta.get("date"), "lang": "en-US",
                  "link-citations": False}
        note = ("This supplement contains Appendices A–E of the paper. Section, figure, table and reference "
                "numbers continue those of the main paper; numbers in square brackets refer to its reference list.\n\n")
        render("supplement", sfront, note + app_body, "Supplementary Material · Did the Action Already Happen?", au)
    report = {"missing_numbers": sorted(set(missing)), "citations_in_order": order, "numbers_used": used,
              "labels": labels}
    (OUT / "report.json").write_text(json.dumps(report, indent=1, ensure_ascii=False, default=str), encoding="utf-8")
    print(f"built paper.* (docx, tex, pdf){' and supplement.*' if SPLIT_SUPPLEMENT else ''} in {OUT}; {len(order)} references, {len(used)} numbers, "
          f"{len(set(missing))} missing numbers")


if __name__ == "__main__":
    main()
    sys.exit(0)
