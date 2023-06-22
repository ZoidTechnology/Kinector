cmake_minimum_required(VERSION 3.25)

project(kinect)

add_subdirectory(libraries/pybind11)
pybind11_add_module(${PROJECT_NAME} kinect.cpp filter.h filter.cpp)

add_subdirectory(libraries/eigen)
target_link_libraries(${PROJECT_NAME} PRIVATE eigen)

set(kinect_sdk_path "C:/Program Files/Microsoft SDKs/Kinect/v2.0_1409")
target_include_directories(${PROJECT_NAME} PRIVATE ${kinect_sdk_path}/inc)
target_link_libraries(${PROJECT_NAME} PRIVATE ${kinect_sdk_path}/Lib/x64/Kinect20.lib)

set(blender_addon_path $ENV{BLENDER_ADDONS_PATH}/kinector)
add_custom_command(TARGET ${PROJECT_NAME} POST_BUILD COMMAND ${CMAKE_COMMAND} -E copy ${CMAKE_SOURCE_DIR}/kinector.py ${blender_addon_path}/__init__.py)
add_custom_command(TARGET ${PROJECT_NAME} POST_BUILD COMMAND ${CMAKE_COMMAND} -E copy $<TARGET_FILE:kinect> ${blender_addon_path}/kinect.pyd)