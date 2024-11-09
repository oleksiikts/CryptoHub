# Crypto Trading Dashboard

A Flask-based web application for cryptocurrency analysis and user management. This app provides users with the ability to register, log in, view profile information, and check real-time and historical cryptocurrency data.

## Features

- **User Registration & Authentication**: _Users can register, log in, and view their profile information. User data is stored in a local SQLite database._
- **Cryptocurrency Data**: _Fetches real-time Bitcoin (BTC) data and historical prices from Binance using the ccxt library._
- **Technical Indicators**:
  - _Moving Average (14-day)_
  - _Relative Strength Index (RSI) (14-day)_
  - _Basic buy/sell/hold decision-making based on market data and calculated indicators._

## Setup

1. **Install Dependencies**:
   ```bash
   pip install flask flask-login ccxt numpy
   ```

## Database Initialization:

The app automatically creates an SQLite database (cryptobase.db) with a user table if it does not exist.

# Run the App:

```bash
python app.py
```

## Project Structure:

- **app.py:** Main Flask application with routes for authentication, data retrieval, and technical analysis.
- **Templates:** HTML templates for user interfaces, including sign-in, sign-up, profile, and data views.
- **Database:** Local SQLite database for storing user data.
