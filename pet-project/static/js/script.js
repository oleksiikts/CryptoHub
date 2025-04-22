document.addEventListener('DOMContentLoaded', () => {
    // 🔐 Перевіряємо, чи на сторінці є зірочки
    const favoriteStars = document.querySelectorAll('.favorite-star');
    if (favoriteStars.length > 0) {

        // 1. Отримуємо активні монети з сервера
        fetch('/get_favorite_coins')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const activeCoins = data.active_coins;

                    // Проходимо через усі зірочки на сторінці і вмикаємо їх для активних монет
                    favoriteStars.forEach(star => {
                        const coin = star.getAttribute('data-coin');
                        if (activeCoins.includes(coin)) {
                            star.classList.add('active');
                            star.innerHTML = '★';
                        } else {
                            star.classList.remove('active');
                            star.innerHTML = '☆';
                        }
                    });
                } else {
                    console.warn("Не вдалося отримати активні монети");
                }
            })
            .catch(error => {
                console.error('❌ Error while fetching active coins:', error);
            });

        // 2. Обробка кліків по зірочках
        favoriteStars.forEach(star => {
            const coin = star.getAttribute('data-coin');

            star.addEventListener('click', function () {
                const isActive = star.classList.contains('active');

                if (isActive) {
                    deactivateFavorite(coin, star);
                } else {
                    addToFavorites(coin, star);
                }
            });
        });
    }

    // 3. Функція додавання в обране
    function addToFavorites(coin, button) {
        fetch('/add_to_favorites', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify({ coin: coin }),
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                button.classList.add('active');  
                button.innerHTML = '★';          
            } else {
                console.warn("Монета вже додана або інша помилка:", data.error);
            }
        })
        .catch(error => {
            console.error('❌ Error in addToFavorites:', error);
        });
    }

    // 4. Функція для видалення монети з бази (через зірочку)
    function deactivateFavorite(coin, button) {
        fetch('/deactivate_favorite', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ coin: coin }),
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                button.classList.remove('active');  
                button.innerHTML = '☆';
    
                // 🔥 Видаляємо рядок монети з таблиці (використовуємо .closest('tr'))
                const row = button.closest('tr');
                if (row) {
                    row.remove();
                }
            }
        })
        .catch(error => {
            console.error('❌ Error in deactivateFavorite:', error);
        });
    }
    

    // 5. Обробка кнопок для аналізу монет
    const analyzeButtons = document.querySelectorAll('.analyze-btn');
    if (analyzeButtons.length > 0) {
        analyzeButtons.forEach(button => {
            button.addEventListener('click', function () {
                const coin = this.dataset.coin;

                fetch('/api/analyze_coin', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ coin })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        const analysisCell = document.getElementById(`analysis-${coin}`);
                        const explanationCell = document.getElementById(`explanation-${coin}`);

                        analysisCell.textContent = data.analysis;
                        explanationCell.textContent = data.explanation;  // Оновлюємо пояснення
                    } else {
                        alert('Помилка при аналізі: ' + data.error);
                    }
                })
                .catch(error => {
                    console.error('❌ Fetch error:', error);
                    alert('Помилка з’єднання з сервером.');
                });
            });
        });
    }

    // 6. Клікабельні рядки для переходу на сторінку з графіком
    const rows = document.querySelectorAll(".clickable-row");
    rows.forEach(row => {
        row.style.cursor = "pointer";
        row.addEventListener("click", () => {
            window.location = row.getAttribute("data-href");
        });
    });

});
