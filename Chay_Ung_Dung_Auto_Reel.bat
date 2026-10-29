@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Auto Reel Sách Hay Mỗi Ngày
if exist "AutoReelSachHay_v13.exe" (
    start "" "AutoReelSachHay_v13.exe" %*
) else if exist "dist\AutoReelSachHay\AutoReelSachHay_v13.exe" (
    start "" "dist\AutoReelSachHay\AutoReelSachHay_v13.exe" %*
) else if exist "AutoReelSachHay_v12.exe" (
    start "" "AutoReelSachHay_v12.exe" %*
) else if exist "dist\AutoReelSachHay\AutoReelSachHay_v12.exe" (
    start "" "dist\AutoReelSachHay\AutoReelSachHay_v12.exe" %*
) else if exist "AutoReelSachHay_v11.exe" (
    start "" "AutoReelSachHay_v11.exe" %*
) else if exist "dist\AutoReelSachHay\AutoReelSachHay_v11.exe" (
    start "" "dist\AutoReelSachHay\AutoReelSachHay_v11.exe" %*
) else if exist "AutoReelSachHay_v10.exe" (
    start "" "AutoReelSachHay_v10.exe" %*
) else if exist "dist\AutoReelSachHay\AutoReelSachHay_v10.exe" (
    start "" "dist\AutoReelSachHay\AutoReelSachHay_v10.exe" %*
) else if exist "AutoReelSachHay_v9.exe" (
    start "" "AutoReelSachHay_v9.exe" %*
) else if exist "dist\AutoReelSachHay\AutoReelSachHay_v9.exe" (
    start "" "dist\AutoReelSachHay\AutoReelSachHay_v9.exe" %*
) else if exist "AutoReelSachHay_v8.exe" (
    start "" "AutoReelSachHay_v8.exe" %*
) else if exist "dist\AutoReelSachHay\AutoReelSachHay_v8.exe" (
    start "" "dist\AutoReelSachHay\AutoReelSachHay_v8.exe" %*
) else if exist "AutoReelSachHay_v7.exe" (
    start "" "AutoReelSachHay_v7.exe"
) else if exist "AutoReelSachHay_v6.exe" (
    start "" "AutoReelSachHay_v6.exe"
) else if exist "AutoReelSachHay_v5.exe" (
    start "" "AutoReelSachHay_v5.exe"
) else if exist "AutoReelSachHay_v4.exe" (
    start "" "AutoReelSachHay_v4.exe"
) else if exist "AutoReelSachHay_v3.exe" (
    start "" "AutoReelSachHay_v3.exe"
) else if exist "AutoReelSachHay_v2.exe" (
    start "" "AutoReelSachHay_v2.exe"
) else if exist "AutoReelSachHay.exe" (
    start "" "AutoReelSachHay.exe"
) else if exist "dist\AutoReelSachHay\AutoReelSachHay_v7.exe" (
    start "" "dist\AutoReelSachHay\AutoReelSachHay_v7.exe"
) else if exist "dist\AutoReelSachHay\AutoReelSachHay_v6.exe" (
    start "" "dist\AutoReelSachHay\AutoReelSachHay_v6.exe"
) else if exist "dist\AutoReelSachHay\AutoReelSachHay_v5.exe" (
    start "" "dist\AutoReelSachHay\AutoReelSachHay_v5.exe"
) else if exist "dist\AutoReelSachHay\AutoReelSachHay_v4.exe" (
    start "" "dist\AutoReelSachHay\AutoReelSachHay_v4.exe"
) else if exist "dist\AutoReelSachHay\AutoReelSachHay_v3.exe" (
    start "" "dist\AutoReelSachHay\AutoReelSachHay_v3.exe"
) else if exist "dist\AutoReelSachHay\AutoReelSachHay_v2.exe" (
    start "" "dist\AutoReelSachHay\AutoReelSachHay_v2.exe"
) else if exist "dist\AutoReelSachHay\AutoReelSachHay.exe" (
    start "" "dist\AutoReelSachHay\AutoReelSachHay.exe"
) else (
    python -X utf8 app.py
)
