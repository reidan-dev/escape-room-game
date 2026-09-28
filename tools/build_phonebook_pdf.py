import csv
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
CSV_PATH = ROOT_DIR / "data" / "phonebook.csv"
OUT_HTML = ROOT_DIR / "printables" / "phonebook_directory.html"

NUM_PANELS = 8  # 4 A4 landscape sheets, each folded in half -> 8-page booklet
MARGIN_MM = 12.5

rows = [r for r in csv.DictReader(open(CSV_PATH, newline="")) if r["role"] != "special"]
rows.sort(key=lambda r: (r["last_name"].lower(), r["first_name"].lower()))
print("total entries:", len(rows))

# Split into NUM_PANELS as-equal-as-possible chunks by entry count (not by
# whole letters — a letter can span two panels, with a plain "cont'd" note
# marking the continuation, same as a real phonebook). Remainder entries are
# spread across the first few panels so sizes differ by at most 1.
n = len(rows)
base, extra = divmod(n, NUM_PANELS)
sizes = [base + 1 if i < extra else base for i in range(NUM_PANELS)]
cuts = [0]
for s in sizes:
    cuts.append(cuts[-1] + s)
panel_slices = [rows[cuts[i]:cuts[i + 1]] for i in range(NUM_PANELS)]
for i, sl in enumerate(panel_slices):
    print(f"panel {i+1}: {len(sl)} entries, {sl[0]['last_name']}.. to ..{sl[-1]['last_name']}")

DASH = "&#8212;" * 5  # em dash x5, flanking a fresh letter header

# Clue-role phone numbers get an in-character "someone already flagged this"
# mark — like a previous investigator went through this phonebook with a
# pen. Varied per entry so it reads as organic annotation, not a uniform
# system-generated tag.
COFFEE_STAIN_SVG = (
    '<svg class="stain" viewBox="0 0 60 60" xmlns="http://www.w3.org/2000/svg">'
    '<ellipse cx="30" cy="30" rx="27" ry="24" transform="rotate(-8 30 30)"/>'
    '<ellipse cx="31" cy="29" rx="19" ry="17" transform="rotate(6 31 29)"/>'
    '</svg>'
)
INK_CIRCLE_SVG = (
    '<svg class="ink-circle" viewBox="0 0 200 40" xmlns="http://www.w3.org/2000/svg">'
    '<path d="M6,20 C6,8 40,3 100,4 C165,5 195,10 194,21 '
    'C193,33 155,37 98,37 C42,37 6,32 6,20 Z"/>'
    '</svg>'
)
CLUE_MARKS = {
    "108-2693": {"highlight": True, "mark": '<span class="hw mark-asterisk">*</span>'},
    "543-6751": {"highlight": True, "mark": '<span class="hw mark-question">?</span>'},
    "030-4478": {"highlight": False, "mark": COFFEE_STAIN_SVG},
    "982-6652": {"highlight": True, "mark": '<span class="hw mark-check">chk&rsquo;d</span>'},
    "647-4402": {"highlight": False, "mark": INK_CIRCLE_SVG},
}


def render_entry(r):
    name = f'{r["last_name"]}, {r["first_name"]}'
    flag = CLUE_MARKS.get(r["phone"])
    if not flag:
        return (
            f'<div class="entry"><span class="name">{name}</span>'
            f'<span class="leader"></span><span class="num">{r["phone"]}</span></div>'
        )
    mark_html = flag["mark"]
    name_html = f'<span class="name hl-name">{name}</span>' if flag["highlight"] else f'<span class="name">{name}</span>'
    entry_html = (
        f'<div class="entry flagged">{name_html}'
        f'<span class="leader"></span><span class="num">{r["phone"]}</span></div>'
    )
    if mark_html.startswith("<svg"):
        # SVG decorations must NOT be a child of the flex `.entry` row. Two
        # separate reasons: (1) an absolutely-positioned flex-item child can
        # upset baseline-alignment height calculation, and (2) — the actual
        # bug hit here — the SVG's own class name ("stain") collided with an
        # entry-level modifier class of the same name, so `.stain { position:
        # absolute; width:22px }` was also applying to the entry div itself,
        # collapsing the whole row out of flow. Keeping the SVG as an
        # external sibling with its own unambiguous class avoids both.
        return f'<div class="flag-wrap">{mark_html}{entry_html}</div>'
    # non-SVG marks (plain <span> text) render fine as a child of .entry
    return (
        f'<div class="entry flagged">{mark_html}{name_html}'
        f'<span class="leader"></span><span class="num">{r["phone"]}</span></div>'
    )


def render_panel(panel_rows, page_num, continues_letter):
    parts = []
    current_letter = None
    for idx, r in enumerate(panel_rows):
        letter = r["last_name"][0].upper()
        if letter != current_letter:
            is_continuation = (idx == 0 and letter == continues_letter)
            if is_continuation:
                header_html = f'<div class="letter-header cont">{letter} <span class="cont-tag">cont&rsquo;d</span></div>'
            else:
                header_html = f'<div class="letter-header">{DASH} {letter} {DASH}</div>'
            parts.append(
                f'<div class="section-start">'
                f'{header_html}'
                f'{render_entry(r)}'
                f'</div>'
            )
            current_letter = letter
        else:
            parts.append(render_entry(r))
    entries_html = "\n      ".join(parts)
    header = (
        '<div class="panel-head"><h1>PHONEBOOK DIRECTORY</h1>'
        f'<div class="sub">Lastname, Firstname &mdash; Phone Number</div></div>'
        if page_num == 1 else
        '<div class="panel-head small">PHONEBOOK DIRECTORY <span class="cont">(cont&rsquo;d)</span></div>'
    )
    # A breadcrumb: someone jotted this number down in the margin on an
    # unrelated page, well away from the actual Lansang entry, as if they'd
    # heard it somewhere and were still trying to place it.
    margin_note = (
        '<div class="margin-note">030-4478???</div>'
        if page_num == 6 else ""
    )
    return f"""
  <div class="panel">
    {header}
    <div class="directory">
      {entries_html}
    </div>
    <div class="page-num">{page_num} / {NUM_PANELS}</div>
    {margin_note}
  </div>""", panel_rows[-1]["last_name"][0].upper()


sheets_html = []
last_letter = None
for i in range(0, NUM_PANELS, 2):
    left, last_letter = render_panel(panel_slices[i], i + 1, last_letter)
    if i + 1 < NUM_PANELS:
        right, last_letter = render_panel(panel_slices[i + 1], i + 2, last_letter)
    else:
        right = ""
    sheets_html.append(f'\n  <div class="sheet">{left}{right}\n  </div>')

sheets_block = "".join(sheets_html)

html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Phonebook Directory</title>
<style>
  @page {{ size: A4 landscape; margin: 0; }}
  * {{ box-sizing: border-box; }}
  body {{
    font-family: Georgia, 'Times New Roman', serif;
    color: #111;
    margin: 0;
  }}
  .sheet {{
    width: 297mm;
    height: 210mm;
    display: flex;
    page-break-after: always;
  }}
  .sheet:last-child {{ page-break-after: auto; }}
  .panel {{
    width: 148.5mm;
    height: 210mm;
    padding: {MARGIN_MM}mm;
    position: relative;
    overflow: hidden;
  }}
  .panel:first-child {{ border-right: 1px dashed #999; }}
  .panel-head {{
    text-align: center;
    border-bottom: 2px solid #000;
    padding-bottom: 5px;
    margin-bottom: 8px;
  }}
  .panel-head h1 {{
    font-size: 24px;
    letter-spacing: 1.5px;
    margin: 0;
  }}
  .panel-head .sub {{
    font-size: 10px;
    font-style: italic;
    color: #444;
    margin-top: 3px;
  }}
  .panel-head.small {{
    font-size: 14px;
    font-weight: bold;
    letter-spacing: 1px;
    padding-bottom: 4px;
  }}
  .panel-head.small .cont {{
    font-weight: normal;
    font-style: italic;
    font-size: 11px;
    color: #444;
  }}
  .directory {{
    column-count: 3;
    column-gap: 5mm;
    column-fill: auto;
    column-rule: 1px solid #ccc;
    font-size: 9px;
    line-height: 1.35;
    height: 166mm;
  }}
  .section-start {{ break-inside: avoid; }}
  .letter-header {{
    break-after: avoid;
    white-space: nowrap;
    font-weight: bold;
    font-size: 11.5px;
    letter-spacing: 1px;
    text-align: center;
    margin: 7px 0 3px;
    color: #000;
  }}
  .letter-header.cont {{
    font-weight: bold;
    font-size: 10px;
    text-align: left;
    color: #333;
    border-top: 1px solid #999;
    padding-top: 3px;
    margin: 6px 0 3px;
  }}
  .letter-header.cont .cont-tag {{
    font-weight: normal;
    font-style: italic;
    font-size: 8.5px;
    color: #666;
  }}
  .entry {{
    break-inside: avoid;
    display: flex;
    align-items: baseline;
    white-space: nowrap;
    overflow: hidden;
  }}
  .entry .name {{
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }}
  .entry .leader {{
    flex: 1;
    border-bottom: 1px dotted #999;
    margin: 0 4px 2px;
    min-width: 4px;
  }}
  .entry .num {{
    font-weight: 600;
    flex-shrink: 0;
  }}
  .page-num {{
    position: absolute;
    bottom: {MARGIN_MM - 4}mm;
    left: 0;
    right: 0;
    text-align: center;
    font-size: 9px;
    color: #555;
  }}
  .margin-note {{
    position: absolute;
    top: 8mm;
    right: 10mm;
    font-family: 'Bradley Hand', 'Noteworthy', 'Comic Sans MS', cursive;
    font-size: 15px;
    color: #b3261e;
    transform: rotate(-7deg);
    pointer-events: none;
  }}

  /* ---------- Clue-number annotations: "someone already flagged this" ---------- */
  .entry.flagged {{
    position: relative;
    overflow: visible;
  }}
  .flag-wrap {{
    position: relative;
    display: block;
  }}
  .hl-name {{
    background: rgba(255, 224, 71, 0.62);
    box-shadow: 2px 0 0 rgba(255, 224, 71, 0.62), -2px 0 0 rgba(255, 224, 71, 0.62);
    border-radius: 1px;
  }}
  .hw {{
    font-family: 'Bradley Hand', 'Noteworthy', 'Comic Sans MS', cursive;
    color: #b3261e;
    position: absolute;
    top: 50%;
    left: calc(100% + 3px);
    line-height: 1;
    white-space: nowrap;
    pointer-events: none;
    z-index: 3;
  }}
  .mark-asterisk {{
    font-size: 17px;
    transform: translateY(-65%) rotate(-8deg);
  }}
  .mark-question {{
    font-size: 14px;
    transform: translateY(-60%) rotate(6deg);
  }}
  .mark-check {{
    font-size: 10px;
    transform: translateY(-50%) rotate(-4deg);
    text-decoration: underline;
    text-decoration-style: wavy;
  }}
  .stain svg, .ink-circle svg {{ display: block; overflow: visible; }}
  .stain {{
    position: absolute;
    left: 2px;
    top: 50%;
    width: 22px;
    height: 22px;
    transform: translateY(-50%) rotate(-4deg);
    pointer-events: none;
    z-index: 1;
  }}
  .stain ellipse {{
    fill: none;
    stroke: #8a5a2b;
    stroke-width: 1.6;
    opacity: 0.4;
  }}
  .ink-circle {{
    position: absolute;
    left: -6px;
    right: -10px;
    top: 50%;
    width: calc(100% + 16px);
    height: 24px;
    transform: translateY(-50%);
    pointer-events: none;
    z-index: 3;
  }}
  .ink-circle path {{
    fill: none;
    stroke: #1d3f8f;
    stroke-width: 1.4;
    opacity: 0.75;
  }}
</style>
</head>
<body>{sheets_block}
</body>
</html>
"""

with open(OUT_HTML, "w") as f:
    f.write(html)

print("Wrote", OUT_HTML)
