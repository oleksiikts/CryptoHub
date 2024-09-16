# Перехід до каталогу репозиторію
cd (Split-Path -Path $MyInvocation.MyCommand.Definition -Parent)

# Перевірте, чи існує директорія .git
if (-not (Test-Path ".git")) {
    Write-Host "Це не Git репозиторій. Перевірте, чи ви в правильній директорії."
    exit 1
}

# Додайте всі зміни
git add .

# Створіть коміт з поточним часом як повідомлення
$message = "fast commit"
git commit -m $message

# Пуште зміни на GitHub
git push origin main