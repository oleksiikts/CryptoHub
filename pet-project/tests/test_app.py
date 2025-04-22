
import pytest
import requests
import time

BASE_URL = "http://127.0.0.1:5000"
ROUTES = ['/learn', '/etf', '/home', '/data']

@pytest.mark.parametrize("route", ROUTES)
def test_real_requests(route):
    url = BASE_URL + route
    print(f"\n🔍 Перевіряємо сторінку: {url}")
    try:
        response = requests.get(url)
        status = response.status_code

        if status == 200:
            print(f"✅ {route} — Успішно (200)")
            assert True
        elif 300 <= status < 400:
            print(f"↪️ {route} — Перенаправлення (код {status}), пропускаємо...")
            pytest.skip(f"Сторінка {route} має редірект (код {status})")
        else:
            print(f"❌ {route} — Помилка (код {status})")
            pytest.fail(f"{route} повернула помилку: {status}")

    except requests.exceptions.RequestException as e:
        print(f"❌ Помилка запиту: {e}")
        pytest.fail(f"Не вдалося зробити запит до {url}")
    
    time.sleep(10)
