# The API census {#sec:censustable}

@tbl:census lists the 52 coded APIs. "Key" records whether the examined create operation has a server-side key, and its documented retention. "partial" marks the near-keys discussed in @sec:census, which I do not count as keys. "Lookup by tag" is the best documented way to find an object by the value of the tag field: an exact filter or query (*exact*), a search documented as lagged or fuzzy (*search*), only scanning a list of recent objects (*list scan*), or *none*. "Undo" records whether the effect can be undone through the API. The released table also holds whether the tag field is hidden from end users, the coder's notes, and a link to every documentation page relied on. Documentation was read in October 2026, and vendors change their APIs, so individual entries may have changed since.

```{=latex}
\begingroup\def\tablefont{\fontsize{7.5}{9}\selectfont}\renewcommand{\arraystretch}{0.95}
```

{{table.census}}

Table: The census: write contracts of 52 APIs, coded from vendor documentation. Class K: server-side key; A: tag field with exact lookup; A−: tag field with only lagged search or list scanning; C: no usable tag field or no lookup. {#tbl:census}

```{=latex}
\endgroup
```
