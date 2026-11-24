import argparse
from pathlib import Path

import cv2
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from skimage.morphology import area_opening, reconstruction

RED = (0, 0, 255)
GREEN = (0, 170, 0)


def synthetic_image(seed: int = 7) -> np.ndarray:
    """Coloured objects of many sizes on a light, slightly uneven background."""
    rng = np.random.default_rng(seed)
    h, w = 480, 720
    yy, xx = np.mgrid[0:h, 0:w]
    bg = 225 + 15 * (xx / w) - 10 * (yy / h)
    img = np.dstack([bg, bg, bg]).astype(np.uint8)

    colours = [(40, 40, 200), (200, 80, 30), (30, 160, 60), (160, 40, 160), (20, 150, 200)]
    occupied = np.zeros((h, w), np.uint8)

    def draw(fn, *a):
        fn(img, *a, -1)
        fn(occupied, *a[:-1], 255, -1)

    draw(cv2.circle, (120, 120), 60, colours[0])
    draw(cv2.circle, (560, 360), 75, colours[1])
    draw(cv2.rectangle, (300, 60), (430, 170), colours[2])
    draw(cv2.ellipse, (330, 350), (90, 45), 25, 0, 360, colours[3])
    hole_colour = tuple(int(v) for v in img[110, 600])
    draw(cv2.circle, (600, 110), 55, colours[4])
    cv2.circle(img, (600, 110), 25, hole_colour, -1)
    draw(cv2.rectangle, (40, 300), (220, 307), colours[1])
    draw(cv2.circle, (470, 230), 16, colours[0])
    draw(cv2.rectangle, (150, 400), (185, 430), colours[2])
    keep_out = cv2.dilate(occupied, np.ones((25, 25), np.uint8))
    placed = 0
    while placed < 25:
        x, y = int(rng.integers(10, w - 10)), int(rng.integers(10, h - 10))
        if keep_out[y, x]:
            continue
        r = int(rng.integers(2, 7))
        cv2.circle(img, (x, y), r, colours[int(rng.integers(len(colours)))], -1)
        cv2.circle(keep_out, (x, y), r + 12, 255, -1)
        placed += 1

    noise = rng.normal(0, 6, img.shape)
    return np.clip(img.astype(np.float32) + noise, 0, 255).astype(np.uint8)


def fill_holes(mask: np.ndarray) -> np.ndarray:
    inv = mask == 0
    marker = np.zeros_like(inv)
    marker[0, :], marker[-1, :], marker[:, 0], marker[:, -1] = inv[0, :], inv[-1, :], inv[:, 0], inv[:, -1]
    outside = reconstruction(marker.astype(np.uint8), inv.astype(np.uint8), method="dilation")
    return np.where(outside > 0, 0, 255).astype(np.uint8)


def opening_by_reconstruction(mask: np.ndarray, se: np.ndarray) -> np.ndarray:
    marker = cv2.erode(mask, se)
    rec = reconstruction(marker, mask, method="dilation")
    return rec.astype(np.uint8)


def se_for_area(min_area: int) -> np.ndarray:
    r = max(1, int(round(np.sqrt(min_area / np.pi))))
    return cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))


def overlay_removed(img: np.ndarray, before: np.ndarray, after: np.ndarray) -> np.ndarray:
    out = img.copy()
    removed = np.where((before > 0) & (after == 0), 255, 0).astype(np.uint8)
    contours, _ = cv2.findContours(removed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    for c in contours:
        (cx, cy), r = cv2.minEnclosingCircle(c)
        cv2.circle(out, (int(cx), int(cy)), int(r) + 6, RED, 2)
    contours, _ = cv2.findContours(after, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    cv2.drawContours(out, contours, -1, GREEN, 2)
    return out


def annotate(img: np.ndarray, stats: np.ndarray, cents: np.ndarray) -> np.ndarray:
    out = img.copy()
    for i in range(1, len(stats)):
        x, y, w, h, _ = stats[i]
        cx, cy = cents[i]
        cv2.rectangle(out, (x, y), (x + w, y + h), GREEN, 2)
        cv2.drawMarker(out, (int(cx), int(cy)), RED, cv2.MARKER_CROSS, 12, 2)
        cv2.putText(out, str(i), (x, max(y - 6, 14)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
    return out


def side_by_side(path: Path, panels: list[tuple[str, np.ndarray]], cols: int | None = None) -> None:
    cols = cols or len(panels)
    rows = -(-len(panels) // cols)
    fig, axes = plt.subplots(rows, cols, figsize=(4.2 * cols, 3.6 * rows))
    for ax, (title, im) in zip(np.ravel(axes), panels):
        if im.ndim == 2:
            ax.imshow(im, cmap="gray", vmin=0, vmax=255)
        else:
            ax.imshow(cv2.cvtColor(im, cv2.COLOR_BGR2RGB))
        ax.set_title(title, fontsize=12)
        ax.axis("off")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("image", nargs="?", help="input colour image (default: synthetic)")
    ap.add_argument("--min-area", type=int, default=400, help="A_min in pixels (default 400)")
    ap.add_argument("--out", default=str(Path(__file__).parent / "out"), help="output directory")
    args = ap.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    save = lambda name, im: cv2.imwrite(str(out / name), im)

    img = cv2.imread(args.image) if args.image else synthetic_image()
    if img is None:
        raise SystemExit(f"cannot read {args.image}")
    save("01_input.png", img)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    sat = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)[:, :, 1]
    save("02a_gray.png", gray)
    save("02b_saturation.png", sat)

    blur = cv2.GaussianBlur(sat, (5, 5), 0)
    save("03_blur.png", blur)

    t, mask = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    if np.count_nonzero(mask) > mask.size / 2:
        mask = cv2.bitwise_not(mask)
    save("04_otsu.png", mask)
    fig, ax = plt.subplots(figsize=(6, 3))
    ax.hist(blur.ravel(), bins=256, range=(0, 255), color="0.4")
    ax.axvline(t, color="red", lw=2, label=f"próg Otsu = {t:.0f}")
    ax.set_xlabel("nasycenie (S)"), ax.set_ylabel("liczba pikseli"), ax.set_yscale("log"), ax.legend()
    fig.tight_layout(), fig.savefig(out / "04b_histogram.png", dpi=150), plt.close(fig)

    closed = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)))
    filled = fill_holes(closed)
    save("05a_closed.png", closed)
    save("05b_filled.png", filled)

    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
    side_by_side(out / "00_basic_operators.png", [
        ("maska", filled),
        ("erozja", cv2.erode(filled, k)),
        ("dylatacja", cv2.dilate(filled, k)),
        ("otwarcie", cv2.morphologyEx(filled, cv2.MORPH_OPEN, k)),
        ("zamknięcie", cv2.morphologyEx(filled, cv2.MORPH_CLOSE, k)),
    ])

    se = se_for_area(args.min_area)
    by_open = cv2.morphologyEx(filled, cv2.MORPH_OPEN, se)
    by_rec = opening_by_reconstruction(filled, se)
    by_area = area_opening(filled, area_threshold=args.min_area, connectivity=2).astype(np.uint8)
    save("06_area_opening.png", by_area)
    save("06b_removed_overlay.png", overlay_removed(img, filled, by_area))
    side_by_side(out / "06c_method_comparison.png", [
        (f"otwarcie (koło o polu ≈ {args.min_area} px)", by_open),
        ("otwarcie przez rekonstrukcję", by_rec),
        (f"otwarcie powierzchniowe (A_min = {args.min_area} px)", by_area),
    ])

    n, labels, stats, cents = cv2.connectedComponentsWithStats(by_area, connectivity=8)
    result = img.copy()
    result[by_area == 0] = np.median(img[filled == 0], axis=0)
    save("07a_result.png", result)
    save("07b_annotated.png", annotate(img, stats, cents))

    side_by_side(out / "99_pipeline.png", [
        ("1. obraz wejściowy", img), ("2–3. nasycenie + rozmycie", blur), ("4. binaryzacja Otsu", mask),
        ("5. czyszczenie maski", filled), ("6. otwarcie powierzchniowe", by_area), ("7. wykryte obiekty", annotate(img, stats, cents)),
    ], cols=3)

    print(f"Otsu threshold: {t:.0f}   A_min: {args.min_area} px   SE radius: {se.shape[0] // 2}")
    print(f"objects before: {cv2.connectedComponents(filled, connectivity=8)[0] - 1}")
    print(f"objects after:  {n - 1}   (plain opening: {cv2.connectedComponents(by_open)[0] - 1}, "
          f"by reconstruction: {cv2.connectedComponents(by_rec)[0] - 1})")
    print(f"{'#':>3} {'cx':>8} {'cy':>8} {'x':>5} {'y':>5} {'w':>5} {'h':>5} {'area':>7}")
    for i in range(1, n):
        x, y, w, h, a = stats[i]
        print(f"{i:>3} {cents[i][0]:8.1f} {cents[i][1]:8.1f} {x:5d} {y:5d} {w:5d} {h:5d} {a:7d}")
    print(f"images written to {out}/")


if __name__ == "__main__":
    main()
