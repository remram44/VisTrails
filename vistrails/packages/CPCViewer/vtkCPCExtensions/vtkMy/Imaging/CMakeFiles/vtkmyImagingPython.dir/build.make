# CMAKE generated file: DO NOT EDIT!
# Generated by "Unix Makefiles" Generator, CMake Version 2.8

#=============================================================================
# Special targets provided by cmake.

# Disable implicit rules so canonical targets will work.
.SUFFIXES:

# Remove some rules from gmake that .SUFFIXES does not remove.
SUFFIXES =

.SUFFIXES: .hpux_make_needs_suffix_list

# Suppress display of executed commands.
$(VERBOSE).SILENT:

# A target that is always out of date.
cmake_force:
.PHONY : cmake_force

#=============================================================================
# Set environment variables for the build.

# The shell in which to execute make rules.
SHELL = /bin/sh

# The CMake executable.
CMAKE_COMMAND = "/Applications/CMake 2.8-12.app/Contents/bin/cmake"

# The command to remove a file.
RM = "/Applications/CMake 2.8-12.app/Contents/bin/cmake" -E remove -f

# Escaping for special characters.
EQUALS = =

# The program to use to edit the cache.
CMAKE_EDIT_COMMAND = "/Applications/CMake 2.8-12.app/Contents/bin/ccmake"

# The top-level source directory on which CMake was run.
CMAKE_SOURCE_DIR = /Developer/Projects/EclipseWorkspace/vistrails/vistrails/packages/CPCViewer/vtkCPCExtensions/vtkMy

# The top-level build directory on which CMake was run.
CMAKE_BINARY_DIR = /Developer/Projects/EclipseWorkspace/vistrails/vistrails/packages/CPCViewer/vtkCPCExtensions/vtkMy

# Include any dependencies generated for this target.
include Imaging/CMakeFiles/vtkmyImagingPython.dir/depend.make

# Include the progress variables for this target.
include Imaging/CMakeFiles/vtkmyImagingPython.dir/progress.make

# Include the compile flags for this target's objects.
include Imaging/CMakeFiles/vtkmyImagingPython.dir/flags.make

Imaging/vtkmyImagingPythonInit.cxx: /Developer/Projects/EclipseWorkspace/uvcdat/devel/install/build/ParaView-build/bin/vtkWrapPythonInit-pv4.1
Imaging/vtkmyImagingPythonInit.cxx: Imaging/vtkmyImagingPythonInit.data
	$(CMAKE_COMMAND) -E cmake_progress_report /Developer/Projects/EclipseWorkspace/vistrails/vistrails/packages/CPCViewer/vtkCPCExtensions/vtkMy/CMakeFiles $(CMAKE_PROGRESS_1)
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --blue --bold "Python Wrapping - generating vtkmyImagingPythonInit.cxx"
	cd /Developer/Projects/EclipseWorkspace/vistrails/vistrails/packages/CPCViewer/vtkCPCExtensions/vtkMy/Imaging && /Developer/Projects/EclipseWorkspace/uvcdat/devel/install/build/ParaView-build/bin/vtkWrapPythonInit-pv4.1 /Developer/Projects/EclipseWorkspace/vistrails/vistrails/packages/CPCViewer/vtkCPCExtensions/vtkMy/Imaging/vtkmyImagingPythonInit.data /Developer/Projects/EclipseWorkspace/vistrails/vistrails/packages/CPCViewer/vtkCPCExtensions/vtkMy/Imaging/vtkmyImagingPythonInit.cxx /Developer/Projects/EclipseWorkspace/vistrails/vistrails/packages/CPCViewer/vtkCPCExtensions/vtkMy/Imaging/vtkmyImagingPythonInitImpl.cxx

Imaging/vtkmyImagingPythonInitImpl.cxx: Imaging/vtkmyImagingPythonInit.cxx

Imaging/CMakeFiles/vtkmyImagingPython.dir/vtkmyImagingPythonInit.cxx.o: Imaging/CMakeFiles/vtkmyImagingPython.dir/flags.make
Imaging/CMakeFiles/vtkmyImagingPython.dir/vtkmyImagingPythonInit.cxx.o: Imaging/vtkmyImagingPythonInit.cxx
	$(CMAKE_COMMAND) -E cmake_progress_report /Developer/Projects/EclipseWorkspace/vistrails/vistrails/packages/CPCViewer/vtkCPCExtensions/vtkMy/CMakeFiles $(CMAKE_PROGRESS_2)
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green "Building CXX object Imaging/CMakeFiles/vtkmyImagingPython.dir/vtkmyImagingPythonInit.cxx.o"
	cd /Developer/Projects/EclipseWorkspace/vistrails/vistrails/packages/CPCViewer/vtkCPCExtensions/vtkMy/Imaging && /usr/bin/c++   $(CXX_DEFINES) $(CXX_FLAGS) -o CMakeFiles/vtkmyImagingPython.dir/vtkmyImagingPythonInit.cxx.o -c /Developer/Projects/EclipseWorkspace/vistrails/vistrails/packages/CPCViewer/vtkCPCExtensions/vtkMy/Imaging/vtkmyImagingPythonInit.cxx

Imaging/CMakeFiles/vtkmyImagingPython.dir/vtkmyImagingPythonInit.cxx.i: cmake_force
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green "Preprocessing CXX source to CMakeFiles/vtkmyImagingPython.dir/vtkmyImagingPythonInit.cxx.i"
	cd /Developer/Projects/EclipseWorkspace/vistrails/vistrails/packages/CPCViewer/vtkCPCExtensions/vtkMy/Imaging && /usr/bin/c++  $(CXX_DEFINES) $(CXX_FLAGS) -E /Developer/Projects/EclipseWorkspace/vistrails/vistrails/packages/CPCViewer/vtkCPCExtensions/vtkMy/Imaging/vtkmyImagingPythonInit.cxx > CMakeFiles/vtkmyImagingPython.dir/vtkmyImagingPythonInit.cxx.i

Imaging/CMakeFiles/vtkmyImagingPython.dir/vtkmyImagingPythonInit.cxx.s: cmake_force
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green "Compiling CXX source to assembly CMakeFiles/vtkmyImagingPython.dir/vtkmyImagingPythonInit.cxx.s"
	cd /Developer/Projects/EclipseWorkspace/vistrails/vistrails/packages/CPCViewer/vtkCPCExtensions/vtkMy/Imaging && /usr/bin/c++  $(CXX_DEFINES) $(CXX_FLAGS) -S /Developer/Projects/EclipseWorkspace/vistrails/vistrails/packages/CPCViewer/vtkCPCExtensions/vtkMy/Imaging/vtkmyImagingPythonInit.cxx -o CMakeFiles/vtkmyImagingPython.dir/vtkmyImagingPythonInit.cxx.s

Imaging/CMakeFiles/vtkmyImagingPython.dir/vtkmyImagingPythonInit.cxx.o.requires:
.PHONY : Imaging/CMakeFiles/vtkmyImagingPython.dir/vtkmyImagingPythonInit.cxx.o.requires

Imaging/CMakeFiles/vtkmyImagingPython.dir/vtkmyImagingPythonInit.cxx.o.provides: Imaging/CMakeFiles/vtkmyImagingPython.dir/vtkmyImagingPythonInit.cxx.o.requires
	$(MAKE) -f Imaging/CMakeFiles/vtkmyImagingPython.dir/build.make Imaging/CMakeFiles/vtkmyImagingPython.dir/vtkmyImagingPythonInit.cxx.o.provides.build
.PHONY : Imaging/CMakeFiles/vtkmyImagingPython.dir/vtkmyImagingPythonInit.cxx.o.provides

Imaging/CMakeFiles/vtkmyImagingPython.dir/vtkmyImagingPythonInit.cxx.o.provides.build: Imaging/CMakeFiles/vtkmyImagingPython.dir/vtkmyImagingPythonInit.cxx.o

# Object files for target vtkmyImagingPython
vtkmyImagingPython_OBJECTS = \
"CMakeFiles/vtkmyImagingPython.dir/vtkmyImagingPythonInit.cxx.o"

# External object files for target vtkmyImagingPython
vtkmyImagingPython_EXTERNAL_OBJECTS =

bin/vtkmyImagingPython.so: Imaging/CMakeFiles/vtkmyImagingPython.dir/vtkmyImagingPythonInit.cxx.o
bin/vtkmyImagingPython.so: Imaging/CMakeFiles/vtkmyImagingPython.dir/build.make
bin/vtkmyImagingPython.so: bin/libvtkmyImagingPythonD.dylib
bin/vtkmyImagingPython.so: bin/libvtkmyImaging.dylib
bin/vtkmyImagingPython.so: bin/libvtkmyCommonPythonD.dylib
bin/vtkmyImagingPython.so: bin/libvtkmyCommon.dylib
bin/vtkmyImagingPython.so: Imaging/CMakeFiles/vtkmyImagingPython.dir/link.txt
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --red --bold "Linking CXX shared module ../bin/vtkmyImagingPython.so"
	cd /Developer/Projects/EclipseWorkspace/vistrails/vistrails/packages/CPCViewer/vtkCPCExtensions/vtkMy/Imaging && $(CMAKE_COMMAND) -E cmake_link_script CMakeFiles/vtkmyImagingPython.dir/link.txt --verbose=$(VERBOSE)

# Rule to build all files generated by this target.
Imaging/CMakeFiles/vtkmyImagingPython.dir/build: bin/vtkmyImagingPython.so
.PHONY : Imaging/CMakeFiles/vtkmyImagingPython.dir/build

Imaging/CMakeFiles/vtkmyImagingPython.dir/requires: Imaging/CMakeFiles/vtkmyImagingPython.dir/vtkmyImagingPythonInit.cxx.o.requires
.PHONY : Imaging/CMakeFiles/vtkmyImagingPython.dir/requires

Imaging/CMakeFiles/vtkmyImagingPython.dir/clean:
	cd /Developer/Projects/EclipseWorkspace/vistrails/vistrails/packages/CPCViewer/vtkCPCExtensions/vtkMy/Imaging && $(CMAKE_COMMAND) -P CMakeFiles/vtkmyImagingPython.dir/cmake_clean.cmake
.PHONY : Imaging/CMakeFiles/vtkmyImagingPython.dir/clean

Imaging/CMakeFiles/vtkmyImagingPython.dir/depend: Imaging/vtkmyImagingPythonInit.cxx
Imaging/CMakeFiles/vtkmyImagingPython.dir/depend: Imaging/vtkmyImagingPythonInitImpl.cxx
	cd /Developer/Projects/EclipseWorkspace/vistrails/vistrails/packages/CPCViewer/vtkCPCExtensions/vtkMy && $(CMAKE_COMMAND) -E cmake_depends "Unix Makefiles" /Developer/Projects/EclipseWorkspace/vistrails/vistrails/packages/CPCViewer/vtkCPCExtensions/vtkMy /Developer/Projects/EclipseWorkspace/vistrails/vistrails/packages/CPCViewer/vtkCPCExtensions/vtkMy/Imaging /Developer/Projects/EclipseWorkspace/vistrails/vistrails/packages/CPCViewer/vtkCPCExtensions/vtkMy /Developer/Projects/EclipseWorkspace/vistrails/vistrails/packages/CPCViewer/vtkCPCExtensions/vtkMy/Imaging /Developer/Projects/EclipseWorkspace/vistrails/vistrails/packages/CPCViewer/vtkCPCExtensions/vtkMy/Imaging/CMakeFiles/vtkmyImagingPython.dir/DependInfo.cmake --color=$(COLOR)
.PHONY : Imaging/CMakeFiles/vtkmyImagingPython.dir/depend

