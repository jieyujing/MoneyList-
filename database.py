import sqlite3
from datetime import datetime, date

class Database:
    def __init__(self):
        self.conn = sqlite3.connect("expenses.db")
        self.cursor = self.conn.cursor()
        self.create_table()
        
    def create_table(self):
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY,
            date TEXT,
            type TEXT,
            amount REAL,
            description TEXT
        )
        """)
        self.conn.commit()
        
    def add_transaction(self, date, type, amount, description):
        self.cursor.execute("""
        INSERT INTO transactions (date, type, amount, description)
        VALUES (?, ?, ?, ?)
        """, (date, type, amount, description))
        self.conn.commit()

    def update_transaction(self, id, date, type, amount, description):
        self.cursor.execute("""
        UPDATE transactions
        SET date = ?, type = ?, amount = ?, description = ?
        WHERE id = ?
        """, (date, type, amount, description, id))
        self.conn.commit()

    def delete_transaction(self, id):
        self.cursor.execute("DELETE FROM transactions WHERE id = ?", (id,))
        self.conn.commit()
        
    def get_transactions(self, start_date=None, end_date=None, transaction_type=None):
        query = "SELECT id, date, type, amount, description FROM transactions"
        params = []
        conditions = []

        # 添加默认的日期范围限制
        if not start_date:
            start_date = "1970-01-01"
        if not end_date:
            end_date = date.today().strftime("%Y-%m-%d")

        conditions.append("date >= ?")
        params.append(start_date)
        conditions.append("date <= ?")
        params.append(end_date)

        if transaction_type:
            conditions.append("type = ?")
            params.append(transaction_type)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY date DESC"
        self.cursor.execute(query, params)
        return self.cursor.fetchall()

    def get_transaction(self, id):
        self.cursor.execute("SELECT id, date, type, amount, description FROM transactions WHERE id = ?", (id,))
        return self.cursor.fetchone()

    def get_balance(self):
        self.cursor.execute("""
        SELECT SUM(CASE WHEN type = '收入' THEN amount ELSE -amount END)
        FROM transactions
        """)
        return self.cursor.fetchone()[0] or 0

    def get_total_income(self):
        self.cursor.execute("SELECT SUM(amount) FROM transactions WHERE type = '收入'")
        return self.cursor.fetchone()[0] or 0

    def get_total_expense(self):
        self.cursor.execute("SELECT SUM(amount) FROM transactions WHERE type = '支出'")
        return self.cursor.fetchone()[0] or 0

    def __del__(self):
        self.conn.close()