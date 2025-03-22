import sqlite3
import datetime
import pandas as pd
from models import Todo


class DatabaseManager:
    def __init__(self, db_file):
        """データベース接続を初期化し、必要なテーブルを作成する"""
        self.db_file = db_file
        self._create_tables()

    def _get_connection(self):
        """データベース接続を返す"""
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row
        return conn

    def _create_tables(self):
        """必要なテーブルを作成する"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # TODOテーブルの作成
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS todos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            priority TEXT,
            due_date TEXT,
            category TEXT,
            completed BOOLEAN DEFAULT 0,
            created_at TEXT,
            updated_at TEXT
        )
        ''')

        conn.commit()
        conn.close()

    def add_todo(self, todo):
        """新しいTODOをデータベースに追加する"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute('''
        INSERT INTO todos (name, description, priority, due_date, category, completed, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            todo.name,
            todo.description,
            todo.priority,
            todo.due_date,
            todo.category,
            todo.completed,
            todo.created_at,
            todo.created_at  # 作成時は更新日時も同じ
        ))

        conn.commit()
        conn.close()

    def get_todos(self, priorities=None, categories=None, show_completed=False, completed_only=False, sort_by="due_date"):
        """条件に合うTODOを取得する"""
        conn = self._get_connection()
        cursor = conn.cursor()

        query = "SELECT * FROM todos WHERE 1=1"
        params = []

        # フィルタ条件の追加
        if priorities:
            placeholders = ", ".join(["?" for _ in priorities])
            query += f" AND priority IN ({placeholders})"
            params.extend(priorities)

        if categories:
            placeholders = ", ".join(["?" for _ in categories])
            query += f" AND category IN ({placeholders})"
            params.extend(categories)

        if not show_completed and not completed_only:
            query += " AND completed = 0"
        elif completed_only:
            query += " AND completed = 1"

        # 並び替え条件
        if sort_by == "期限":
            query += " ORDER BY due_date ASC"
        elif sort_by == "優先度":
            query += " ORDER BY CASE priority WHEN '高' THEN 1 WHEN '中' THEN 2 WHEN '低' THEN 3 END"
        elif sort_by == "作成日":
            query += " ORDER BY created_at DESC"

        cursor.execute(query, params)
        rows = cursor.fetchall()

        todos = []
        for row in rows:
            todo = Todo(
                id=row["id"],
                name=row["name"],
                description=row["description"],
                priority=row["priority"],
                due_date=row["due_date"],
                category=row["category"],
                completed=bool(row["completed"]),
                created_at=row["created_at"],
                updated_at=row["updated_at"]
            )
            todos.append(todo)

        conn.close()
        return todos

    def update_todo_status(self, todo_id, completed):
        """TODOの完了状態を更新する"""
        conn = self._get_connection()
        cursor = conn.cursor()

        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute(
            "UPDATE todos SET completed = ?, updated_at = ? WHERE id = ?",
            (completed, current_time, todo_id)
        )

        conn.commit()
        conn.close()

    def delete_todo(self, todo_id):
        """TODOを削除する"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM todos WHERE id = ?", (todo_id,))

        conn.commit()
        conn.close()

    def get_statistics(self):
        """タスクの統計情報を取得する"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # 全タスク数
        cursor.execute("SELECT COUNT(*) FROM todos")
        total_tasks = cursor.fetchone()[0]

        # 完了済みタスク数
        cursor.execute("SELECT COUNT(*) FROM todos WHERE completed = 1")
        completed_tasks = cursor.fetchone()[0]

        # 未完了タスク数
        cursor.execute("SELECT COUNT(*) FROM todos WHERE completed = 0")
        pending_tasks = cursor.fetchone()[0]

        conn.close()

        return {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "pending_tasks": pending_tasks
        }

    def get_overdue_tasks(self):
        """期限切れのタスクを取得する"""
        conn = self._get_connection()
        cursor = conn.cursor()

        today = datetime.datetime.now().strftime("%Y-%m-%d")

        cursor.execute(
            "SELECT * FROM todos WHERE completed = 0 AND due_date < ? ORDER BY due_date",
            (today,)
        )

        rows = cursor.fetchall()

        overdue_tasks = []
        for row in rows:
            todo = Todo(
                id=row["id"],
                name=row["name"],
                description=row["description"],
                priority=row["priority"],
                due_date=row["due_date"],
                category=row["category"],
                completed=bool(row["completed"]),
                created_at=row["created_at"],
                updated_at=row["updated_at"]
            )
            overdue_tasks.append(todo)

        conn.close()
        return overdue_tasks

    def get_category_statistics(self):
        """カテゴリ別のタスク数を取得する"""
        conn = self._get_connection()

        # pandasを使用してSQLクエリ結果を直接DataFrameとして取得
        query = "SELECT category, COUNT(*) as count FROM todos GROUP BY category"
        df = pd.read_sql_query(query, conn)

        conn.close()

        # インデックスをカテゴリに設定
        if not df.empty:
            df = df.set_index('category')

        return df

    def get_priority_statistics(self):
        """優先度別のタスク数を取得する"""
        conn = self._get_connection()

        # pandasを使用してSQLクエリ結果を直接DataFrameとして取得
        query = "SELECT priority, COUNT(*) as count FROM todos GROUP BY priority"
        df = pd.read_sql_query(query, conn)

        conn.close()

        # インデックスを優先度に設定
        if not df.empty:
            df = df.set_index('priority')

        return df
