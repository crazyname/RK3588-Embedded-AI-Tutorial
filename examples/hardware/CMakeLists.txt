cmake_minimum_required(VERSION 3.12)
project(rk3588_classifier LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(RKNN_INCLUDE_DIR "" CACHE PATH "Directory containing rknn_api.h")
set(RKNN_LIB "" CACHE FILEPATH "Full path to ARM64 librknnrt.so")
if(NOT EXISTS "${RKNN_INCLUDE_DIR}/rknn_api.h")
  message(FATAL_ERROR "Pass -DRKNN_INCLUDE_DIR pointing to the RKNPU2 SDK include folder")
endif()
if(NOT EXISTS "${RKNN_LIB}")
  message(FATAL_ERROR "Pass -DRKNN_LIB with the full ARM64 runtime .so path")
endif()
add_executable(rknn_classifier rknn_classify.cpp)
target_include_directories(rknn_classifier PRIVATE "${RKNN_INCLUDE_DIR}")
target_link_libraries(rknn_classifier PRIVATE "${RKNN_LIB}")
set_target_properties(rknn_classifier PROPERTIES BUILD_RPATH "$ORIGIN")

# Lesson 26 zero-copy inference. Requires native target runtime with matching headers.
add_executable(rknn_zero_copy rknn_zero_copy.cpp)
target_include_directories(rknn_zero_copy PRIVATE "${RKNN_INCLUDE_DIR}")
target_link_libraries(rknn_zero_copy PRIVATE "${RKNN_LIB}")
set_target_properties(rknn_zero_copy PROPERTIES BUILD_RPATH "$ORIGIN")

# One-model comparison: normal inputs_set versus input memory binding.
add_executable(rknn_compare_input_io rknn_compare_input_io.cpp)
target_include_directories(rknn_compare_input_io PRIVATE "${RKNN_INCLUDE_DIR}")
target_link_libraries(rknn_compare_input_io PRIVATE "${RKNN_LIB}")
set_target_properties(rknn_compare_input_io PROPERTIES BUILD_RPATH "$ORIGIN")

# Optional Rockchip RGA preprocessing (virtual-address import, RGB888 letterbox).
# This is an independent tool; it does not use DMA-BUF to deliver frames to the NPU.
set(RGA_INCLUDE_DIR "" CACHE PATH "Directory containing im2d.hpp and librga headers")
set(RGA_LIB "" CACHE FILEPATH "Absolute path to board-matching librga.so")
if(RGA_INCLUDE_DIR AND RGA_LIB)
  if(NOT EXISTS "${RGA_INCLUDE_DIR}/im2d.hpp" OR NOT EXISTS "${RGA_LIB}")
    message(FATAL_ERROR "RGA_INCLUDE_DIR must contain im2d.hpp and RGA_LIB must be a real library")
  endif()
  add_executable(rga_letterbox_rgb888 rga_letterbox_rgb888.cpp)
  target_include_directories(rga_letterbox_rgb888 PRIVATE "${RGA_INCLUDE_DIR}")
  target_link_libraries(rga_letterbox_rgb888 PRIVATE "${RGA_LIB}")
  set_target_properties(rga_letterbox_rgb888 PROPERTIES BUILD_RPATH "$ORIGIN")
endif()

# Optimized Model Zoo YOLOv8: actual RKNPU2 6/9 outputs with our own FP32 DFL/NMS.
# Input comes from prepared RGB 640x640 HWC RAW; not a V4L2 or DMA-BUF app.
add_library(yolov8_decode STATIC yolov8_postprocess.cpp)
target_include_directories(yolov8_decode PUBLIC "${CMAKE_CURRENT_SOURCE_DIR}")
add_executable(rknn_yolov8_raw rknn_yolov8_raw.cpp)
target_include_directories(rknn_yolov8_raw PRIVATE "${RKNN_INCLUDE_DIR}")
target_link_libraries(rknn_yolov8_raw PRIVATE yolov8_decode "${RKNN_LIB}")
set_target_properties(rknn_yolov8_raw PROPERTIES BUILD_RPATH "$ORIGIN")

# Pure CPU, no SDK runtime or NPU required, useful for comparing against Python.
add_executable(yolov8_decode_files yolov8_decode_files.cpp)
target_link_libraries(yolov8_decode_files PRIVATE yolov8_decode)

# Experimental ROCK 5B V4L2 YUYV capture -> real DMA-BUF fd import to RGA
# -> CPU letterbox -> rknn_inputs_set -> optimized YOLOv8 C++ DFL/NMS.
# Not end-to-end zero-copy: RKNPU2 input still uses CPU-side staging.
if(RGA_INCLUDE_DIR AND RGA_LIB)
  add_executable(v4l2_rga_rknn_yolov8 v4l2_rga_rknn_yolov8.cpp)
  target_include_directories(v4l2_rga_rknn_yolov8 PRIVATE "${RKNN_INCLUDE_DIR}" "${RGA_INCLUDE_DIR}")
  target_link_libraries(v4l2_rga_rknn_yolov8 PRIVATE yolov8_decode "${RKNN_LIB}" "${RGA_LIB}")
  set_target_properties(v4l2_rga_rknn_yolov8 PROPERTIES BUILD_RPATH "$ORIGIN")
endif()
