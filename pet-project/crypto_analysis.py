import ccxt
import pandas as pd
import numpy as np
import pandas_ta as ta
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from collections import defaultdict
from sklearn.preprocessing import StandardScaler  

exchange = ccxt.binance()


def get_historical_data(symbol='BTC/USDT', timeframe='1h', limit=1000):
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        return df
    except Exception as e:
        print(f"Error fetching historical data for {symbol}: {e}")
        return pd.DataFrame()


def calculate_indicators(df):
    df['SMA'] = ta.sma(df['close'], length=50)
    df['EMA'] = ta.ema(df['close'], length=50)
    df['RSI'] = ta.rsi(df['close'], length=14)

    macd = ta.macd(df['close'], fast=12, slow=26, signal=9)
    df['MACD'] = macd['MACD_12_26_9']
    df['MACD_signal'] = macd['MACDs_12_26_9']

    
    df['Stochastic'] = ta.stoch(df['high'], df['low'], df['close'], fastk_period=14, slowk_period=3, slowd_period=3)['STOCHk_14_3_3']
    
    
    bbands = ta.bbands(df['close'], length=20, std=2)
    df['BB_upper'] = bbands.iloc[:, 0]
    df['BB_middle'] = bbands.iloc[:, 1]
    df['BB_lower'] = bbands.iloc[:, 2]

    df['ATR'] = ta.atr(df['high'], df['low'], df['close'], length=14)

    df.dropna(inplace=True)  
    return df


def create_target_column(df):
    df['target'] = 0
    price_diff = df['close'].diff()

    df.loc[price_diff > 0, 'target'] = 1
    df.loc[price_diff < 0, 'target'] = -1

    return df


def prepare_data(df):
    X = df[['SMA', 'EMA', 'RSI', 'MACD', 'Stochastic', 'BB_upper', 'BB_lower', 'ATR']]
    y = df['target']
    return X, y


def scale_data(X):
    scaler = StandardScaler()
    return scaler.fit_transform(X)


def generate_explanation(decision, df):
    explanation = ""
    if decision == "Купити":
        if df['RSI'].iloc[-1] < 30:
            explanation += "RSI < 30 — перепроданість, сигнал до покупки. "
        if df['close'].iloc[-1] > df['SMA'].iloc[-1]:
            explanation += "Ціна вище 50-денної SMA — тренд на підвищення. "
        if df['MACD'].iloc[-1] > df['MACD_signal'].iloc[-1]:
            explanation += "MACD перетинає сигнальну лінію знизу вгору — бичачий сигнал. "
        if df['Stochastic'].iloc[-1] < 20:
            explanation += "Stochastic < 20 — перепроданість, сигнал до покупки. "
        if df['close'].iloc[-1] < df['BB_lower'].iloc[-1]:
            explanation += "Ціна нижче нижньої лінії Bollinger Bands — можливий сигнал до покупки. "
    
    elif decision == "Продати":
        if df['RSI'].iloc[-1] > 70:
            explanation += "RSI > 70 — перекупленість, сигнал до продажу. "
        if df['close'].iloc[-1] < df['EMA'].iloc[-1]:
            explanation += "Ціна нижче 50-денної EMA — тренд на пониження. "
        if df['MACD'].iloc[-1] < df['MACD_signal'].iloc[-1]:
            explanation += "MACD перетинає сигнальну лінію згори вниз — ведмежий сигнал. "
        if df['Stochastic'].iloc[-1] > 80:
            explanation += "Stochastic > 80 — перекупленість, сигнал до продажу. "
        if df['close'].iloc[-1] > df['BB_upper'].iloc[-1]:
            explanation += "Ціна вище верхньої лінії Bollinger Bands — можливий сигнал до продажу. "
    
    elif decision == "Чекати":
        explanation += "Індикатори дають суперечливі сигнали або тренд не виражений. "

    return explanation


def train_and_predict(symbol='BTC/USDT'):
    timeframes = ['1h', '1d', '1w']
    decision_results = defaultdict(dict)

    for timeframe in timeframes:
        df = get_historical_data(symbol=symbol, timeframe=timeframe, limit=1000)
        if df.empty:
            decision_results[timeframe]['decision'] = "Не вдалося отримати дані"
            decision_results[timeframe]['model_report'] = "Немає даних"
            decision_results[timeframe]['explanation'] = ""
            continue

        df = calculate_indicators(df)
        df = create_target_column(df)

        if df.empty or df.shape[0] < 10:
            decision_results[timeframe]['decision'] = "Недостатньо даних"
            decision_results[timeframe]['model_report'] = "Мало рядків для навчання"
            decision_results[timeframe]['explanation'] = ""
            continue

        X, y = prepare_data(df)
        X = scale_data(X)  

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(X_train, y_train)

        y_pred = model.predict(X_test)
        model_report = classification_report(y_test, y_pred, zero_division=0)

        latest_data = X[-1:].reshape(1, -1)
        prediction = model.predict(latest_data)[0]

        if prediction == 1:
            decision = "Купити"
        elif prediction == -1:
            decision = "Продати"
        else:
            decision = "Чекати"

        explanation = generate_explanation(decision, df)

        decision_results[timeframe]['decision'] = decision
        decision_results[timeframe]['model_report'] = model_report
        decision_results[timeframe]['explanation'] = explanation

    return decision_results

if __name__ == '__main__':
    decision_results = train_and_predict('BTC/USDT')
    for tf, result in decision_results.items():
        print(f"\n📊 Таймфрейм: {tf}")
        print(f"🔍 Рішення: {result['decision']}")
        print(f"📄 Звіт моделі:\n{result['model_report']}")
        print(f"💬 Пояснення: {result['explanation']}")
