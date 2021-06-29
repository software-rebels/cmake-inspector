add_library(goo goo.cpp)
if(AT_SUB)
    target_compile_definitions(goo PUBLIC test)
endif(AT_SUB)    