from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_login import LoginManager, login_required, current_user, UserMixin, login_user, logout_user
import sqlite3
import re
import ccxt
import pandas as pd
import numpy as np
import feedparser  # RSS parser
import pytz
from datetime import datetime
from crypto_analysis import train_and_predict
import plotly.graph_objects as go
import plotly.io as pio
import requests
from db import (
    register_user, add_favorite, remove_favorite,
    get_favorites, get_user_by_email, get_user_by_id,
    get_active_favorites, deactivate_favorite_coin,
    delete_favorite_coin
)

app = Flask(__name__)
app.secret_key = 'hello'

### LOGIN MANAGER ###
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'signin_page'

class User(UserMixin):
    def __init__(self, id, email, login, password, phone):
        self.id = id
        self.email = email
        self.login = login
        self.password = password
        self.phone = phone

@login_manager.user_loader
def load_user(user_id):
    user_data = get_user_by_id(user_id)
    if user_data:
        return User(*user_data)
    return None

@login_manager.unauthorized_handler
def unauthorized():
    if request.is_json:
        return jsonify(success=False, error="Unauthorized"), 401
    return redirect(url_for('signin_page'))


### VALIDATION ###
def validate_phone(phone):
    pattern = r'^\+380\d{9}$'
    return re.match(pattern, phone) is not None


### AUTH ROUTES ###
@app.route('/signin', methods=['GET', 'POST'])
def signin_page():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user_data = get_user_by_email(email)
        if user_data and password == user_data[3]:
            user = User(*user_data)
            login_user(user)
            return redirect(url_for('profile_page'))
        flash('Невірний email або пароль.')
    return render_template('signin.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup_page():
    if request.method == 'POST':
        email = request.form['email']
        login = request.form['login']
        password = request.form['password']
        phone = request.form['phone']

        if not validate_phone(phone):
            flash('Невірний формат номера телефону. Використовуйте формат +380XXXXXXXXX.')
            return render_template('signup.html')

        try:
            register_user(email, login, password, phone)
            flash('Реєстрація успішна!')
            return redirect(url_for('signin_page'))
        except sqlite3.IntegrityError:
            flash('Користувач з таким email вже існує.')

    return render_template('signup.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Ви вийшли з системи.')
    return redirect(url_for('signin_page'))


### FAVORITES ###
@app.route('/add_to_favorites', methods=['POST'])
@login_required
def add_to_favorites():
    try:
        data = request.get_json()
        coin = data.get('coin', '').upper()
        if not coin:
            return jsonify(success=False, error="No coin provided"), 400

        add_favorite(current_user.id, coin)
        return jsonify(success=True)
    except Exception as e:
        return jsonify(success=False, error=str(e)), 500

@app.route('/remove_from_favorites', methods=['POST'])
@login_required
def remove_from_favorites():
    data = request.get_json()
    coin = data['coin'].upper()
    remove_favorite(current_user.id, coin)
    return jsonify(success=True)

@app.route('/deactivate_favorite', methods=['POST'])
@login_required
def deactivate_favorite():
    data = request.get_json()
    coin = data['coin'].upper()
    deactivate_favorite_coin(current_user.id, coin)
    return jsonify(success=True)

@app.route('/get_favorite_coins', methods=['GET'])
@login_required
def get_favorite_coins():
    try:
        active_coins = get_active_favorites(current_user.id)
        return jsonify(success=True, active_coins=active_coins)
    except Exception as e:
        return jsonify(success=False, error=str(e)), 500


### PROFILE & ANALYSIS ###
@app.route('/profile')
@login_required
def profile_page():
    favorites = get_favorites(current_user.id)
    favorite_coins = [coin for coin, active in favorites if active]
    favorites_data = []

    for coin in favorite_coins:
        try:
            decision_results = train_and_predict(coin + '/USDT')
            conclusion = decision_results['1h']['decision']
            explanation = decision_results['1h']['explanation']
        except Exception as e:
            conclusion = "Помилка аналізу"
            explanation = str(e)

        favorites_data.append({
            'name': coin,
            'last_price': get_last_price(coin),
            'technical_analysis': conclusion,
            'explanation': explanation
        })

    return render_template('profile.html', favorites=favorites_data, favorite_names=favorite_coins)


@app.route('/get_trade_decision', methods=['GET'])
@login_required
def get_trade_decision():
    decision_results = train_and_predict('BTC/USDT')
    return render_template('result.html', symbol='BTC/USDT', decision_results=decision_results)


@app.route('/api/analyze_coin', methods=['POST'])
@login_required
def analyze_coin():
    data = request.get_json()
    coin = data.get('coin')
    if not coin:
        return jsonify(success=False, error="No coin provided")

    try:
        result = train_and_predict(coin + '/USDT')
        decision = result['1h']['decision']
        return jsonify(success=True, analysis=decision)
    except Exception as e:
        return jsonify(success=False, error=str(e)), 500

def get_last_price(symbol):
    exchange = ccxt.binance()
    try:
        ticker = exchange.fetch_ticker(symbol + '/USDT')
        return ticker['last']
    except Exception as e:
        print(f"Error fetching data for {symbol}: {e}")
        return None





def calculate_rsi(data, window=14):
    """Обчислює RSI для даного DataFrame."""
    delta = data['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

@app.route('/home')
def home():
    cointelegraph_news = get_cointelegraph_news()
    return render_template('index.html', cointelegraph_news=cointelegraph_news)


### NEWS ###
def get_cointelegraph_news():
    url = "https://cointelegraph.com/rss"
    feed = feedparser.parse(url)
    news_list = []
    local_tz = pytz.timezone("Europe/Kyiv")

    for entry in feed.entries[:15]:
        utc_time = datetime.strptime(entry.published, "%a, %d %b %Y %H:%M:%S %z")
        local_time = utc_time.astimezone(local_tz).strftime("%d-%m-%Y %H:%M")
        news_list.append({
            "title": entry.title,
            "link": entry.link,
            "published": local_time
        })
    return news_list

@app.route('/cointelegraph-news')
def cointelegraph_news():
    news_data = get_cointelegraph_news()
    return render_template("cointelegraph_news.html", news=news_data)


### STATIC PAGES ###
@app.route('/learn')
def learn_page():
    return render_template('learn.html')

@app.route('/learn/indicators')
def indicators_page():
    return render_template('indicators.html')

@app.route('/stock-vs-crypto')
def stock_vs_crypto():
    return render_template('stock_vs_crypto.html')

@app.route("/newbie-tips")
def newbie_tips_page():
    return render_template("newbie_tips.html")






def format_large_number(value):
    try:
        num = float(value)
        if num >= 1_000_000_000_000:
            return f"${num / 1_000_000_000_000:.2f}T"
        elif num >= 1_000_000_000:
            return f"${num / 1_000_000_000:.2f}B"
        elif num >= 1_000_000:
            return f"${num / 1_000_000:.2f}M"
        else:
            return f"${num:,.2f}"
    except:
        return "N/A"

app.jinja_env.filters['format_large'] = format_large_number


def format_price(value):
    try:
        return f"${float(value):,.2f}"
    except:
        return "N/A"

app.jinja_env.filters['format_price'] = format_price


### PRICE FETCHING ###
def get_last_price(coin):
    exchange = ccxt.binance()
    ticker = exchange.fetch_ticker(coin + '/USDT')
    return round(ticker['last'], 2)






def get_market_data_binance(symbol):
    exchange = ccxt.binance()
    try:
        ticker = exchange.fetch_ticker(symbol + '/USDT')
        volume_24h = ticker['quoteVolume']
        price = ticker['last']
        market_cap = price * volume_24h
        return market_cap, volume_24h
    except Exception as e:
        print(f"Error fetching market data for {symbol}: {e}")
        return None, None


@app.route('/data', methods=['GET'])
def data_page():
    # Список монет для відображення
    coins = ['BTC', 'ETH', 'XRP', 'LTC', 'BNB', 'SOL', 'ADA', 'DOGE', 'DOT', 'PEPE', 'NEAR', 'KAS', 'ARB', 'ATOM', 'SHIB', 'XLM']
    
    data = {}
    
    for coin in coins:
        last_price = get_last_price(coin)
        market_cap, volume_24h = get_market_data_binance(coin)
        
        # Додаємо дані для кожної монети в словник
        data[coin] = {
            'last_price': last_price,
            'market_cap': market_cap,
            'volume_24h': volume_24h
        }
    
    Передаємо дані для всіх монет у шаблон
   return render_template('data.html', coins_data=data)




@app.route('/chart/<coin_name>')
def chart(coin_name):
    # Підключення до біржі для отримання даних
    exchange = ccxt.binance()
    symbol = f'{coin_name}/USDT'  # Вставляємо назву монети в символ
    ohlcv = exchange.fetch_ohlcv(symbol, '1h')  # Отримуємо дані за годину

    # Перетворюємо дані в DataFrame
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

    # Створення графіка
    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=df['timestamp'],
        open=df['open'],
        high=df['high'],
        low=df['low'],
        close=df['close'],
        name=coin_name
    ))

    # Додавання індикатора RSI
    df['RSI'] = calculate_rsi(df)

    # Додавання RSI на графік
    fig.add_trace(go.Scatter(
        x=df['timestamp'],
        y=df['RSI'],
        mode='lines',
        name="RSI",
        line=dict(color='orange'),
        yaxis="y2"
    ))

    # Параметри для графіка
    fig.update_layout(
        title=f"{coin_name}/USDT Analysis",
        xaxis_title="Time",
        yaxis_title="Price",
        yaxis2=dict(
            title="RSI",
            overlaying="y",
            side="right"
        ),
        hovermode="x unified",
        annotations=[
            dict(
                x=df['timestamp'].iloc[-1],
                y=df['close'].iloc[-1],
                xref="x", yref="y",
                text=f"Price: {df['close'].iloc[-1]:.2f}",
                showarrow=True,
                arrowhead=2,
                ax=0,
                ay=-40
            ),
            dict(
                x=df['timestamp'].iloc[-1],
                y=df['RSI'].iloc[-1],
                xref="x", yref="y2",
                text=f"RSI: {df['RSI'].iloc[-1]:.2f}",
                showarrow=True,
                arrowhead=2,
                ax=0,
                ay=40
            )
        ]
    )

    # Генеруємо HTML для графіка
    graph_html = pio.to_html(fig, full_html=False)

    # Повертаємо сторінку з графіком
    return render_template("chart.html", graph_html=graph_html, coin_name=coin_name)


if __name__ == "__main__":
    app.run(debug=True)
