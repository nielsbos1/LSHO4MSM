# How to create your own package

- Clone pybind11 repository in this folder
- Run commands below

```bash
cd build
cmake -DCMAKE_CXX_COMPILER="C:/msys64/mingw64/bin/g++"  -DCMAKE_C_COMPILER="C:/msys64/mingw64/bin/gcc" --debug-trycompile  .. -G "MinGW Makefiles"
cd ..
cmake --build build
```
