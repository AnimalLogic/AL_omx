CMAKE_MINIMUM_REQUIRED(VERSION 2.8)

include(RezBuild)

rez_find_packages(PREFIX pkgs AUTO)

add_pythonlibs_build(PACKAGE AL.omx MAKE_WHEEL NO_TESTS)
