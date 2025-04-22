
import sqlite3

def init_db():
    db = sqlite3.connect('cryptobase.db')
    c = db.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS users (
                  UserId INTEGER PRIMARY KEY AUTOINCREMENT,
                  Email TEXT NOT NULL UNIQUE,
                  Login TEXT NOT NULL,
                  Password TEXT NOT NULL,
                  Phone TEXT
              )""")

    c.execute("""CREATE TABLE IF NOT EXISTS favorites (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  coin TEXT,
                  active INTEGER DEFAULT 0,
                  FOREIGN KEY (user_id) REFERENCES users(UserId)
              )""")

    db.commit()
    db.close()

def add_favorite(user_id, coin):
    with sqlite3.connect('cryptobase.db') as db:
        c = db.cursor()
        # Перевіряємо, чи вже є монета у списку обраного
        c.execute("SELECT id FROM favorites WHERE user_id = ? AND coin = ?", (user_id, coin))
        result = c.fetchone()

        if result:
            # Якщо є — оновлюємо активність
            c.execute("UPDATE favorites SET active = 1 WHERE user_id = ? AND coin = ?", (user_id, coin))
        else:
            # Якщо немає — додаємо
            c.execute("INSERT INTO favorites (user_id, coin, active) VALUES (?, ?, 1)", (user_id, coin))

        db.commit()


def remove_favorite(user_id, coin):
    with sqlite3.connect('cryptobase.db') as db:
        c = db.cursor()
        c.execute("DELETE FROM favorites WHERE user_id = ? AND coin = ?", (user_id, coin))
        db.commit()

def get_favorites(user_id):
    with sqlite3.connect('cryptobase.db') as db:
        c = db.cursor()
        c.execute("SELECT coin, active FROM favorites WHERE user_id = ?", (user_id,))
        return [(row[0], row[1]) for row in c.fetchall()]

def register_user(email, login, password, phone):
    with sqlite3.connect('cryptobase.db') as db:
        c = db.cursor()
        c.execute("INSERT INTO users (Email, Login, Password, Phone) VALUES (?, ?, ?, ?)", 
                  (email, login, password, phone))
        db.commit()

def get_user_by_email(email):
    with sqlite3.connect('cryptobase.db') as db:
        c = db.cursor()
        c.execute("SELECT UserId, Email, Login, Password, Phone FROM users WHERE Email = ?", (email,))
        return c.fetchone()

def get_user_by_id(user_id):
    with sqlite3.connect('cryptobase.db') as db:
        c = db.cursor()
        c.execute("SELECT UserId, Email, Login, Password, Phone FROM users WHERE UserId = ?", (user_id,))
        return c.fetchone()

def get_active_favorites(user_id):
    with sqlite3.connect('cryptobase.db') as db:
        c = db.cursor()
        c.execute("SELECT coin FROM favorites WHERE user_id = ? AND active = 1", (user_id,))
        return [row[0] for row in c.fetchall()]

def deactivate_favorite_coin(user_id, coin):
    with sqlite3.connect('cryptobase.db') as db:
        c = db.cursor()
        c.execute("UPDATE favorites SET active = 0 WHERE user_id = ? AND coin = ?", (user_id, coin))
        db.commit()

def delete_favorite_coin(user_id, coin):
    with sqlite3.connect('cryptobase.db') as db:
        c = db.cursor()
        c.execute("DELETE FROM favorites WHERE user_id = ? AND coin = ?", (user_id, coin))
        db.commit()
