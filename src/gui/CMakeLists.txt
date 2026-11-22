find_package(OpenCV REQUIRED COMPONENTS highgui)

add_executable(object_remover_gui main.cpp)
target_link_libraries(object_remover_gui PRIVATE object_remover_core ${OpenCV_LIBS})
set_target_properties(object_remover_gui PROPERTIES OUTPUT_NAME object-remover-gui)
