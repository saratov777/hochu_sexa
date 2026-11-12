# MyHandwriting — Russian single-stroke handwriting font

Built from one scanned page of handwriting (`source/handwriting-scan.png`). Every
glyph was extracted from the scan as **pen centerlines** (skeletons), not traced ink
outlines. Nothing was taken from an existing font.

## Files

| File | What it is |
|---|---|
| `dist/MyHandwriting-Regular.ttf` | Installable TrueType font (centerlines stroked with a round pen, 45/1000 em) |
| `dist/MyHandwriting-Regular.otf` | Same font as OpenType/CFF |
| `dist/MyHandwriting-SingleStroke.svg` | **True single-stroke master**: SVG font whose glyphs are open centerline paths (stroke, never fill). Works with Inkscape's *Hershey Text* extension for plotters, laser engraving and CNC |
| `dist/MyHandwriting-SingleStroke-Sheet.svg` | The same centerlines as a viewable, editable drawing: one named group per glyph, with baseline, x-height and advance-width guides |
| `dist/MyHandwriting-Source.ufo` | Editable font source (FontForge, Glyphs, FontLab, RoboFont). Each glyph's `lib` also stores its centerline as `com.myhandwriting.centerline` |
| `dist/MyHandwriting-Specimen.pdf` | Specimen: original paragraphs, alphabets, digits, punctuation, new sentences, scan-vs-font comparison, single-stroke master |
| `tools/` | Reproducible pipeline: scan → centerlines → fonts → specimen → checks |

## Why there are two representations

TrueType and OpenType can only describe **filled closed contours**. A font file cannot
contain an open, zero-width stroke that a text renderer would draw with a pen. The
TTF and OTF are therefore *expanded* versions of the centerlines: each centerline is
offset by half the pen width with round caps and joins, and the results are merged.
They look like the pen line, but they are outline fonts, not single-stroke fonts.

The single-stroke geometry lives in `MyHandwriting-SingleStroke.svg`, the sheet SVG
and the UFO glyph libs. It has 289 open strokes and 6 closed loops in total (drawn
ovals such as о, 0 and %). There are no double contours.

## Installing

- **Windows:** right-click the `.ttf` and choose *Install* (or *Install for all users*).
- **macOS:** double-click the `.otf` or `.ttf` and choose *Install Font* in Font Book.
- **Linux:** copy the font to `~/.local/share/fonts/` and run `fc-cache -f`.

Install either the TTF or the OTF, not both. In applications the family name is
**MyHandwriting**.

### Natural variation (contextual alternates)

The scan contains several written versions of и, а, в, у and of every digit. The font
switches between them automatically depending on the previous letter, so repeated
letters and numbers such as "1111" do not look stamped.

- **LibreOffice, browsers, InDesign, macOS apps:** this is on by default.
- **Microsoft Word:** Font → Advanced → tick *Use Contextual Alternates*.
- **CSS:** `font-feature-settings: "calt" 1;` (on by default). `salt` forces the first variant.

## Single-stroke use (plotter / engraving / CNC)

**Inkscape Hershey Text:**

1. Copy `MyHandwriting-SingleStroke.svg` into Inkscape's `extensions/svg_fonts/` folder.
   On Linux this is `~/.config/inkscape/extensions/svg_fonts/`, or the `share/inkscape/extensions/svg_fonts` folder of the install.
2. Open *Extensions → Text → Hershey Text*.
3. Choose *Other (enter name or file path)* and enter `MyHandwriting-SingleStroke`, or
   the full path to the `.svg` file.

The output is open paths with no fill, which a plotter draws once.

Any other tool can read the `d` attribute of each `<glyph>`. Units are 1000 per em,
y points up, the baseline is at y = 0, and `horiz-adv-x` gives the advance width.

## Editing

- **Shapes:** edit the centerlines in `MyHandwriting-SingleStroke-Sheet.svg`, or the UFO
  outlines in a font editor.
- **Pen thickness:** rebuild with `python3 tools/build.py --pen 60`. The default is 45,
  which is the measured ink width of the scan.
- **Glyph regions:** each glyph's area in the scan, and baseline overrides, are in
  `tools/glyphmap.py`.

## Rebuilding from the scan

```
pip install opencv-python-headless numpy scipy scikit-image fonttools ufoLib2 ufo2ft \
            pyclipper pillow uharfbuzz opentype-sanitizer
python3 tools/extract.py      # scan -> build/centerlines_px.json (+ tools/debug_sheet.py overlays)
python3 tools/build.py        # -> SVG master, sheet, UFO, TTF, OTF
python3 tools/specimen.py     # -> PDF via headless Chrome (env CHROME=... to override)
python3 tools/validate.py     # quality checks
```

### How the centerlines are extracted

1. Ink is assigned to a glyph by connected component, so neighbouring letters are not
   picked up.
2. The crop is upsampled 4×, thresholded and skeletonised.
3. The skeleton is turned into a graph and short spurs are pruned.
4. At every junction, the branches that continue each other most straight are paired.
   This lets a pen line pass through a crossing as one stroke instead of breaking into pieces.
5. Faint breaks are re-joined when the gap continues the stroke direction. Specks are
   dropped, but the dots of ё/Ё, the breve of й/Й and punctuation dots are kept.
6. The strokes are smoothed and fitted with cubic Béziers. Sharp turns are kept as cusps.

## Accuracy notes and approximations

- **Letters are not joined.** Every letter comes from the isolated alphabet rows. The
  connecting strokes between letters in your paragraphs are not reconstructed, because
  a font cannot reproduce them faithfully without many more samples. Spacing is set
  tight on the slanted axis instead. Words read as your handwriting, but they look
  written letter by letter.
- **Sizes were normalised to how you write in sentences.** In the alphabet rows,
  capitals are 2.07× the x-height. In your paragraphs they are about 2.35×, and the
  font uses 2.35×. Digits use 1.9× the x-height and punctuation 0.75× the punctuation
  row, both measured from "18:45" and "шапка?" in the text.
- **The baseline is evened out.** Letters that sit on the line keep 20% of the row's
  natural bounce. щ uses a measured baseline because its row bends sharply.
- **У, Ф and Д have no descenders**, matching the uppercase row in this sample.
- **Derived characters** were not written in the scan and are built from sampled
  marks: ' and ’ (half of "), “ ” „ (shifted "), – (shortened —) and … (three dots).
  They are marked `*` in the sheet and have `derivedFrom` in the UFO.
- **Scan resolution limits detail.** The lowercase x-height is about 16 px. Very small
  features are smoothed, and stroke order and direction are inferred, so they may
  differ from how you actually wrote them.
- **Strokes broken by faint ink** stay separate where re-joining was not safe: the top
  bar of Г and parts of т and «. They render correctly but are separate paths.
- **Word spacing is wide** (633/1000 em) because that is the median gap in the paragraphs.
  Reduce it with letter or word spacing in your application if you prefer.
- **No kerning table.** Spacing comes from each glyph's extent along the 25° slant.
- **Latin letters are not included**, by design. Applications show them in a fallback font.
