@echo off
:: Fill in these three values before running
set GIT_USERNAME=anshory1972
set GIT_EMAIL=arief.yusuf@gmail.com
set GITHUB_USERNAME=anshory1972

cd /d C:\WORK\economist

git config user.email "%GIT_EMAIL%"
git config user.name "%GIT_USERNAME%"

git add html\econdashboard.html html\bop.html html\financial.html
git commit -m "Update Indonesia Economic Dashboard"
git branch -M main
git remote remove origin 2>nul
git remote add origin https://github.com/%GITHUB_USERNAME%/econdashboard.git
git push -u origin main

echo.
echo Done! Now go to github.com/%GITHUB_USERNAME%/econdashboard
echo Settings -^> Pages -^> Source: main / root -^> Save
pause
