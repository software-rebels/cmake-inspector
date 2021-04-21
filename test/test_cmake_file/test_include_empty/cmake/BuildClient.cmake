if(FEATURE_RENDERER2 AND NOT BUILD_CLIENT)
    set(shdr2h_src somefile.cpp)
endif()
add_executable(shdr2h ${shdr2h_src})