@echo off
REM Перехід до каталогу репозиторію
cd /d %~dp0

REM Перевірте, чи існує директорія .git
if not exist ".git" (
    echo Це не Git репозиторій. Перевірте, чи ви в правильній директорії.
    exit /b 1
)

REM Додайте всі зміни
git add .

REM Створіть коміт з повідомленням
set "message=fast commit"
git commit -m "fast push"

REM Пуште зміни на GitHub
git push origin main
