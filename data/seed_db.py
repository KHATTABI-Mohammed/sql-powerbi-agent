"""Crée et peuple `data/powerbi_sample.db` (SQLite) avec un petit jeu de données
de vente, utilisé comme base cible pour les requêtes générées par l'agent.

Usage: python data/seed_db.py
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "powerbi_sample.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS customers (
    customer_id INTEGER PRIMARY KEY,
    name        TEXT NOT NULL,
    country     TEXT NOT NULL,
    segment     TEXT NOT NULL,
    signup_date TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS products (
    product_id  INTEGER PRIMARY KEY,
    name        TEXT NOT NULL,
    category    TEXT NOT NULL,
    unit_price  REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS orders (
    order_id    INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
    order_date  TEXT NOT NULL,
    status      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS order_items (
    order_item_id INTEGER PRIMARY KEY,
    order_id      INTEGER NOT NULL REFERENCES orders(order_id),
    product_id    INTEGER NOT NULL REFERENCES products(product_id),
    quantity      INTEGER NOT NULL,
    unit_price    REAL NOT NULL
);
"""

CUSTOMERS = [
    (1, "Amine Khattabi", "Maroc", "PME", "2023-01-15"),
    (2, "Sophie Martin", "France", "Particulier", "2023-03-02"),
    (3, "TechCorp SA", "France", "Grand Compte", "2022-11-20"),
    (4, "Youssef Idrissi", "Maroc", "Particulier", "2024-02-10"),
    (5, "DataWave Inc.", "Belgique", "Grand Compte", "2023-07-08"),
]

PRODUCTS = [
    (1, "Licence Analytics Pro", "Logiciel", 199.0),
    (2, "Licence Analytics Basic", "Logiciel", 49.0),
    (3, "Serveur Edge X1", "Matériel", 899.0),
    (4, "Support Premium (an)", "Service", 350.0),
    (5, "Capteur IoT", "Matériel", 25.0),
]

ORDERS = [
    (1, 1, "2024-01-10", "Livrée"),
    (2, 2, "2024-02-14", "Livrée"),
    (3, 3, "2024-03-01", "En cours"),
    (4, 1, "2024-03-20", "Livrée"),
    (5, 5, "2024-04-05", "Annulée"),
    (6, 4, "2024-05-11", "Livrée"),
]

ORDER_ITEMS = [
    (1, 1, 1, 2, 199.0),
    (2, 1, 4, 1, 350.0),
    (3, 2, 2, 1, 49.0),
    (4, 3, 3, 5, 899.0),
    (5, 4, 5, 20, 25.0),
    (6, 5, 1, 1, 199.0),
    (7, 6, 2, 3, 49.0),
    (8, 6, 5, 10, 25.0),
]


def seed() -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.executescript(SCHEMA)
        conn.executemany("INSERT OR REPLACE INTO customers VALUES (?,?,?,?,?)", CUSTOMERS)
        conn.executemany("INSERT OR REPLACE INTO products VALUES (?,?,?,?)", PRODUCTS)
        conn.executemany("INSERT OR REPLACE INTO orders VALUES (?,?,?,?)", ORDERS)
        conn.executemany("INSERT OR REPLACE INTO order_items VALUES (?,?,?,?,?)", ORDER_ITEMS)
        conn.commit()
    print(f"Base de données créée: {DB_PATH}")


if __name__ == "__main__":
    seed()
