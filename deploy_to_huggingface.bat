@echo off
REM Aethel Judge - Hugging Face Deployment Script
REM This script prepares and deploys Aethel Judge to Hugging Face Spaces

echo ========================================
echo Aethel Judge - HuggingFace Deployment
echo ========================================
echo.

REM Check if HF Space directory exists
if not exist "aethel-judge" (
    echo Cloning Hugging Face Space repository...
    git clone https://huggingface.co/spaces/diotec/aethel-judge
    if errorlevel 1 (
        echo ERROR: Failed to clone repository
        echo Please make sure you have access to the Space
        pause
        exit /b 1
    )
) else (
    echo Space directory already exists, updating...
    cd aethel-judge
    git pull
    cd ..
)

echo.
echo Copying files to Space directory...

REM Copy core application
xcopy /E /I /Y aethel aethel-judge\aethel
xcopy /E /I /Y api aethel-judge\api

REM Copy configuration files
copy /Y requirements.txt aethel-judge\requirements.txt
copy /Y Dockerfile.huggingface aethel-judge\Dockerfile
copy /Y README_HF.md aethel-judge\README.md
copy /Y .dockerignore aethel-judge\.dockerignore

REM Create vault directories
if not exist "aethel-judge\.aethel_vault\bundles" mkdir aethel-judge\.aethel_vault\bundles
if not exist "aethel-judge\.aethel_vault\certificates" mkdir aethel-judge\.aethel_vault\certificates

echo.
echo Files copied successfully!
echo.
echo ========================================
echo Ready to deploy!
echo ========================================
echo.
echo Next steps:
echo 1. cd aethel-judge
echo 2. git add .
echo 3. git commit -m "Deploy Aethel Judge v1.3"
echo 4. git push
echo.
echo Your Space will be available at:
echo https://huggingface.co/spaces/diotec/aethel-judge
echo.
echo Would you like to commit and push now? (Y/N)
set /p DEPLOY=

if /i "%DEPLOY%"=="Y" (
    cd aethel-judge
    git add .
    git commit -m "Deploy Aethel Judge v1.3 - Formal Verification System"
    git push
    if errorlevel 1 (
        echo.
        echo ERROR: Push failed. You may need to authenticate.
        echo Run: git config credential.helper store
        echo Then try pushing again manually.
        pause
        exit /b 1
    )
    echo.
    echo ========================================
    echo Deployment successful! 🎉
    echo ========================================
    echo.
    echo Your Space is building at:
    echo https://huggingface.co/spaces/diotec/aethel-judge
    echo.
    echo Check the build logs in the Space interface.
    cd ..
) else (
    echo.
    echo Deployment prepared but not pushed.
    echo Run the commands manually when ready.
)

echo.
pause
