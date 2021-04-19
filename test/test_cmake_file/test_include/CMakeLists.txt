option(BUILD_CLIENT		"Build the client executable"									ON)
option(FEATURE_RENDERER2		"Build and use the new renderer"						OFF)
set(foo bar.cpp)
add_executable(foo_exec ${foo})
if(BUILD_CLIENT)
    include(cmake/BuildClient.cmake)
endif()

