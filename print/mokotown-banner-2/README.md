# Baner Mokotown nr 2 — nowe logo, poprawny QR, plik do druku 130 × 76 cm

## Pliki wejściowe
- `banner-source.png` — oryginał (1642 × 958 px, stare logo, fałszywy QR).
- `logo-mokotown.png` — poprawne logo (3000 × 1500 px, przezroczyste tło).

## Proces
1. Powiększenie 4x Real-ESRGAN: `../mokotown-banner/upscale_realesrgan.py` → 6568 × 3832 px.
2. Podmiana logo: `replace_logo.py POWIEKSZONY.png logo-mokotown.png WYNIK.png 4`
   (stare logo usuwane maską + inpaint, nowe logo dopasowane wysokością do starego,
   wordmark wyrównany do linii „SZKOŁA MUZYCZNA DLA KAŻDEGO”).
3. QR + eksport: `../mokotown-banner/make_print_banner.py WYNIK.png --out out/`
   (płytka QR na różowym polu w lewym dolnym rogu wykrywana automatycznie).

## Gotowe pliki (`out/`)
- `mokotown-banner-130x76cm-150dpi.pdf` — do drukarni, strona 130 × 76 cm.
- `mokotown-banner-130x76cm-150dpi.jpg` — ten sam obraz jako JPG (jakość 95).
- `mokotown-banner-130x76cm-spad20mm-150dpi.pdf` / `.jpg` — wersja ze spadem 20 mm
  (strona 134 × 80 cm, TrimBox 130 × 76 cm), zrobiona `../mokotown-banner/add_bleed.py`.
