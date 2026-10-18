# paper/

Scripted paper build. The text is written in Markdown (`src/`). Every number in it is a macro such as
`{{h1.S.rate|pct}}`, which `build.py` fills in from the evidence index. The script then renders a Word file and a
LaTeX/PDF file with numbered sections, captions, cross-references, IEEE-style references and appendices.

| Path | Contents |
|---|---|
| `final/` | The full paper with Appendices A–E: `Did_the_Action_Already_Happen.pdf`, `.docx` and the generated `paper.tex` |
| `src/` | Sections (`01_`…`09_`), appendices (`A1_`…`A5_`) and `meta.yaml` (title, abstract, keywords, declarations) |
| `refs/` | `bib.yaml` (references) and `refs_verified.json` (each reference checked against its source) |
| `derive.py` | Builds the main evidence index `build/numbers.json` and the data figures from `results/` and `runs/` |
| `figures_static.py` | The data-free explanatory figure (`fig_worlds.png`) |
| `exploratory/` | The two analyses that were not pre-registered: the API census (`census/`) and the horizon replay, plus robustness checks. `make_extra.py` writes `numbers_extra.json` |
| `followup/` | `derive_followup.py` (numbers for the follow-up section) and `followup_corrected.py` (the corrected follow-up analysis, see `docs/PROTOCOL_corrections.md`) |
| `figures/` | All figures, 300 dpi |

Build from the repository root after the derive steps in the main README:

```
.venv\Scripts\python paper\build.py
```

The build needs pandoc 3.1 or later and `xelatex` with the TeX Gyre fonts. It writes `build/paper.docx`,
`build/paper.tex` and `build/paper.pdf` (set `SPLIT_SUPPLEMENT = True` in `build.py` to put the appendices in a
separate `supplement.*`), and it reports any number the text references that the evidence index
lacks. Before the Word file is saved, its XML is put into the element order that the Office Open XML schema requires. The layout is a single-column
article: Times 10.5 pt, blue numbered headings, a boxed abstract, gridded tables with a shaded header row, a running
head and "Page X of Y" footers. A venue submission would move `src/` into that venue's template.
