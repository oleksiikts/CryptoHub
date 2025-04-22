document.addEventListener('DOMContentLoaded', () => {
    // 1. Отримуємо активні монети з сервера
    fetch('/get_favorite_coins')  
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const activeCoins = data.active_coins;

                // Проходимо через усі зірочки на сторінці і вмикаємо їх для активних монет
                document.querySelectorAll('.favorite-star').forEach(star => {
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

    // 2. Обробка кнопок видалення монет з таблиці
    document.querySelectorAll('.delete-coin').forEach(button => {
        button.addEventListener('click', function () {
            const coin = button.getAttribute('data-coin');

            // Запит для видалення монети з обраних
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
                    // Якщо все вдалося, видаляємо рядок з таблиці
                    button.closest('tr').remove();
                    alert('Монету видалено з обраних');
                } else {
                    alert('Помилка при видаленні монети');
                }
            })
            .catch(error => {
                console.error('❌ Error in delete coin:', error);
            });
        });
    });

    // 3. Обробка кнопок зірочок для додавання/видалення монет
    document.querySelectorAll('.favorite-star').forEach(star => {
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

    // 4. Функція додавання в обране
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

    // 5. Функція для видалення монети з бази (через зірочку)
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
            }
        })
        .catch(error => {
            console.error('❌ Error in deactivateFavorite:', error);
        });
    }

    // 6. Покажемо кошик при наведенні на монету
    document.querySelectorAll('.coin-item').forEach(item => {
        const deleteIcon = item.querySelector('.delete-coin');

        item.addEventListener('mouseenter', () => {
            deleteIcon.style.display = 'inline-block'; // Змінюємо на display, щоб кошик став видимим
        });

        item.addEventListener('mouseleave', () => {
            deleteIcon.style.display = 'none'; // Сховуємо кошик
        });
    });
});
