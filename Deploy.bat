@echo off
echo =======================================================
echo    Deploying Today's Newspapers to the Internet...
echo =======================================================
echo.
echo Make sure you have the following 4 files in this folder:
echo 1. et.pdf
echo 2. bs.pdf
echo 3. fe.pdf
echo 4. mint.pdf
echo.

cmd.exe /c npx netlify-cli deploy --prod --dir=. --site 2c877cbd-6fb4-410a-b66d-4b3761a219a4

echo.
echo =======================================================
echo                  DEPLOYMENT COMPLETE!
echo =======================================================
pause
