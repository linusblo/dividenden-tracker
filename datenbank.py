"""
Datenbank-Zugriff (SQLite).
"""
import sqlite3
import pandas as pd
from config import DB_PFAD


def init_db():
    """Erstellt die Datenbank und migriert bei Bedarf."""
    conn = sqlite3.connect(DB_PFAD)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS positionen (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL UNIQUE,
            stueckzahl REAL NOT NULL
        )
    """)
    vorhandene_spalten = [row[1] for row in conn.execute("PRAGMA table_info(positionen)").fetchall()]
    if "sparrate_betrag" not in vorhandene_spalten:
        conn.execute("ALTER TABLE positionen ADD COLUMN sparrate_betrag REAL DEFAULT 0")
    if "sparrate_intervall" not in vorhandene_spalten:
        conn.execute("ALTER TABLE positionen ADD COLUMN sparrate_intervall INTEGER DEFAULT 4")
    if "reinvest_dividende" not in vorhandene_spalten:
        conn.execute("ALTER TABLE positionen ADD COLUMN reinvest_dividende INTEGER DEFAULT 1")
    conn.commit()
    conn.close()


def lade_positionen():
    """Lädt alle Positionen aus der Datenbank."""
    conn = sqlite3.connect(DB_PFAD)
    df = pd.read_sql_query("SELECT * FROM positionen", conn)
    conn.close()
    return df


def speichere_position(ticker, stueckzahl):
    """Speichert eine neue Position oder aktualisiert eine vorhandene."""
    conn = sqlite3.connect(DB_PFAD)
    conn.execute("""
        INSERT INTO positionen (ticker, stueckzahl) 
        VALUES (?, ?)
        ON CONFLICT(ticker) DO UPDATE SET stueckzahl = excluded.stueckzahl
    """, (ticker.upper(), stueckzahl))
    conn.commit()
    conn.close()


def aktualisiere_sparrate(position_id, betrag, intervall):
    """Aktualisiert die Sparrate einer Position."""
    conn = sqlite3.connect(DB_PFAD)
    conn.execute("""
        UPDATE positionen 
        SET sparrate_betrag = ?, sparrate_intervall = ?
        WHERE id = ?
    """, (betrag, intervall, position_id))
    conn.commit()
    conn.close()


def aktualisiere_reinvest(position_id, reinvest):
    """Aktualisiert den Reinvest-Modus einer Position."""
    conn = sqlite3.connect(DB_PFAD)
    conn.execute("UPDATE positionen SET reinvest_dividende = ? WHERE id = ?",
                 (1 if reinvest else 0, position_id))
    conn.commit()
    conn.close()


def loesche_position(position_id):
    """Löscht eine Position anhand ihrer ID."""
    conn = sqlite3.connect(DB_PFAD)
    conn.execute("DELETE FROM positionen WHERE id = ?", (position_id,))
    conn.commit()
    conn.close()