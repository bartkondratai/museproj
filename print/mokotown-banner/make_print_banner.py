#!/usr/bin/env python3
"""
Podmiana kodu QR na banerze Mokotown Music Academy i przygotowanie pliku do druku.

Użycie:
  python3 make_print_banner.py ORYGINAL.png [--width-cm 130] [--height-cm 76] [--dpi 150]
                               [--url https://www.mokotownmusic.pl] [--out out/]
                               [--extend "#111111"]

Co robi:
  1. Znajduje białą "płytkę" z kodem QR w dolnym, ciemnym pasku grafiki.
  2. Zamalowuje ją i wkleja nowy, działający kod QR (korekcja błędów H).
  3. Sprawdza dekoderem OpenCV, że nowy QR odczytuje się poprawnie.
  4. Skaluje całość do zadanego rozmiaru w cm przy zadanym DPI
     i zapisuje PNG + PDF + JPG (z osadzoną rozdzielczością).

Wymaga: pillow, qrcode, opencv-python-headless, numpy
"""
import argparse
import os
import sys

import cv2
import numpy as np
import qrcode
from PIL import Image, ImageDraw
from qrcode.constants import ERROR_CORRECT_H

CM_PER_INCH = 2.54


def make_qr(url: str, size_px: int) -> Image.Image:
    qr = qrcode.QRCode(error_correction=ERROR_CORRECT_H, box_size=10, border=0)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    # NEAREST — moduły muszą pozostać ostre, bez rozmycia
    return img.resize((size_px, size_px), Image.NEAREST)


def find_qr_plate(img: Image.Image):
    """Zwraca (x, y, w, h) białej płytki z QR w dolnej części grafiki."""
    rgb = np.array(img.convert("RGB"))
    h, w = rgb.shape[:2]
    y0 = int(h * 0.55)
    region = rgb[y0:, :, :]
    gray = cv2.cvtColor(region, cv2.COLOR_RGB2GRAY)
    _, white = cv2.threshold(gray, 215, 255, cv2.THRESH_BINARY)
    # domknięcie: zlewa moduły QR z płytką w jedną bryłę
    k = max(3, int(min(w, h) * 0.012)) | 1
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (k, k))
    white = cv2.morphologyEx(white, cv2.MORPH_CLOSE, kernel)
    n, labels, stats, _ = cv2.connectedComponentsWithStats(white, connectivity=8)
    best = None
    for i in range(1, n):
        x, y, bw, bh, area = stats[i]
        if bw < w * 0.05 or bh < h * 0.08:
            continue
        ratio = bw / bh
        if not (0.8 <= ratio <= 1.25):
            continue
        fill = area / float(bw * bh)
        if fill < 0.5:
            continue
        score = area
        if best is None or score > best[0]:
            best = (score, x, y + y0, bw, bh)
    if best is None:
        return None
    _, x, y, bw, bh = best
    return int(x), int(y), int(bw), int(bh)


def replace_qr(img: Image.Image, url: str, plate=None) -> tuple[Image.Image, tuple]:
    img = img.convert("RGB")
    if plate is None:
        plate = find_qr_plate(img)
    if plate is None:
        sys.exit("Nie znaleziono płytki z kodem QR. Podaj ją ręcznie: --plate x,y,w,h")
    x, y, w, h = plate
    side = min(w, h)
    x = x + (w - side) // 2
    y = y + (h - side) // 2
    draw = ImageDraw.Draw(img)
    radius = max(4, side // 14)
    draw.rounded_rectangle([x, y, x + side, y + side], radius=radius, fill="white")
    margin = max(4, int(side * 0.07))
    inner = side - 2 * margin
    qr = make_qr(url, inner)
    img.paste(qr, (x + margin, y + margin))
    return img, (x, y, side, side)


def verify(img: Image.Image, url: str, box) -> bool:
    x, y, s, _ = box
    pad = s // 4
    crop = img.crop((max(0, x - pad), max(0, y - pad), x + s + pad, y + s + pad))
    arr = cv2.cvtColor(np.array(crop), cv2.COLOR_RGB2BGR)
    data, _, _ = cv2.QRCodeDetector().detectAndDecode(arr)
    return data == url


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("source")
    ap.add_argument("--url", default="https://www.mokotownmusic.pl")
    ap.add_argument("--width-cm", type=float, default=130)
    ap.add_argument("--height-cm", type=float, default=76)
    ap.add_argument("--dpi", type=int, default=150)
    ap.add_argument("--out", default="out")
    ap.add_argument("--plate", help="x,y,w,h płytki QR w pikselach oryginału (opcjonalnie)")
    ap.add_argument("--extend", help="kolor tła; dopełnia kadr do zadanych proporcji zamiast przerywać")
    args = ap.parse_args()

    Image.MAX_IMAGE_PIXELS = None
    src = Image.open(args.source)
    plate = tuple(int(v) for v in args.plate.split(",")) if args.plate else None
    fixed, box = replace_qr(src, args.url, plate)
    if not verify(fixed, args.url, box):
        sys.exit("Nowy QR nie odczytuje się poprawnie — przerwano.")
    print(f"QR podmieniony w polu x={box[0]} y={box[1]} bok={box[2]} px, odczyt OK: {args.url}")

    os.makedirs(args.out, exist_ok=True)
    fixed.save(os.path.join(args.out, "banner-qr-fixed-original-size.png"))

    target_w = round(args.width_cm / CM_PER_INCH * args.dpi)
    target_h = round(args.height_cm / CM_PER_INCH * args.dpi)
    src_ratio = fixed.width / fixed.height
    tgt_ratio = target_w / target_h
    print(f"Źródło: {fixed.width}x{fixed.height} px (proporcje {src_ratio:.3f}); "
          f"cel: {target_w}x{target_h} px = {args.width_cm}x{args.height_cm} cm @ {args.dpi} dpi "
          f"(proporcje {tgt_ratio:.3f})")
    eff_dpi = fixed.width / (args.width_cm / CM_PER_INCH)
    print(f"Efektywna rozdzielczość źródła przy tej szerokości: {eff_dpi:.0f} dpi")

    if abs(src_ratio - tgt_ratio) / tgt_ratio > 0.03:
        if not args.extend:
            sys.exit("Proporcje grafiki nie pasują do zadanego formatu. "
                     "Użyj --extend KOLOR, aby dopełnić kadr, albo popraw wymiary.")
        scale = min(target_w / fixed.width, target_h / fixed.height)
        inner = fixed.resize((round(fixed.width * scale), round(fixed.height * scale)), Image.LANCZOS)
        canvas = Image.new("RGB", (target_w, target_h), args.extend)
        canvas.paste(inner, ((target_w - inner.width) // 2, (target_h - inner.height) // 2))
        final = canvas
    else:
        final = fixed.resize((target_w, target_h), Image.LANCZOS)

    stem = f"mokotown-banner-{args.width_cm:g}x{args.height_cm:g}cm-{args.dpi}dpi"
    dpi = (args.dpi, args.dpi)
    final.save(os.path.join(args.out, stem + ".png"), dpi=dpi)
    final.save(os.path.join(args.out, stem + ".jpg"), quality=95, dpi=dpi, subsampling=0)
    final.save(os.path.join(args.out, stem + ".pdf"), resolution=args.dpi)
    print("Zapisano:", ", ".join(f"{stem}.{e}" for e in ("png", "jpg", "pdf")), "w", args.out)


if __name__ == "__main__":
    main()
