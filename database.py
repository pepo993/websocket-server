import sqlite3

DB_PATH = "data/bingoton.db"

def connect_db():
    """ Crea la connessione al database """
    conn = sqlite3.connect(DB_PATH)
    return conn

def setup_database():
    """ Crea le tabelle se non esistono """
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS game_state (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            game_active BOOLEAN DEFAULT 0,
            drawn_numbers TEXT DEFAULT '[]'
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS players (
            user_id INTEGER,
            game_id INTEGER,
            cartelle TEXT,
            PRIMARY KEY (user_id, game_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            user_id INTEGER PRIMARY KEY,
            deposits REAL DEFAULT 0,
            withdrawals REAL DEFAULT 0
        )
    """)

    conn.commit()
    conn.close()

setup_database()
