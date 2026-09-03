#!/usr/bin/env python3
"""
Delikatna korekta koloru banera: mniej pomarańczowa skóra + minimalnie chłodniejszy ton całości.
  python3 grade_cooler.py WEJSCIE.png WYJSCIE.png [--skin 0.22] [--cool 0.025]
"""
import argparse
import cv2, numpy as np
from PIL import Image

def grade(rgb: np.ndarray, skin_desat=0.25, skin_hue_shift=-3.0, cool=0.03) -> np.ndarray:
    img = rgb.astype(np.float32) / 255.0
    hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)            # H 0..360, S 0..1, V 0..1
    h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    # maska skóry: odcień pomarańczowo-czerwony, umiarkowane nasycenie (pomija plamy farby i ikony)
    # skóra: H 12-30 (pomarańczowe plamy, ikony i żółty pasek mają H 32-37 i zostają nietknięte)
    hm = np.clip(np.minimum(h - 10, 31 - h) / 3.0, 0, 1)
    sm = np.clip((s - 0.2) / 0.15, 0, 1)
    vm = np.clip((v - 0.15) / 0.1, 0, 1)
    mask = hm * sm * vm
    mask = cv2.GaussianBlur(mask, (0, 0), max(1.0, rgb.shape[1] / 1500))
    # skóra: mniej nasycenia, odcień lekko w stronę czerwieni (od pomarańczu)
    s2 = s * (1 - skin_desat * mask)
    h2 = (h + skin_hue_shift * mask) % 360
    hsv2 = np.stack([h2, s2, v], axis=-1)
    out = cv2.cvtColor(hsv2, cv2.COLOR_HSV2RGB)
    # globalnie chłodniej: odrobinę mniej czerwieni, odrobinę więcej niebieskiego
    out[..., 0] *= (1 - cool)
    out[..., 2] *= (1 + cool)
    return (np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8), mask

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("src"); ap.add_argument("dst")
    ap.add_argument("--skin", type=float, default=0.25)
    ap.add_argument("--cool", type=float, default=0.03)
    ap.add_argument("--mask-out")
    a = ap.parse_args()
    Image.MAX_IMAGE_PIXELS = None
    rgb = np.array(Image.open(a.src).convert("RGB"))
    out, mask = grade(rgb, skin_desat=a.skin, cool=a.cool)
    Image.fromarray(out).save(a.dst)
    if a.mask_out:
        Image.fromarray((mask * 255).astype(np.uint8)).save(a.mask_out)
    print("ok", out.shape[1], "x", out.shape[0], "skin mask coverage %.1f%%" % (100 * (mask > 0.5).mean()))
