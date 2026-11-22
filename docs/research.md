# Removing Small Objects with Morphology

## 1. Goal and scope

The program reads a colour image and an area threshold `A_min` (in pixels), removes every object smaller than `A_min` using morphological operations, and then prints the number of remaining objects and their coordinates.

**Input:** path to an RGB image (PNG/JPG) and the number `A_min` supplied by the user (CLI argument or a slider in a GUI).

**Output:**

- the result image (the original with small objects removed, or the binary mask),
- the object count `N`,
- for each object: index, centroid `(x, y)`, bounding box `(x, y, w, h)` and area in pixels.

**Key definitions (state these in the report):**

- *Object* — a connected component of the binary foreground mask, under a fixed connectivity (8-connectivity recommended).
- *Area* — the number of pixels in the component. If physical units are required, a px → mm² scale factor is enough.
- *Coordinates* — the centroid; additionally the bounding box, since it is easy to draw on the image.

The assignment requires removal **by morphological transformations**. A plain "count pixels per label and drop" filter is not, formally, morphology. The core of the solution should therefore be an **area opening** or an **opening by reconstruction**: both are morphological operators and both preserve the exact shape of the large objects.

---

## 2. Theory

Everything rests on four operations on a binary image `X` with a structuring element `B` (SE). All other operations are compositions of these.

**Erosion** — a pixel survives only if the SE translated to that position fits entirely inside the object. Shrinks objects and removes those smaller than `B`.

$$X \ominus B = \{\, z : B_z \subseteq X \,\}$$

**Dilation** — a pixel is set if the SE translated to that position touches the object. Grows objects and fills gaps.

$$X \oplus B = \{\, z : \hat{B}_z \cap X \neq \emptyset \,\}$$

**Opening** = erosion followed by dilation. Removes objects in which `B` does not fit, but also smooths the contours of the survivors (rounds corners, cuts thin protrusions).

$$X \circ B = (X \ominus B) \oplus B$$

**Closing** = dilation followed by erosion. Fills small holes and gaps in objects.

$$X \bullet B = (X \oplus B) \ominus B$$

### Why a plain opening is not enough

Opening decides removal by **shape** (does `B` fit?), not by **area**. A thin, long object with an area of 5000 px disappears after opening with a 15×15 square (area 225 px), while a compact disc of 300 px survives. The assignment is about area, so we need an operator that measures area.

### Morphological reconstruction (opening by reconstruction)

Reconstruction of mask `X` from marker `M` is repeated *geodesic dilation* — dilation constrained to `X` — until the image stops changing. The result contains exactly those components of `X` touched by the marker:

$$\delta^{(1)}_X(M) = (M \oplus B) \cap X, \qquad R_X(M) = \delta^{(\infty)}_X(M)$$

**Opening by reconstruction:** marker = erosion of `X` by `B`, then reconstruct. Objects that survived the erosion come back in their **original, untouched shape**; the rest disappear. The criterion is still the shape of `B`, but contours are no longer distorted (Vincent 1993).

### Area opening — the core of the solution

An area opening with parameter λ keeps connected components with area ≥ λ and removes the rest, without altering the shape of the survivors. Formally it is the **supremum of openings by all connected structuring elements with area ≥ λ**, so it is a proper morphological opening (idempotent, anti-extensive, increasing) (Vincent 1992/1994):

$$\gamma_\lambda(X) = \bigcup \{\, X \circ B : B \text{ connected},\ |B| \geq \lambda \,\}$$

For a binary image this is exactly "remove objects with area < `A_min`", i.e. a 1:1 match with the assignment. The same operator exists for greyscale images, which optionally lets us filter before binarisation.

**Area closing** is the dual: it fills holes with area < λ. Useful before measuring area, since a hole underestimates an object's area.

---

## 3. Pipeline step by step

Binary morphology works on a mask, so the foreground must first be extracted from the colour image. The program is seven steps in a straight line:

1. **Load the image** — `cv::imread` (note: OpenCV returns BGR, not RGB).
2. **Prepare a channel for segmentation** — one of:
    - greyscale (`cv::cvtColor(img, gray, cv::COLOR_BGR2GRAY)`) — when objects differ from the background in brightness,
    - the S channel of HSV (`cv::COLOR_BGR2HSV` + `cv::extractChannel(hsv, s, 1)`) — when objects are coloured on a grey/white background (works very well for typical test images),
    - colour distance from the background colour (e.g. in Lab space) — the most general.
3. **Smoothing** — a light Gaussian (`cv::GaussianBlur`) or 3×3/5×5 median filter (`cv::medianBlur`) so that noise does not produce spurious objects.
4. **Binarisation** — Otsu's method picks the threshold automatically by maximising between-class variance of the histogram (Otsu 1979): `cv::threshold(s, mask, 0, 255, cv::THRESH_BINARY | cv::THRESH_OTSU)`. If the background is light and objects are dark, invert the mask (`cv::THRESH_BINARY_INV`).
5. **Mask cleanup** — a morphological closing with a small SE (`cv::morphologyEx(mask, mask, cv::MORPH_CLOSE, cv::getStructuringElement(cv::MORPH_ELLIPSE, {3, 3}))`) to bridge small gaps, and hole filling (OpenCV has no `fill_holes`; see section 5).
6. **Remove objects with area < `A_min`** — our own `areaOpening()` (OpenCV has no area opening; see section 5).
7. **Labelling and measurement** — `cv::connectedComponentsWithStats(mask, labels, stats, centroids, 8, CV_32S)` returns area (`stats.at<int>(i, cv::CC_STAT_AREA)`), bounding box (`CC_STAT_LEFT/TOP/WIDTH/HEIGHT`) and centroid (`centroids.at<double>(i, 0/1)`) for each component; label 0 is the background, so object count = `n - 1`.

Finally: print the object table, draw boxes and indices on the result image (`cv::rectangle`, `cv::putText`), save the image (`cv::imwrite`) and (optionally) a CSV.

---

## 4. Comparison of small-object removal methods

Recommendation: **area opening as the main method**, and in the report a comparison against plain opening and opening by reconstruction on the same image. This comparison clearly shows the difference between a shape criterion and an area criterion.

| Method | Removal criterion | Shape of survivors | Is it morphology | Notes |
| --- | --- | --- | --- | --- |
| Area opening | area < `A_min`, exactly | untouched | yes (attribute opening) | best fit for the assignment; we implement it ourselves (section 5) |
| Opening by reconstruction | SE does not fit in the object | untouched | yes | shape criterion, not area; SE derived from `A_min` (e.g. disc of area `A_min`) |
| Plain opening | SE does not fit in the object | smoothed, distorted | yes | simplest (`cv::morphologyEx` + `MORPH_OPEN`); loses thin large objects, corrupts area measurement |
| Labelling + area filter | area < `A_min`, exactly | untouched | not directly | identical result to area opening, but formally component analysis |

Practical note: for a binary image, area opening and "label and drop small" give identical results (the scikit-image documentation states the same equivalence for its `area_opening` / `remove_small_objects`). A filter built on `cv::connectedComponentsWithStats` is therefore a ready-made oracle for testing our `areaOpening()`.

### Choosing the SE from `A_min` (for SE-based methods)

For a disc of area `A_min`, radius r = √(A_min / π); SE = ellipse of diameter 2r+1. Compact objects (discs, squares) are filtered almost the same as with area opening; elongated objects are not. This is worth demonstrating on a test image containing a thin bar.

---

### What OpenCV does not provide

OpenCV gives erosion, dilation, opening, closing and connected-component labelling, but **no area opening, no morphological reconstruction and no hole filling**. These are also the most interesting parts to present.

- **Reconstruction by dilation** — loop: `cv::dilate(marker, next, 3×3)`, `cv::bitwise_and(next, mask, next)`; stop when `cv::countNonZero(next != marker) == 0`. Simple, slow on large objects, fine for this project. (Vincent 1993 gives faster queue-based variants.)
- **Opening by reconstruction** — `cv::erode` with the SE, then reconstruction of the original mask from that marker.
- **Hole filling** — reconstruction of the complement from the image border: marker = border pixels of `~mask`, reconstruct inside `~mask` → background reachable from the edge; holes = everything else. Pure morphology, no `floodFill` needed.
- **Area opening (binary)** — for each connected component compute its area and keep it if area ≥ `A_min`. Implementation: a single pass with union-find (the standard approach for connected set openings, Meijster & Wilkinson 2002), or BFS flood fill per component. Validate against the `connectedComponentsWithStats` filter.
- **Border objects** — reconstruction of the mask from its border pixels gives exactly the objects touching the edge; subtract to discard them if needed.

### GUI options

| Option | Extra dependencies | Effort | What you get |
| --- | --- | --- | --- |
| OpenCV HighGUI (`cv::imshow`, `cv::createTrackbar`) | none | ~1 evening | window with `A_min` slider and live preview; object list in the terminal |
| Dear ImGui + GLFW/OpenGL | ImGui, GLFW (via CMake `FetchContent`) | medium | slider, method selector and object table in one window; needs `cv::Mat` → texture upload |
| Qt 6 Widgets | Qt 6 | largest | proper app: file-open dialog, image views, object table, save button; `cv::Mat` → `QImage` conversion |

Recommendation: CLI first, then HighGUI trackbar (almost free, still counts as a GUI). Move to Qt 6 only if there is time left — it gives the best-looking result for the presentation.

### Build and tests

- Dependencies on Arch: `pacman -S opencv cmake` (+ `qt6-base` for Qt, `gtest` for tests). OpenCV's HighGUI requires `opencv` built with a GUI backend; the Arch package has one.
- CMake: `find_package(OpenCV REQUIRED)`, a `core` static library linked by `cli`, `gui` and `tests`; `option(BUILD_GUI ...)`.
- Tests: GoogleTest (`find_package(GTest)` or `FetchContent`), synthetic images drawn with `cv::circle` / `cv::rectangle`.

---

## 6. Pitfalls and edge cases

Most errors in projects like this come from segmentation, not from the morphology itself.

- **Light vs dark background.** Morphology assumes objects = 1, background = 0. With a white background the mask must be inverted, otherwise the background becomes one giant "object". This can be detected automatically: if > 50% of pixels are 1 after binarisation, invert.
- **4- vs 8-connectivity.** Two objects touching only at a corner are one object under 8-connectivity and two under 4-connectivity. Pick one and use it consistently in filtering and labelling.
- **Touching objects.** Touching objects merge into one component with a large area. Standard fix: distance transform + marker-based watershed (`cv::distanceTransform`, `cv::watershed`). This is an extension — worth mentioning, not required.
- **Holes in objects.** A ring has a smaller area than a full disc. Decide whether area is counted with or without holes and state it in the report (recommended: fill holes before measuring).
- **Noise after binarisation.** Single pixels are objects too. Area opening removes them automatically when `A_min` > 1, but light blurring before binarisation still improves contours.
- **Objects cut by the image border.** The visible part may fall below the threshold even though the object is large. Flag them separately (bbox touches the border) or optionally discard them (reconstruction from the border, section 5).
- **Shadows and highlights.** In phone photos an object's shadow often ends up in the mask. The HSV S channel is less sensitive to this than greyscale.
- **Coordinate convention.** `cv::Mat::at<>(row, col)` is `(y, x)`; `cv::Point` and OpenCV centroids are `(x, y)`. Always print `(x, y)` with the origin at the top-left corner and say so in the program output.
- **"Smaller than" comparison.** The assignment says "area smaller than the given value", so an object with area exactly `A_min` stays: keep `area >= minArea`. Cover the boundary case with a test.
- **Mask type.** OpenCV morphology and labelling expect `CV_8UC1`; keep masks as 0/255 everywhere and convert once after thresholding.

---

## 7. Implementation plan, repo layout and tests

- [ ] CMake skeleton: `core` library, `cli` executable, `tests`; OpenCV found and linked.
- [ ] Synthetic image generator: coloured discs and rectangles with **known** areas and centres on a uniform background (+ a noisy variant).
- [ ] Colour → mask segmentation with automatic light-background detection.
- [ ] Morphology: reconstruction, hole filling, `areaOpening` (default), plus `opening` and `openingByReconstruction` for comparison.
- [ ] Labelling, print `N` and the table (index, cx, cy, bbox, area), save CSV.
- [ ] Visualisation: original / mask / result side by side, boxes and indices on objects.
- [ ] Unit tests (below).
- [ ] Experiment for the report: same image, three methods, various `A_min`; table of object counts.
- [ ] GUI, level 1: HighGUI window with `A_min` trackbar and live preview.
- [ ] GUI, level 2 (if time): Qt 6 or Dear ImGui with file dialog, method selector and object table.

### Tests worth having

- image with objects of area 50, 200, 1000 px and `A_min` = 200 → two remain (boundary: area equal to the threshold stays),
- centroids of detected discs match the known centres within ±1 px,
- `areaOpening` result == "label and drop small" result via `connectedComponentsWithStats` (identical masks),
- a thin 3×500 px bar survives area opening but disappears after plain opening — a test that documents the difference between methods,
- `fillHoles` on a ring returns a full disc; reconstruction from a marker inside one object returns only that object,
- images with white and black backgrounds give the same object count.

### Test images

Besides synthetic ones, photos of coins, buttons or blocks on a uniform background are useful. The assignment needs at least one colour image.

---

## 8. References

For the report, 3–4 items are enough: one textbook, Vincent (reconstruction + area opening), Otsu, and optionally Breen & Jones as the generalisation.

### Papers

| Reference | What to take from it |
| --- | --- |
| L. Vincent, [Morphological Grayscale Reconstruction in Image Analysis: Applications and Efficient Algorithms](https://typeset.io/papers/morphological-grayscale-reconstruction-in-image-analysis-nh3wqbbs21), IEEE Trans. Image Processing 2(2):176–201, 1993 | definition of reconstruction, opening by reconstruction, fast algorithms; theoretical basis of the project |
| L. Vincent, [Morphological Area Openings and Closings for Grey-scale Images](https://www.doi.org/10.1007/978-3-662-03039-4_13), in: Shape in Picture, NATO ASI vol. 126, Springer 1994, pp. 197–208 | definition of area opening as the supremum of openings by connected SEs with area ≥ λ |
| L. Vincent, [Grayscale area openings and closings, their efficient implementation and applications](https://typeset.io/pdf/grayscale-area-openings-and-closings-their-efficient-15jx1dfgem.pdf), EURASIP Workshop on Mathematical Morphology, Barcelona 1993, pp. 22–27 | efficient area opening implementation (priority queue) |
| A. Meijster, M. H. F. Wilkinson, A comparison of algorithms for connected set openings and closings, IEEE Trans. PAMI 24(4):484–494, 2002 | union-find implementation of area openings — the basis for our `areaOpening()` |
| E. J. Breen, R. Jones, Attribute openings, thinnings, and granulometries, Computer Vision and Image Understanding 64(3):377–389, 1996, [doi:10.1006/cviu.1996.0066](https://doi.org/10.1006/cviu.1996.0066) | generalisation: attribute openings (area is one attribute; others include perimeter, elongation) |
| P. Salembier, A. Oliveras, L. Garrido, [Antiextensive connected operators for image and sequence processing](https://imatge.upc.edu/web/publications/antiextensive-connected-operators-image-and-sequence-processing), IEEE Trans. Image Processing 7(4):555–570, 1998 | connected operators and the max-tree — the structure behind `area_opening` in scikit-image |
| R. M. Haralick, S. R. Sternberg, X. Zhuang, [Image Analysis Using Mathematical Morphology](https://www.haralick.org/journals/04767941.pdf), IEEE Trans. PAMI 9(4):532–550, 1987 | classic tutorial on erosion, dilation, opening and closing; good for the theory intro |
| N. Otsu, A Threshold Selection Method from Gray-Level Histograms, IEEE Trans. SMC 9(1):62–66, 1979, [doi:10.1109/TSMC.1979.4310076](https://doi.org/10.1109/tsmc.1979.4310076) | automatic binarisation threshold |
| F. Bolelli, S. Allegretti, L. Baraldi, C. Grana, [Spaghetti Labeling: Directed Acyclic Graphs for Block-Based Connected Components Labeling](https://iris.unimore.it/handle/11380/1181437), IEEE Trans. Image Processing 29:1999–2012, 2020 | modern connected-component labelling algorithm (optional, if you describe labelling) |

### Textbooks

- R. C. Gonzalez, R. E. Woods, *Digital Image Processing*, 4th ed., Pearson 2018 — chapter on morphological image processing (erosion, dilation, opening, reconstruction, hole filling, connected components). The most convenient source to cite definitions from.
- P. Soille, *Morphological Image Analysis: Principles and Applications*, 2nd ed., Springer 2003 — thorough treatment of reconstruction and area openings.
- J. Serra, *Image Analysis and Mathematical Morphology*, Academic Press 1982 — source of the classic definitions.
- R. Tadeusiewicz, P. Korohoda, *Komputerowa analiza i przetwarzanie obrazów*, Wydawnictwo Fundacji Postępu Telekomunikacji, Kraków 1997 — Polish textbook with a morphology chapter; useful for Polish terminology in the presentation.

Textbook details and the Meijster & Wilkinson entry were given from memory — verify edition, year and pages before putting them in the bibliography.

### Documentation

- [OpenCV: Structural Analysis and Shape Descriptors](https://docs.opencv.org/5.0/main_modules/imgproc_shape.html) — `connectedComponentsWithStats`.
- OpenCV image filtering module (`cv::erode`, `cv::dilate`, `cv::morphologyEx`, `cv::getStructuringElement`) and HighGUI (`cv::createTrackbar`) — docs.opencv.org.
- [scikit-image: skimage.morphology](https://scikit-image.org/docs/stable/api/skimage.morphology.html) — reference implementation of `area_opening` / `reconstruction`, useful for cross-checking results.
- [PyImageSearch: OpenCV connected component labeling and analysis](https://pyimagesearch.com/2021/02/22/opencv-connected-component-labeling-and-analysis/) — practical example of filtering components by area (Python, but the API maps 1:1 to C++).
