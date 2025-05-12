@echo off
echo Compiling SuffixKART backend...

REM Create include directory if it doesn't exist
if not exist "include" mkdir include

REM Check if json.hpp exists in the include directory, if not download it
if not exist "include\json.hpp" (
    echo Downloading nlohmann/json library...
    powershell -Command "Invoke-WebRequest -Uri 'https://github.com/nlohmann/json/releases/download/v3.11.3/json.hpp' -OutFile 'include\json.hpp'"
    echo Download complete.
)

REM Attempt to delete existing backend.exe if it exists
if exist "backend.exe" (
    echo Attempting to remove existing backend.exe...
    del /f backend.exe
    if exist "backend.exe" (
        echo Could not delete existing backend.exe, using new_backend.exe instead
        set OUTPUT_NAME=new_backend.exe
    ) else (
        set OUTPUT_NAME=backend.exe
    )
) else (
    set OUTPUT_NAME=backend.exe
)

REM Compile the backend executable
echo Compiling to %OUTPUT_NAME%...
g++ -std=c++17 main.cpp bloom.cpp BK_Tree.cpp Suffix_tree.c PatternSearch.c -o %OUTPUT_NAME%

if %ERRORLEVEL% neq 0 (
    echo Compilation failed
    exit /b 1
)

echo Compilation successful! Backend executable created as %OUTPUT_NAME%
echo You can now run the Flask application with: python app.py
echo.
echo If you compiled to new_backend.exe, update app.py to use that filename 