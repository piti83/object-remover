add_library(object_remover_core STATIC
  segmentation.cpp
  morphology.cpp
  analysis.cpp
)

target_include_directories(object_remover_core PUBLIC include)
target_link_libraries(object_remover_core PUBLIC ${OpenCV_LIBS})
target_include_directories(object_remover_core PUBLIC ${OpenCV_INCLUDE_DIRS})
target_compile_options(object_remover_core PRIVATE
  $<$<CXX_COMPILER_ID:GNU,Clang>:-Wall -Wextra -Wpedantic>)
