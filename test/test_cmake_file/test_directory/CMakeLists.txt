project(test_directory)
cmake_minimum_required(VERSION 3.16)

add_library(foo bar.cpp)
add_definitions(-Dfoo)
target_compile_definitions(foo PUBLIC foo)
add_compile_definitions(john)
add_definitions(-Dbar)
remove_definitions(-Djohn -Dbar -Dfoo)
