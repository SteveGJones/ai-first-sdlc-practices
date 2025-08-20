@echo off
REM Virtual Environment Runner for AI-First SDLC Python Projects
REM Auto-activates virtual environment and runs commands in that context
REM Perfect for AI agents like Claude to run Python commands safely

setlocal enabledelayedexpansion

REM Configuration
if "%VENV_DIR%"=="" set VENV_DIR=venv

REM Change to script directory
cd /d "%~dp0"

REM Check if venv exists
if not exist "%VENV_DIR%\Scripts\activate.bat" (
    echo Warning: Virtual environment not found at '%VENV_DIR%'
    echo Creating virtual environment...
    
    REM Find Python
    where python >nul 2>nul
    if errorlevel 1 (
        where python3 >nul 2>nul
        if errorlevel 1 (
            echo Error: Python not found. Please install Python 3.7+
            exit /b 1
        ) else (
            set PYTHON_CMD=python3
        )
    ) else (
        set PYTHON_CMD=python
    )
    
    REM Create venv
    !PYTHON_CMD! -m venv "%VENV_DIR%"
    if errorlevel 1 (
        echo Error: Failed to create virtual environment
        exit /b 1
    )
    
    REM Activate venv
    call "%VENV_DIR%\Scripts\activate.bat"
    
    REM Upgrade pip
    echo Upgrading pip...
    python -m pip install --upgrade pip --quiet
    
    REM Install requirements if exists
    if exist "requirements.txt" (
        echo Installing requirements.txt...
        pip install -r requirements.txt
        if errorlevel 1 (
            echo Warning: Some requirements failed to install
        ) else (
            echo Requirements installed successfully
        )
    )
    
    REM Install dev requirements if exists
    if exist "requirements-dev.txt" (
        echo Installing requirements-dev.txt...
        pip install -r requirements-dev.txt
        if errorlevel 1 (
            echo Warning: Some dev requirements failed to install
        ) else (
            echo Dev requirements installed successfully
        )
    )
    
    echo Virtual environment created and configured
) else (
    REM Just activate existing venv
    call "%VENV_DIR%\Scripts\activate.bat"
)

REM Show environment info if requested
if "%1"=="--info" (
    echo Python: 
    where python
    echo Version:
    python --version
    echo Venv: %VIRTUAL_ENV%
    if not "%2"=="" (
        shift
    )
)

REM Execute command or start shell
if "%1"=="" (
    echo No command provided. Starting command prompt with venv activated...
    echo Python: 
    where python
    echo.
    echo Type 'exit' to leave the virtual environment
    cmd /k
) else (
    REM Remove --info flag if it was the only argument
    if "%1"=="--info" (
        if "%2"=="" (
            exit /b 0
        )
        REM Shift arguments to skip --info
        shift
    )
    
    REM Build command from all arguments
    set cmd_line=%1
    shift
    :build_loop
    if not "%1"=="" (
        set cmd_line=!cmd_line! %1
        shift
        goto build_loop
    )
    
    REM Execute the command
    !cmd_line!
)