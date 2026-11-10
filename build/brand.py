"""
Beli's colours and type, in one place.

Imported by chart.py and report.py so the charts and the report look like one document.

Sampled from Beli's own assets rather than guessed: the logo at beliapp.com is #134F5C
on white, the app greys sit around #9FA197, and the site sets proxima-nova.

Two notes on what had to change, both from running the dataviz skill's validator
(scripts/validate_palette.js) rather than eyeballing:

1. #134F5C fails the validator as a *categorical* slot -- too dark for the lightness
   band, too desaturated for the chroma floor. It is used here as an **emphasis** mark
   instead: one dark accent against a light de-emphasis grey, where lightness
   separation is the mechanism. In that role the brand teal against Beli's own
   #9FA197 scores dE 31.5 normal-vision and 28.9 under protanopia, well clear of the
   15 and 8 floors. So the chart uses Beli's real colours, not an approximation.
2. #9FA197 sits at 2.62:1 against white, under the 3:1 bar. The validator calls that a
   WARN with relief required: the chart carries direct labels and the report carries a
   full table, which is the relief.

ACCENT_LIGHT is a lighter step of the same hue, validated on its own, for marks that
need to sit on the teal or carry less weight.

Proxima Nova is an Adobe Fonts licence and cannot be redistributed. Montserrat is the
closest freely-licensed geometric sans; the two static weights in assets/fonts were
instanced from Google's variable release. If they are missing the charts fall back to
Segoe UI and still render.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FONT_DIR = ROOT / "assets" / "fonts"

# --- Beli's own values -------------------------------------------------------------
TEAL = "#134f5c"          # the logo
TEAL_LIGHT = "#1393ae"    # same hue, snapped to a step that passes on its own
WASH = "#c6dce2"          # light teal, for the cluster band behind the marks
GREY = "#9fa197"          # the app greys, used as the de-emphasis mark
INK = "#1d1d1d"           # site body text
SURFACE = "#ffffff"       # Beli's surface is white, not off-white

# --- chrome ------------------------------------------------------------------------
INK_2 = "#52514e"
MUTED = "#898781"
GRID = "#ededed"          # the site's own hairline grey
AXIS = "#d2d1c9"

STACK = ["Montserrat", "Segoe UI", "DejaVu Sans", "sans-serif"]
WEB_STACK = ('Montserrat, "Proxima Nova", system-ui, -apple-system, "Segoe UI", '
             "sans-serif")


def load_fonts():
    """Register the bundled Montserrat weights with matplotlib. Safe to call twice."""
    from matplotlib import font_manager
    found = []
    for path in sorted(FONT_DIR.glob("*.ttf")):
        try:
            font_manager.fontManager.addfont(str(path))
            found.append(path.name)
        except Exception:
            pass
    return found


def rcparams():
    """Matplotlib defaults for every chart in this project."""
    load_fonts()
    return {
        "font.family": "sans-serif",
        "font.sans-serif": STACK,
        "figure.facecolor": SURFACE,
        "axes.facecolor": SURFACE,
        "text.color": INK,
    }
