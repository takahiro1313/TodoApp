class Todo:
    def __init__(self, name, description="", priority="中", due_date=None,
                 category="仕事", completed=False, created_at=None, updated_at=None, id=None):
        """
        Todoモデルクラス

        引数:
            name (str): タスク名
            description (str): タスクの詳細説明
            priority (str): 優先度（高/中/低）
            due_date (str): 期限日（YYYY-MM-DD形式）
            category (str): カテゴリ
            completed (bool): 完了状態
            created_at (str): 作成日時
            updated_at (str): 更新日時
            id (int): タスクID（データベースから取得時に使用）
        """
        self.id = id
        self.name = name
        self.description = description
        self.priority = priority
        self.due_date = due_date
        self.category = category
        self.completed = completed
        self.created_at = created_at
        self.updated_at = updated_at

    def __str__(self):
        """
        文字列表現を返す
        """
        status = "完了" if self.completed else "未完了"
        return f"{self.name} [{self.priority}] ({status}) - 期限: {self.due_date}"
