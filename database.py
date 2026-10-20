import sqlite3
from contextlib import contextmanager
from typing import Optional, List

from .models import Transaction, Budget


class DatabaseManager:
    def __init__(self, db_path: str = "expense_mate.db"):
        self.db_path = db_path
        self._init_schema()

    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row

        try:
            yield conn
        finally:
            conn.close()

    def _init_schema(self) -> None:
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS transactions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        amount REAL NOT NULL,
                        category TEXT NOT NULL,
                        trans_type TEXT NOT NULL,
                        date TEXT NOT NULL,
                        description TEXT DEFAULT ''
                    );
                """)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS budgets (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        category TEXT NOT NULL,
                        monthly_limit REAL NOT NULL,
                        month_year TEXT NOT NULL,
                        UNIQUE(category, month_year)
                    );
                """)
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_trans_date ON transactions(date);")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_trans_cat ON transactions(category);")
                conn.commit()
        except sqlite3.Error as exc:
            raise RuntimeError(f"Unable to initialize database schema: {exc}") from exc

    def insert_transaction(self, t: Transaction) -> int:
        try:
            t.validate()
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO transactions (amount, category, trans_type, date, description)
                    VALUES (?, ?, ?, ?, ?)
                """, (t.amount, t.category.strip(), t.trans_type, t.date, t.description.strip()))
                conn.commit()
                return cursor.lastrowid
        except (sqlite3.Error, ValueError) as exc:
            raise ValueError(f"Failed to save transaction: {exc}") from exc

    def get_all_transactions(self) -> List[Transaction]:
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM transactions ORDER BY date DESC, id DESC")
                return [
                    Transaction(
                        id=row["id"],
                        amount=row["amount"],
                        category=row["category"],
                        trans_type=row["trans_type"],
                        date=row["date"],
                        description=row["description"]
                    )
                    for row in cursor.fetchall()
                ]
        except sqlite3.Error as exc:
            raise RuntimeError(f"Unable to read transactions: {exc}") from exc

    def upsert_budget(self, b: Budget) -> int:
        try:
            b.validate()
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO budgets (category, monthly_limit, month_year)
                    VALUES (?, ?, ?)
                    ON CONFLICT(category, month_year) DO UPDATE SET
                        monthly_limit = excluded.monthly_limit
                """, (b.category.strip(), b.monthly_limit, b.month_year))
                conn.commit()
                return cursor.lastrowid
        except (sqlite3.Error, ValueError) as exc:
            raise ValueError(f"Failed to save budget: {exc}") from exc

    def get_budget(self, category: str, month_year: str) -> Optional[Budget]:
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM budgets WHERE category = ? AND month_year = ?",
                    (category.strip(), month_year)
                )
                row = cursor.fetchone()

                if row:
                    return Budget(
                        id=row["id"],
                        category=row["category"],
                        monthly_limit=row["monthly_limit"],
                        month_year=row["month_year"]
                    )

                return None
        except sqlite3.Error as exc:
            raise RuntimeError(f"Unable to fetch budget: {exc}") from exc

    def get_budgets_for_month(self, month_year: str) -> List[Budget]:
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM budgets WHERE month_year = ?",
                    (month_year,)
                )

                return [
                    Budget(
                        id=row["id"],
                        category=row["category"],
                        monthly_limit=row["monthly_limit"],
                        month_year=row["month_year"]
                    )
                    for row in cursor.fetchall()
                ]
        except sqlite3.Error as exc:
            raise RuntimeError(f"Unable to fetch budgets: {exc}") from exc