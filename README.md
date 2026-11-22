# object-remover
C++ Program for removing objects from images

## Build

Requires CMake ≥ 3.20, a C++17 compiler, OpenCV and GoogleTest.

```sh
cmake -S . -B build            # -DBUILD_GUI=OFF / -DBUILD_TESTS=OFF to skip
cmake --build build -j
ctest --test-dir build         # run tests
./build/src/cli/object-remover
```

See `docs/research.md` for the plan.
