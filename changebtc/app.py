from flask import Flask, render_template
import requests

app = Flask(__name__)

@app.route('/home')
def index():
    return render_template('index.html')

@app.route('/signin')
def signin_page():
    return render_template('signin.html')  # Створіть файл signin.html у вашій папці templates

@app.route('/signup')
def signup_page():
    return render_template('signup.html')  # Створіть файл signup.html у вашій папці templates

def get_crypto_data():
    url = 'https://www.okx.com/api/v5/market/tickers?instType=SWAP'  # URL до API
    try:
        response = requests.get(url)
        response.raise_for_status()  # Викликає виключення для поганих статус-кодів
        return response.json()  # Повертає дані у форматі JSON
    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        return {"code": "1", "msg": "Error fetching data", "data": []}  # Повертає код помилки

@app.route('/data')
def data_page():
    data = get_crypto_data()  # Викликаємо функцію для отримання даних через API

    # Перевіряємо, чи API повернуло коректний код
    if data['code'] == "0":
        return render_template('data.html', data=data)
    else:
        return "Error fetching data from API", 500

if __name__ == '__main__':
    app.run(debug=True)

#@app.route('/data'): Це декоратор Flask, який визначає маршрут /data. Коли користувач відвідує цю URL-адресу, викликається функція data_page().
#def data_page():: Це функція, яка обробляє запит на сторінку даних. Вона викликає функцію для отримання даних з API, перевіряє статус відповіді та рендерить шаблон data.html, передаючи в нього отримані дані.
#if __name__ == '__main__':: Це стандартна конструкція Python, яка дозволяє перевірити, чи запускається файл безпосередньо (не імпортується з іншого модуля). Якщо так, то виконується код, що йде нижче.
#app.run(debug=True): Цей рядок запускає сервер Flask у режимі налагодження (debug mode). Це означає, що, якщо виникне помилка, ви отримаєте детальну інформацію про неї в браузері, а також сервер автоматично перезавантажиться при зміні коду.