@echo off
REM AI-First SDLC Claude Launcher for Windows
REM One command to set up everything and start Claude Code
REM Usage: bin\claude.bat

setlocal enabledelayedexpansion

REM Determine project root (parent of bin directory)
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%\.."
set PROJECT_ROOT=%CD%
for %%I in ("%PROJECT_ROOT%") do set PROJECT_NAME=%%~nxI

REM Configuration
if "%VENV_DIR%"=="" set VENV_DIR=%PROJECT_ROOT%\venv

REM Banner
echo.
echo ========================================================
echo          AI-First SDLC Claude Launcher
echo ========================================================
echo.

REM Change to project directory
cd /d "%PROJECT_ROOT%"
echo Project: %PROJECT_NAME%
echo Location: %PROJECT_ROOT%

REM Check if Python project
if exist "requirements.txt" goto :python_project
if exist "setup.py" goto :python_project
if exist "pyproject.toml" goto :python_project
if exist "Pipfile" goto :python_project
goto :non_python

:python_project
echo Python project detected
echo.

REM Find Python
where python >nul 2>nul
if errorlevel 1 (
    where python3 >nul 2>nul
    if errorlevel 1 (
        echo Error: Python not found
        echo Please install Python from https://python.org
        pause
        exit /b 1
    ) else (
        set PYTHON_CMD=python3
    )
) else (
    set PYTHON_CMD=python
)

REM Check/create virtual environment
if not exist "%VENV_DIR%\Scripts\activate.bat" (
    echo Creating virtual environment...
    !PYTHON_CMD! -m venv "%VENV_DIR%"
    if errorlevel 1 (
        echo Error: Failed to create virtual environment
        pause
        exit /b 1
    )

    call "%VENV_DIR%\Scripts\activate.bat"

    echo Upgrading pip...
    python -m pip install --upgrade pip --quiet

    if exist "requirements.txt" (
        echo Installing requirements...
        pip install -r requirements.txt
    )

    if exist "requirements-dev.txt" (
        echo Installing dev requirements...
        pip install -r requirements-dev.txt
    )

    echo Virtual environment ready
) else (
    call "%VENV_DIR%\Scripts\activate.bat"
    echo Virtual environment activated
)

echo Python:
where python
python --version
goto :check_claude

:non_python
echo Non-Python project
echo.

:check_claude
REM Check for Claude CLI
where claude >nul 2>nul
if errorlevel 1 (
    echo.
    echo Error: Claude CLI not found
    echo.
    echo Please install Claude Code:
    echo.
    echo   Windows:
    echo     Visit https://claude.ai/download
    echo.
    pause
    exit /b 1
)

REM Display helpful context
echo.
echo ========================================================
echo Ready to start Claude Code!
echo ========================================================
echo.
echo Quick tips:
echo   - Claude will start in: %PROJECT_ROOT%
if exist "requirements.txt" (
    echo   - Python environment is activated
    echo   - All dependencies from requirements.txt are installed
)
echo   - Type 'exit' in Claude to return here
echo.
echo ========================================================
echo.

REM Launch Claude Code
echo Launching Claude Code...
echo.

REM Start Claude in the project directory
claude "%PROJECT_ROOT%"
