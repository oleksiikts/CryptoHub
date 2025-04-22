from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_login import LoginManager, login_required, current_user, UserMixin, login_user, logout_user
import sqlite3
import re
import ccxt
import pandas as pd
import numpy as np
import feedparser  
import pytz
from datetime import datetime
from crypto_analysis import train_and_predict
import plotly.graph_objects as go
import plotly.io as pio
from datetime import datetime
import requests
import yfinance as yf
from concurrent.futures import ThreadPoolExecutor
from db import (
    register_user, add_favorite, remove_favorite,
    get_favorites, get_user_by_email, get_user_by_id,
    get_active_favorites, deactivate_favorite_coin,
    delete_favorite_coin
)

app = Flask(__name__)
app.secret_key = 'hello'

@app.route('/etf')
def etf_table():
    tickers = [
        
        'SPY', 'QQQ', 'VOO', 'ARKK', 'DIA', 'VTI', 'IWM', 'XLK', 'XLF', 'XLV',
        
        'TSLA', 'AMZN', 'NVDA'
    ]

    etf_data = []

    for symbol in tickers:
        try:
            etf = yf.Ticker(symbol)
            info = etf.info

            etf_data.append({
                'symbol': symbol,
                'name': info.get('shortName', 'N/A'),
                'price': info.get('regularMarketPrice', 'N/A'),
                'change': info.get('regularMarketChangePercent', 0),
                'volume': info.get('volume', 'N/A'),
                'market_cap': info.get('marketCap', 'N/A'),
                'type': 'Stock' if symbol in ['TSLA', 'AMZN', 'NVDA'] else 'ETF'
            })
        except Exception as e:
            print(f"Error fetching data for {symbol}: {e}")

    return render_template('etf.html', etfs=etf_data)



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



def validate_phone(phone):
    pattern = r'^\+380\d{9}$'
    return re.match(pattern, phone) is not None



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
    try:
        ticker = exchange.fetch_ticker(symbol + '/USDT')
        return ticker['last']
    except:
        return None











def calculate_rsi(data, window=14):
    delta = data['close'].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(span=window, adjust=False).mean()
    avg_loss = loss.ewm(span=window, adjust=False).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    return rsi.fillna(0)  

@app.route('/home')
def home():
    cointelegraph_news = get_cointelegraph_news()
    return render_template('index.html', cointelegraph_news=cointelegraph_news)



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
        num = float(value)
        if num >= 1:
            return f"${num:,.2f}"  
        elif num >= 0.01:
            return f"${num:.4f}"   
        elif num >= 0.0001:
            return f"${num:.6f}"   
        elif num >= 0.000001:
            return f"${num:.8f}"   
        else:
            return f"${num:.10f}"  
    except:
        return "N/A"

app.jinja_env.filters['format_price'] = format_price







exchange = ccxt.binance()


coins = ['BTC', 'ETH', 'XRP', 'LTC', 'BNB', 'SOL', 'ADA', 'DOGE', 'DOT', 'PEPE', 'NEAR', 'KAS', 'ARB', 'ATOM', 'SHIB', 'XLM']


def get_market_data_binance(symbol):
    try:
        ticker = exchange.fetch_ticker(symbol + '/USDT')
        volume_24h = ticker['quoteVolume']
        price = ticker['last']
        open_price = ticker['open']
        market_cap = price * volume_24h

        
        change_percent = ((price - open_price) / open_price) * 100 if open_price else None

        return symbol, {
            'last_price': price,
            'market_cap': market_cap,
            'volume_24h': volume_24h,
            'change_percent': change_percent
        }
    except Exception as e:
        print(f"Error fetching market data for {symbol}: {e}")
        return symbol, {
            'last_price': None,
            'market_cap': None,
            'volume_24h': None,
            'change_percent': None
        }


def get_last_price(symbol):
    try:
        ticker = exchange.fetch_ticker(symbol + '/USDT')
        return ticker['last']
    except:
        return None


@app.route('/data', methods=['GET'])
def data_page():
    data = {}

    with ThreadPoolExecutor(max_workers=10) as executor:
        market_results = list(executor.map(get_market_data_binance, coins))

    for symbol, market_info in market_results:
        data[symbol] = market_info

    return render_template('data.html', coins_data=data)
@app.route('/chart/<coin_name>')
def chart(coin_name):
    
    exchange = ccxt.binance()
    symbol = f'{coin_name}/USDT'  
    ohlcv = exchange.fetch_ohlcv(symbol, '1h')  

    
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

    
    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=df['timestamp'],
        open=df['open'],
        high=df['high'],
        low=df['low'],
        close=df['close'],
        name=coin_name
    ))

    
    df['RSI'] = calculate_rsi(df)

    
    fig.add_trace(go.Scatter(
        x=df['timestamp'],
        y=df['RSI'],
        mode='lines',
        name="RSI",
        line=dict(color='orange'),
        yaxis="y2"
    ))

    
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

    
    graph_html = pio.to_html(fig, full_html=False)

    
    return render_template("chart.html", graph_html=graph_html, coin_name=coin_name)




@app.route('/etf_chart/<symbol>')
def etf_chart(symbol):
    try:
        
        df = yf.download(symbol, period="1mo", interval="1h", auto_adjust=False)

        if df.empty:
            return f"Дані для {symbol} не знайдено або помилка завантаження."

        
        df.reset_index(inplace=True)
        print("Колонки:", df.columns)

        
        if isinstance(df.columns, pd.MultiIndex):
            symbol_upper = symbol.upper()
            df = df[[('Datetime', ''), ('Open', symbol_upper), ('High', symbol_upper),
                     ('Low', symbol_upper), ('Close', symbol_upper),
                     ('Adj Close', symbol_upper), ('Volume', symbol_upper)]]
            df.columns = ['datetime', 'open', 'high', 'low', 'close', 'adj_close', 'volume']
        else:
            df.columns = [col.lower() for col in df.columns]

        
        df['rsi'] = calculate_rsi(df)

        
        df_rsi = df[['datetime', 'rsi']].dropna()

        
        fig = go.Figure()

        
        fig.add_trace(go.Scatter(
            x=df['datetime'],
            y=df['close'],
            mode='lines',
            name='Ціна',
            line=dict(color='blue'),
            yaxis='y1'
        ))

        
        fig.add_trace(go.Scatter(
            x=df_rsi['datetime'],
            y=df_rsi['rsi'],
            mode='lines',
            name='RSI',
            line=dict(color='orange'),
            yaxis='y2'
        ))

        
        fig.update_layout(
            title=f"{symbol} ETF Chart (Лінійна ціна + RSI)",
            xaxis_title="Час",
            yaxis=dict(
                title="Ціна",
                side="left"
            ),
            yaxis2=dict(
                title="RSI",
                overlaying="y",
                side="right"
            ),
            hovermode="x unified",
            annotations=[
                dict(
                    x=df['datetime'].iloc[-1],
                    y=df['close'].iloc[-1],
                    xref="x", yref="y",
                    text=f"Ціна: {df['close'].iloc[-1]:.2f}",
                    showarrow=True,
                    arrowhead=2,
                    ax=0,
                    ay=-40
                ),
                dict(
                    x=df_rsi['datetime'].iloc[-1],
                    y=df_rsi['rsi'].iloc[-1],
                    xref="x", yref="y2",
                    text=f"RSI: {df_rsi['rsi'].iloc[-1]:.2f}",
                    showarrow=True,
                    arrowhead=2,
                    ax=0,
                    ay=40
                )
            ]
        )

        graph_html = pio.to_html(fig, full_html=False)
        return render_template("chart_etf.html", graph_html=graph_html, symbol=symbol)

    except Exception as e:
        return f"Помилка при побудові графіка: {str(e)}"



if __name__ == "__main__":
    app.run(debug=True)
