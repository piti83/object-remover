find_package(GTest REQUIRED)

add_executable(object_remover_tests
  test_segmentation.cpp
  test_morphology.cpp
  test_analysis.cpp
)
target_link_libraries(object_remover_tests PRIVATE object_remover_core GTest::gtest_main)

include(GoogleTest)
gtest_discover_tests(object_remover_tests)
