"""Fetch the exact type families referenced by the supplied Stitch export."""
from pathlib import Path
import re
from urllib.request import Request, urlopen

FOLDER = Path(__file__).resolve().parents[1] / "static" / "fonts"
FONTS = [("instrument-sans", "Instrument+Sans:wght@400..700", "instrumentsans"),
         ("wix-madefor-display", "Wix+Madefor+Display:wght@500..700", "wixmadefordisplay"),
         ("spline-sans-mono", "Spline+Sans+Mono:wght@400..600", "splinesansmono"),
         ("material-symbols", "Material+Symbols+Outlined", None)]

if __name__ == "__main__":
    FOLDER.mkdir(parents=True, exist_ok=True)
    generated = []
    for filename, family, license_folder in FONTS:
        request = Request("https://fonts.googleapis.com/css2?family=" + family + "&display=swap",
            headers={"User-Agent": "Mozilla/5.0 Chrome/120.0.0.0 Safari/537.36"})
        css = urlopen(request, timeout=30).read().decode()
        blocks = re.findall(r"@font-face\s*\{([^}]+)\}", css)
        selected = {}
        for block in blocks:
            weight = re.search(r"font-weight:\s*([^;]+)", block).group(1).strip()
            selected[weight] = block
        if not selected:
            raise ValueError(f"No font file returned for {family}")
        for weight, block in selected.items():
            url = re.search(r"url\((https://[^)]+)\)", block).group(1)
            extension = ".woff2" if ".woff2" in url else ".ttf"
            asset = filename + "-" + weight.replace(" ", "-") + extension
            data = urlopen(url, timeout=30).read()
            (FOLDER / asset).write_bytes(data)
            block = block.replace(url, "app/static/fonts/" + asset)
            generated.append("@font-face {" + block + "}")
        license_url = (f"https://raw.githubusercontent.com/google/fonts/main/ofl/{license_folder}/OFL.txt"
                       if license_folder else "https://raw.githubusercontent.com/google/material-design-icons/master/LICENSE")
        (FOLDER / (filename + "-LICENSE.txt")).write_bytes(urlopen(license_url, timeout=30).read())
        print(filename, len(selected), "weight files")
    (FOLDER / "fonts.css").write_text("\n".join(generated), encoding="utf-8")
