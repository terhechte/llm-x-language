cmake_minimum_required(VERSION 3.10)
project(cpp_container)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Find required packages
find_package(CURL REQUIRED)
find_package(Threads REQUIRED)

# Add executable
add_executable(main src/main.cpp)

# Link libraries
target_link_libraries(main 
    ${CURL_LIBRARIES}
    ${CMAKE_THREAD_LIBS_INIT}
    pthread
)

# Include directories
target_include_directories(main PRIVATE ${CURL_INCLUDE_DIRS})