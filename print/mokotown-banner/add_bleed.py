#!/usr/bin/env python3
"""
Dodaje spad do gotowego pliku banera (lustrzane odbicie krawędzi) i zapisuje JPG + PDF.
PDF ma stronę = format + spad, a TrimBox ustawiony na format netto, więc drukarnia
widzi linię cięcia bez znaczników na grafice.

Użycie:
  python3 add_bleed.py WEJSCIE.png --width-cm 130 --height-cm 76 --bleed-mm 20 --dpi 150 --out out/
"""
import argparse, os
import cv2, img2pdf, numpy as np, pikepdf
from PIL import Image

CM_PER_INCH = 2.54

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("source")
    ap.add_argument("--width-cm", type=float, default=130)
    ap.add_argument("--height-cm", type=float, default=76)
    ap.add_argument("--bleed-mm", type=float, default=20)
    ap.add_argument("--dpi", type=int, default=150)
    ap.add_argument("--out", default="out")
    a = ap.parse_args()
    Image.MAX_IMAGE_PIXELS = None

    img = np.array(Image.open(a.source).convert("RGB"))
    tw, th = round(a.width_cm / CM_PER_INCH * a.dpi), round(a.height_cm / CM_PER_INCH * a.dpi)
    if img.shape[1] != tw or img.shape[0] != th:
        img = cv2.resize(img, (tw, th), interpolation=cv2.INTER_LANCZOS4)
    b = round(a.bleed_mm / 25.4 * a.dpi)
    padded = cv2.copyMakeBorder(img, b, b, b, b, cv2.BORDER_REFLECT_101)

    os.makedirs(a.out, exist_ok=True)
    stem = f"mokotown-banner-{a.width_cm:g}x{a.height_cm:g}cm-spad{a.bleed_mm:g}mm-{a.dpi}dpi"
    jpg = os.path.join(a.out, stem + ".jpg")
    Image.fromarray(padded).save(jpg, quality=95, dpi=(a.dpi, a.dpi), subsampling=0)

    bleed_cm = a.bleed_mm / 10
    page_w_pt = (a.width_cm + 2 * bleed_cm) / CM_PER_INCH * 72
    page_h_pt = (a.height_cm + 2 * bleed_cm) / CM_PER_INCH * 72
    bleed_pt = bleed_cm / CM_PER_INCH * 72
    pdf_path = os.path.join(a.out, stem + ".pdf")
    with open(pdf_path, "wb") as f:
        f.write(img2pdf.convert(jpg, layout_fun=img2pdf.get_layout_fun((page_w_pt, page_h_pt))))
    with pikepdf.open(pdf_path, allow_overwriting_input=True) as pdf:
        page = pdf.pages[0]
        page.TrimBox = [bleed_pt, bleed_pt, page_w_pt - bleed_pt, page_h_pt - bleed_pt]
        page.BleedBox = [0, 0, page_w_pt, page_h_pt]
        pdf.save(pdf_path)
    print(f"{padded.shape[1]}x{padded.shape[0]} px = {a.width_cm + 2*bleed_cm:g}x{a.height_cm + 2*bleed_cm:g} cm "
          f"(netto {a.width_cm:g}x{a.height_cm:g} cm, spad {a.bleed_mm:g} mm) -> {jpg}, {pdf_path}")

if __name__ == "__main__":
    main()
