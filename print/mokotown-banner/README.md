# Baner Mokotown Music Academy — poprawny QR + plik do druku

**Cel QR:** https://www.mokotownmusic.pl (korekcja błędów H, sprawdzony dekoderem OpenCV).

## Gotowe pliki do druku (130 × 76 cm, 150 dpi, 7677 × 4488 px)
Wersja HD: oryginał powiększony 4x modelem Real-ESRGAN x4plus (6556 × 3836 px, ok. 128 dpi
realnej ostrości przy 130 cm), potem podmieniony QR i eksport do formatu druku.
- `out/mokotown-banner-130x76cm-150dpi.pdf` — do drukarni (strona dokładnie 130 × 76 cm).
- `out/mokotown-banner-130x76cm-150dpi.jpg` — ten sam obraz jako JPG (jakość 95).
- `out/banner-qr-fixed-original-size.png` — oryginalna rozdzielczość 1639 × 959, tylko z podmienionym QR (do internetu).
- `banner-source.png` — oryginał z fałszywym QR (1639 × 959 px).

## Powiększanie (upscale) — `upscale_realesrgan.py`
Samodzielna implementacja RRDBNet (bez basicsr), liczy na CPU kafelkami. Wagi:
`RealESRGAN_x4plus.pth` z https://github.com/xinntao/Real-ESRGAN/releases/tag/v0.1.0 (67 MB, nie w repo).
```bash
pip install torch pillow numpy
python3 upscale_realesrgan.py banner-source.png RealESRGAN_x4plus.pth banner-source-x4.png
python3 make_print_banner.py banner-source-x4.png --out out/
```
Najpierw powiększ oryginał z fałszywym QR, a dopiero potem podmień kod — wtedy QR jest
generowany w pełnej rozdzielczości, a nie powiększany.

## Pliki
- `qr-mokotownmusic.svg` — wektorowy QR, bezstratny w każdym rozmiarze (najlepszy dla drukarni / Canvy).
- `qr-mokotownmusic.png` — rastrowy QR, 2220×2220 px.
- `make_print_banner.py` — podmienia QR na oryginalnej grafice i zapisuje pliki do druku.

## Użycie
```bash
pip install pillow "qrcode[pil]" opencv-python-headless numpy img2pdf
python3 make_print_banner.py baner-oryginal.png --width-cm 130 --height-cm 76 --dpi 150 --out out/
```
Wynik w `out/`: PNG, JPG (q95) i PDF z osadzonym DPI oraz `banner-qr-fixed-original-size.png`
(oryginalna rozdzielczość, tylko z podmienionym QR).

Skrypt sam znajduje białą płytkę z QR w dolnym ciemnym pasku. Jeśli nie trafi,
podaj ją ręcznie: `--plate x,y,szer,wys` (piksele oryginału).

## Uwagi do druku
- Baner ma proporcje ok. 16:9, czyli pasuje do **130 × 76 cm**. Format 1300 × 76 cm (17:1)
  wymagałby nowego układu; skrypt przerywa przy niezgodnych proporcjach, chyba że podasz
  `--extend "#111111"` (dopełnia kadr kolorem tła zamiast przeprojektowywać).
- Surowy plik ~1650 px szerokości daje przy 130 cm tylko ~32 dpi; stąd krok z upscalerem.
- Minimalny bok QR na banerze oglądanym z 1–2 m: ok. 6–8 cm.
