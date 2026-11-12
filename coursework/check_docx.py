"""Formatting and content checks for the generated .docx (exit 1 on failure)."""
import re, sys, zipfile
from docx import Document
from docx.shared import Cm

PATH = sys.argv[1]
fails = []


def check(ok, msg):
    print(("PASS " if ok else "FAIL ") + msg)
    if not ok:
        fails.append(msg)


z = zipfile.ZipFile(PATH)
check(z.testzip() is None, "zip container intact")
xml = z.read("word/document.xml").decode()
styles = z.read("word/styles.xml").decode()

doc = Document(PATH)
for i, s in enumerate(doc.sections):
    ok = (abs(s.page_width - Cm(21)) < 2000 and abs(s.page_height - Cm(29.7)) < 2000 and
          abs(s.left_margin - Cm(3)) < 2000 and abs(s.right_margin - Cm(1.5)) < 2000 and
          abs(s.top_margin - Cm(2)) < 2000 and abs(s.bottom_margin - Cm(2)) < 2000)
    check(ok, f"section {i}: A4 portrait, margins 3/1.5/2/2 cm")

colors = set(re.findall(r'w:color w:val="([0-9A-Fa-f]{6}|auto)"', xml + styles))
used_in_doc = set(re.findall(r'w:color w:val="([0-9A-Fa-f]{6}|auto)"', xml))
check(used_in_doc <= {"000000", "auto"}, f"document text/border colours only black {used_in_doc}")
check("w:hyperlink" not in xml, "no hyperlinks")
fonts = set(re.findall(r'w:(?:ascii|hAnsi|cs|eastAsia)="([^"]+)"', xml))
check(fonts <= {"Times New Roman"}, f"run fonts in body {fonts or '{inherit Normal}'}")
n = doc.styles["Normal"]
check(n.font.name == "Times New Roman" and n.font.size.pt == 14, "Normal: Times New Roman 14 pt")
pf = n.paragraph_format
check(pf.line_spacing == 1.5 and abs(pf.first_line_indent - Cm(1.25)) < 2000,
      "Normal: 1.5 spacing, 1.25 cm first-line indent, justified")
for h in ("Heading 1", "Heading 2"):
    st = doc.styles[h]
    check(st.font.bold and st.font.color.rgb == (0, 0, 0) and 14 <= st.font.size.pt <= 16
          and "Theme" not in st.element.xml.split("w:rFonts")[1][:200],
          f"{h}: bold black Times {st.font.size.pt} pt, no theme font/colour")

text = "\n".join(p.text for p in doc.paragraphs)
for t in doc.tables:
    for row in t.rows:
        for c in row.cells:
            text += "\n" + c.text
allowed = {"ERP", "MES", "DMZ", "TLS", "VPN", "RBAC", "SIEM", "NTP", "IP", "Telnet", "FTP", "DCS"}
latin = sorted({w for w in re.findall(r"[A-Za-z]{2,}", text) if w not in allowed})
check(not latin, f"no English words besides standard abbreviations {latin}")
for sec in range(1, 14):
    check(re.search(rf"^{sec} \S", text, re.M) is not None, f"section {sec} heading present")
figs = re.findall(r"Рисунок (\d+) –", text)
check(figs == [str(i) for i in range(1, 9)], f"figures 1..8 in order {figs}")
tabs = re.findall(r"Таблица (\d+) –", text)
check(tabs == [str(i) for i in range(1, 8)], f"tables 1..7 in order {tabs}")
check("1Г" in text and "первой группе" in text, "conclusion states group 1 and class 1Г")
print(f"\n{len(fails)} failure(s)")
sys.exit(1 if fails else 0)
