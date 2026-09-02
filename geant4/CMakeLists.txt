cmake_minimum_required(VERSION 3.16)

project(
    VoyagerProtonShielding
    VERSION 0.1.0
    LANGUAGES CXX
)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

find_package(Geant4 REQUIRED)

include(${Geant4_USE_FILE})

file(GLOB PROJECT_SOURCES CONFIGURE_DEPENDS
    ${PROJECT_SOURCE_DIR}/src/*.cc
)

file(GLOB PROJECT_HEADERS CONFIGURE_DEPENDS
    ${PROJECT_SOURCE_DIR}/include/*.hh
)

add_executable(
    voyager_geant4
    main.cc
    ${PROJECT_SOURCES}
    ${PROJECT_HEADERS}
)

target_include_directories(
    voyager_geant4
    PRIVATE
    ${PROJECT_SOURCE_DIR}/include
)

target_link_libraries(
    voyager_geant4
    PRIVATE
    ${Geant4_LIBRARIES}
)
