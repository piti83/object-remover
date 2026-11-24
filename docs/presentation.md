# Plan prezentacji — usuwanie małych obiektów morfologią

Plan slajdów do ręcznego złożenia w Google Slides. Każdy slajd ma:

- **Na slajdzie** — tekst do wklejenia (krótko, hasłowo),
- **Grafika** — plik z `prototype/out/` albo coś do narysowania,
- **Co powiedzieć** — notatki prelegenta.

Grafiki generuje prototyp w Pythonie:

```sh
python -m venv prototype/.venv
prototype/.venv/bin/pip install -r prototype/requirements.txt
prototype/.venv/bin/python prototype/steps.py                 # obraz syntetyczny, A_min = 400
prototype/.venv/bin/python prototype/steps.py foto.jpg --min-area 1500
```

Liczby w planie pochodzą z przebiegu na obrazie syntetycznym przy A_min = 400 px. Jeśli zmienisz obraz lub próg, przepisz je z wyjścia skryptu.

Łącznie 11 slajdów, około 8–10 minut. Po slajdzie z planem każdy krok ma jeden krótki slajd: jedno, dwa zdania i jeden obraz.

---

## 1. Tytuł

**Na slajdzie:**
Usuwanie małych obiektów z obrazu kolorowego za pomocą przekształceń morfologicznych
Analiza i przetwarzanie obrazów — projekt zaliczeniowy
Imię Nazwisko, data

**Grafika:** `01_input.png` obok `07b_annotated.png` (przed → po).

---

## 2. Zadanie

**Na slajdzie:**

- Wejście: obraz kolorowy + próg powierzchni A_min podany przez użytkownika
- Usunąć obiekty o powierzchni < A_min — **przekształceniami morfologicznymi**
- Wyjście: liczba pozostałych obiektów + ich współrzędne

**Grafika:** `01_input.png`.

**Co powiedzieć:** Na obrazie są obiekty o bardzo różnych rozmiarach, od kilkupikselowych kropek po duże figury. Użytkownik decyduje, co jest „małe”. Kluczowe słowo w temacie to „morfologicznymi”: samo policzenie pikseli i wyrzucenie małych etykiet nie spełnia tematu.

---

## 3. Plan rozwiązania — 7 kroków

**Na slajdzie (diagram ze strzałkami):**
Wczytanie → wybór kanału → wygładzenie → binaryzacja (Otsu) → czyszczenie maski → **usunięcie małych obiektów** → etykietowanie i pomiar

**Grafika:** narysuj łańcuch 7 prostokątów ze strzałkami; krok 6 wyróżniony kolorem.

**Co powiedzieć:** Morfologia binarna działa na masce czarno-białej, więc kroki 1–5 zamieniają obraz kolorowy w maskę „obiekt / tło”. Krok 6 to sedno tematu. Krok 7 odpowiada na pytanie „ile i gdzie”.

---

## 4. Krok 1: wczytanie obrazu

**Na slajdzie:** Obraz kolorowy (BGR), obiekty od kilku do kilkunastu tysięcy pikseli.

**Grafika:** `01_input.png`.

**Co powiedzieć:** Obraz testowy jest syntetyczny, więc znam pole i środek każdego obiektu i mogę sprawdzić wynik. Są na nim m.in. pierścień z dziurą i cienki pasek — wrócą w krokach 5 i 6.

---

## 5. Krok 2: wybór kanału

**Na slajdzie:** Kanał nasycenia (S z HSV): tło ≈ 0, każdy kolorowy obiekt jasny.

**Grafika:** `02a_gray.png` obok `02b_saturation.png`.

**Co powiedzieć:** W skali szarości każdy kolor ma inną jasność, a tło ma gradient oświetlenia. W nasyceniu tło jest prawie czarne niezależnie od barwy obiektów, więc łatwiej je oddzielić.

---

## 6. Krok 3: wygładzenie

**Na slajdzie:** Filtr Gaussa 5×5 — mniej szumu, gładsze krawędzie.

**Grafika:** `03_blur.png`.

**Co powiedzieć:** Bez wygładzenia pojedyncze zaszumione piksele stałyby się osobnymi „obiektami” po binaryzacji.

---

## 7. Krok 4: binaryzacja Otsu

**Na slajdzie:** Próg dobierany automatycznie z histogramu (tu: 109). Wynik: maska obiekt / tło.

**Grafika:** `04b_histogram.png` + `04_otsu.png`.

**Co powiedzieć:** Otsu wybiera próg, który najlepiej rozdziela dwie grupy pikseli (tło i obiekty). Jeśli maska wyjdzie odwrotnie, czyli „obiekt” zajmuje ponad połowę obrazu, program ją odwraca.

---

## 8. Krok 5: czyszczenie maski

**Na slajdzie:** Zamknięcie (dylatacja → erozja) skleja drobne przerwy; wypełnienie dziur — pierścień liczony jako pełne koło.

**Grafika:** `05a_closed.png` obok `05b_filled.png` (żółty pierścień w prawym górnym rogu).

**Co powiedzieć:** Bez wypełnienia dziury pole pierścienia byłoby zaniżone. Wypełnianie dziur to też morfologia: tło połączone z krawędzią obrazu odbudowujemy rekonstrukcją, a wszystko inne, co czarne, to dziury.

---

## 9. Krok 6: usunięcie obiektów o polu < A_min

**Na slajdzie:** Otwarcie powierzchniowe: zostają składowe o polu ≥ A_min, kształt bez zmian. 33 obiekty → 8 (A_min = 400 px).

**Grafika:** `06b_removed_overlay.png` (czerwone kółka = usunięte, zielone kontury = zostają). Opcjonalnie mały `06c_method_comparison.png` w rogu.

**Co powiedzieć:** Zwykłe otwarcie (erozja → dylatacja) usuwa obiekty po kształcie, a nie po polu: zniknąłby też cienki pasek o polu 1445 px, a kwadrat straciłby ostre rogi. Otwarcie powierzchniowe to otwarcie wszystkimi spójnymi kształtami o polu ≥ A_min naraz, więc usuwa dokładnie to, czego wymaga temat.

---

## 10. Krok 7: liczenie obiektów i współrzędne

**Na slajdzie:** Etykietowanie składowych spójnych → **8 obiektów**, dla każdego środek (x, y), prostokąt i pole.

| # | środek (x, y) | pole [px] |
| --- | --- | --- |
| 1 | (600.0, 110.0) | 9476 |
| 2 | (120.0, 120.0) | 11285 |
| 7 | (129.9, 303.5) | 1445 |
| … | … | … |

**Grafika:** `07b_annotated.png`.

**Co powiedzieć:** Koło narysowane w punkcie (120, 120) ma wyliczony środek (120.0, 120.0), więc współrzędne się zgadzają.

---

## 11. Wynik — koniec

**Na slajdzie:** Dziękuję. Pytania?

**Grafika:** `99_pipeline.png` (wszystkie kroki w siatce 2×3).

**Co powiedzieć:** Jedno zdanie podsumowania: obraz kolorowy → maska → otwarcie powierzchniowe → 8 obiektów ze współrzędnymi. Docelowy program powstaje w C++ z OpenCV.
