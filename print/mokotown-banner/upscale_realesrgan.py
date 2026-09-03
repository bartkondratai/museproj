"""Real-ESRGAN x4plus (RRDBNet) inference on CPU with tiling. No basicsr dependency."""
import sys, time, math
import numpy as np
import torch, torch.nn as nn, torch.nn.functional as F
from PIL import Image

class RDB(nn.Module):
    def __init__(self, nf=64, gc=32):
        super().__init__()
        self.conv1 = nn.Conv2d(nf, gc, 3, 1, 1)
        self.conv2 = nn.Conv2d(nf + gc, gc, 3, 1, 1)
        self.conv3 = nn.Conv2d(nf + 2 * gc, gc, 3, 1, 1)
        self.conv4 = nn.Conv2d(nf + 3 * gc, gc, 3, 1, 1)
        self.conv5 = nn.Conv2d(nf + 4 * gc, nf, 3, 1, 1)
        self.lrelu = nn.LeakyReLU(0.2, inplace=True)
    def forward(self, x):
        x1 = self.lrelu(self.conv1(x))
        x2 = self.lrelu(self.conv2(torch.cat((x, x1), 1)))
        x3 = self.lrelu(self.conv3(torch.cat((x, x1, x2), 1)))
        x4 = self.lrelu(self.conv4(torch.cat((x, x1, x2, x3), 1)))
        x5 = self.conv5(torch.cat((x, x1, x2, x3, x4), 1))
        return x5 * 0.2 + x

class RRDB(nn.Module):
    def __init__(self, nf, gc=32):
        super().__init__()
        self.rdb1, self.rdb2, self.rdb3 = RDB(nf, gc), RDB(nf, gc), RDB(nf, gc)
    def forward(self, x):
        return self.rdb3(self.rdb2(self.rdb1(x))) * 0.2 + x

class RRDBNet(nn.Module):
    def __init__(self, in_ch=3, out_ch=3, nf=64, nb=23, gc=32):
        super().__init__()
        self.conv_first = nn.Conv2d(in_ch, nf, 3, 1, 1)
        self.body = nn.Sequential(*[RRDB(nf, gc) for _ in range(nb)])
        self.conv_body = nn.Conv2d(nf, nf, 3, 1, 1)
        self.conv_up1 = nn.Conv2d(nf, nf, 3, 1, 1)
        self.conv_up2 = nn.Conv2d(nf, nf, 3, 1, 1)
        self.conv_hr = nn.Conv2d(nf, nf, 3, 1, 1)
        self.conv_last = nn.Conv2d(nf, out_ch, 3, 1, 1)
        self.lrelu = nn.LeakyReLU(0.2, inplace=True)
    def forward(self, x):
        feat = self.conv_first(x)
        feat = feat + self.conv_body(self.body(feat))
        feat = self.lrelu(self.conv_up1(F.interpolate(feat, scale_factor=2, mode="nearest")))
        feat = self.lrelu(self.conv_up2(F.interpolate(feat, scale_factor=2, mode="nearest")))
        return self.conv_last(self.lrelu(self.conv_hr(feat)))

def main(src, weights, dst, tile=192, pad=16):
    torch.set_num_threads(max(1, torch.get_num_threads()))
    sd = torch.load(weights, map_location="cpu")
    sd = sd.get("params_ema", sd.get("params", sd))
    net = RRDBNet(); net.load_state_dict(sd, strict=True); net.eval()
    img = np.array(Image.open(src).convert("RGB")).astype(np.float32) / 255.0
    h, w = img.shape[:2]
    x = torch.from_numpy(img).permute(2, 0, 1).unsqueeze(0)
    out = torch.zeros(1, 3, h * 4, w * 4)
    ny, nx = math.ceil(h / tile), math.ceil(w / tile)
    t0 = time.time(); n = 0
    with torch.no_grad():
        for iy in range(ny):
            for ix in range(nx):
                y0, x0 = iy * tile, ix * tile
                y1, x1 = min(h, y0 + tile), min(w, x0 + tile)
                py0, px0 = max(0, y0 - pad), max(0, x0 - pad)
                py1, px1 = min(h, y1 + pad), min(w, x1 + pad)
                o = net(x[:, :, py0:py1, px0:px1])
                oy, ox = (y0 - py0) * 4, (x0 - px0) * 4
                out[:, :, y0*4:y1*4, x0*4:x1*4] = o[:, :, oy:oy + (y1-y0)*4, ox:ox + (x1-x0)*4]
                n += 1
                if n % 5 == 0 or n == ny * nx:
                    print(f"tile {n}/{ny*nx}  {time.time()-t0:.0f}s", flush=True)
    res = (out.squeeze(0).permute(1, 2, 0).clamp(0, 1).numpy() * 255).round().astype(np.uint8)
    Image.fromarray(res).save(dst)
    print("saved", dst, res.shape[1], "x", res.shape[0])

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])
