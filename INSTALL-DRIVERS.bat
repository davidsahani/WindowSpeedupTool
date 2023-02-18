@echo off
title GetAdmin Privilege
cd /d "%~dp0"

rem Delete the temporary VBS file if it already exists
if exist "%temp%\getadmin.vbs" (
    del "%temp%\getadmin.vbs"
)

rem check if script is running as admin
fsutil dirty query %systemdrive% > nul 2> nul

rem If the error level is not 0, create a VBS file to run the batch file as admin
if %errorlevel%==1 (
	echo Set UAC = CreateObject^("Shell.Application"^) : > "%temp%\getadmin.vbs"
	echo UAC.ShellExecute "cmd.exe", "/k cd ""%~sdp0"" && ""%~s0"" %params%", "", "runas", 1 >> "%temp%\getadmin.vbs"
	"%temp%\getadmin.vbs"
	exit
)


title DRIVERS-INSTALL
color A

echo INSTALLING DRIVERS...
for /F "tokens=3,* delims== " %%a in ('"dir /s *.inf ^ | findstr "Directory""') do (
	for /F "tokens=5,* delims== " %%b in ('"dir %%a ^ | findstr ".inf"$"') do (
		pnputil /add-driver %%a\%%b /install
	)
)

echo. Drivers installation finished
echo.
pause
