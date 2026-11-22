cmake_minimum_required(VERSION 3.20)
project(object_remover VERSION 0.1.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

option(BUILD_GUI   "Build the GUI front-end" ON)
option(BUILD_TESTS "Build unit tests"        ON)

if(NOT CMAKE_BUILD_TYPE AND NOT CMAKE_CONFIGURATION_TYPES)
  set(CMAKE_BUILD_TYPE Debug CACHE STRING "Build type" FORCE)
endif()

find_package(OpenCV REQUIRED COMPONENTS core imgproc imgcodecs)

add_subdirectory(src/core)
add_subdirectory(src/cli)

if(BUILD_GUI)
  add_subdirectory(src/gui)
endif()

if(BUILD_TESTS)
  enable_testing()
  add_subdirectory(tests)
endif()
