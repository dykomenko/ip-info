@echo off
chcp 65001 >nul
title IP Info
python "%~dp0ip_info.py" %*
