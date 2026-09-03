"""Podmiana logo na banerze nr 2. Współrzędne podane dla oryginału 1642x958, skalowane przez s."""
import sys
import cv2, numpy as np
from PIL import Image

def replace_logo(img: Image.Image, logo: Image.Image, s: float, color=(20, 20, 20)) -> Image.Image:
    rgb = np.array(img.convert("RGB"))
    # 1) usuń stare logo: maska ciemnych pikseli w prostokącie starego logo, dylatacja, inpaint
    x0, y0, x1, y1 = [int(v * s) for v in (55, 55, 790, 282)]
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    sat = rgb.max(axis=2).astype(int) - rgb.min(axis=2).astype(int)
    mask = np.zeros(gray.shape, np.uint8)
    reg = (gray[y0:y1, x0:x1] < 232) & (sat[y0:y1, x0:x1] < 60)   # szare/czarne, nie pomarańczowe
    mask[y0:y1, x0:x1] = reg.astype(np.uint8) * 255
    k = max(3, int(round(5 * s))) | 1
    mask = cv2.dilate(mask, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k)))
    bgr = cv2.inpaint(cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR), mask, max(3, int(3 * s)), cv2.INPAINT_TELEA)
    out = Image.fromarray(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))
    # 2) nowe logo: przytnij do zawartości, przeskaluj do wysokości starego, wyrównaj tekst do linii "SZKOŁA"
    logo = logo.convert("RGBA")
    a = np.array(logo.getchannel("A"))
    ys, xs = np.where(a > 10)
    logo = logo.crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))
    target_h = int(round(209 * s))
    target_w = int(round(logo.width * target_h / logo.height))
    logo = logo.resize((target_w, target_h), Image.LANCZOS)
    solid = Image.new("RGBA", logo.size, color + (255,))
    solid.putalpha(logo.getchannel("A"))
    px, py = int(round(111 * s)), int(round(68 * s))
    out.paste(solid, (px, py), solid)
    return out, (px, py, target_w, target_h)

if __name__ == "__main__":
    src, logo, dst, s = sys.argv[1], sys.argv[2], sys.argv[3], float(sys.argv[4])
    Image.MAX_IMAGE_PIXELS = None
    out, box = replace_logo(Image.open(src), Image.open(logo), s)
    out.save(dst)
    print("logo placed at", box)
