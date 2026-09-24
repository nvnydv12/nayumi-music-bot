@echo off
echo ====================================================
echo             LAVALINK V4 AUTO-DOWNLOADER
echo ====================================================
echo Downloading latest Lavalink.jar from official GitHub releases...
curl -L -o "%~dp0Lavalink.jar" "https://github.com/lavalink-devs/Lavalink/releases/latest/download/Lavalink.jar"
if %ERRORLEVEL% EQU 0 (
    echo.
    echo [SUCCESS] Lavalink.jar downloaded successfully!
    echo To start Lavalink, run: java -jar Lavalink.jar
) else (
    echo.
    echo [ERROR] Download failed. Please download Lavalink.jar manually from:
    echo https://github.com/lavalink-devs/Lavalink/releases
)
pause
