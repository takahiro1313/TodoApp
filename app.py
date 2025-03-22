import streamlit as st
import datetime
from database import DatabaseManager
from models import Todo

# ページ設定
st.set_page_config(
    page_title="業務効率化TODOアプリ",
    page_icon="✅",
    layout="wide"
)

# CSSでUIを調整
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stButton button {
        width: 100%;
    }
    .status-high {
        color: red;
        font-weight: bold;
    }
    .status-medium {
        color: orange;
        font-weight: bold;
    }
    .status-low {
        color: green;
        font-weight: bold;
    }
    .completed {
        text-decoration: line-through;
        color: gray;
    }
    </style>
""", unsafe_allow_html=True)

# データベースマネージャーの初期化
db = DatabaseManager("todo.db")

# サイドバー - タスク追加フォーム
st.sidebar.header("新しいタスクを追加")

task_name = st.sidebar.text_input("タスク名")
task_description = st.sidebar.text_area("詳細説明")
priority = st.sidebar.selectbox("優先度", ["高", "中", "低"])
due_date = st.sidebar.date_input(
    "期限", datetime.datetime.now() + datetime.timedelta(days=1))
category = st.sidebar.selectbox("カテゴリ", ["仕事", "個人", "会議", "その他"])

if st.sidebar.button("タスクを追加"):
    if task_name:
        todo = Todo(
            name=task_name,
            description=task_description,
            priority=priority,
            due_date=due_date.strftime("%Y-%m-%d"),
            category=category,
            completed=False,
            created_at=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        db.add_todo(todo)
        st.sidebar.success("タスクが追加されました！")
    else:
        st.sidebar.error("タスク名は必須です")

# メインコンテンツ
st.title("業務効率化TODOアプリ")

# タブで表示を切り替え
tab1, tab2, tab3 = st.tabs(["すべてのタスク", "完了済み", "統計"])

with tab1:
    # フィルタリングオプション
    col1, col2, col3 = st.columns(3)

    with col1:
        filter_priority = st.multiselect(
            "優先度でフィルタ",
            ["高", "中", "低"],
            default=["高", "中", "低"]
        )

    with col2:
        filter_category = st.multiselect(
            "カテゴリでフィルタ",
            ["仕事", "個人", "会議", "その他"],
            default=["仕事", "個人", "会議", "その他"]
        )

    with col3:
        filter_completed = st.checkbox("完了済みを表示", value=False)
        sort_by = st.selectbox("並び替え", ["期限", "優先度", "作成日"])

    # タスクの取得とフィルタリング
    todos = db.get_todos(
        priorities=filter_priority,
        categories=filter_category,
        show_completed=filter_completed,
        sort_by=sort_by
    )

    # タスクの表示
    if todos:
        for todo in todos:
            col1, col2, col3 = st.columns([6, 2, 2])

            # タスク名と説明
            with col1:
                if todo.completed:
                    st.markdown(
                        f"<h3 class='completed'>{todo.name}</h3>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<h3>{todo.name}</h3>",
                                unsafe_allow_html=True)

                st.write(todo.description)
                st.caption(f"作成: {todo.created_at}")

            # タスク情報
            with col2:
                priority_class = {
                    "高": "status-high",
                    "中": "status-medium",
                    "低": "status-low"
                }.get(todo.priority, "")

                st.markdown(
                    f"<p>優先度: <span class='{priority_class}'>{todo.priority}</span></p>", unsafe_allow_html=True)
                st.write(f"期限: {todo.due_date}")
                st.write(f"カテゴリ: {todo.category}")

            # アクションボタン
            with col3:
                if not todo.completed:
                    if st.button("完了にする", key=f"complete_{todo.id}"):
                        db.update_todo_status(todo.id, True)
                        st.experimental_rerun()
                else:
                    if st.button("未完了に戻す", key=f"uncomplete_{todo.id}"):
                        db.update_todo_status(todo.id, False)
                        st.experimental_rerun()

                if st.button("削除", key=f"delete_{todo.id}"):
                    db.delete_todo(todo.id)
                    st.experimental_rerun()

            st.divider()
    else:
        st.info("タスクがありません。サイドバーから新しいタスクを追加してください。")

with tab2:
    # 完了済みタスクの表示
    completed_todos = db.get_todos(show_completed=True, completed_only=True)

    if completed_todos:
        for todo in completed_todos:
            col1, col2 = st.columns([8, 2])

            with col1:
                st.markdown(
                    f"<h3 class='completed'>{todo.name}</h3>", unsafe_allow_html=True)
                st.write(todo.description)
                st.caption(f"完了日: {todo.updated_at}")

            with col2:
                if st.button("削除", key=f"delete_completed_{todo.id}"):
                    db.delete_todo(todo.id)
                    st.experimental_rerun()

            st.divider()
    else:
        st.info("完了済みのタスクはありません。")

with tab3:
    # タスク統計の表示
    stats = db.get_statistics()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("タスク概要")
        st.metric("全タスク数", stats["total_tasks"])
        st.metric("完了済み", stats["completed_tasks"])
        st.metric("未完了", stats["pending_tasks"])

        # 期限切れタスクの表示
        st.subheader("期限切れタスク")
        overdue_tasks = db.get_overdue_tasks()

        if overdue_tasks:
            for task in overdue_tasks:
                st.markdown(
                    f"<p class='status-high'>{task.name} - 期限: {task.due_date}</p>", unsafe_allow_html=True)
        else:
            st.success("期限切れのタスクはありません！")

    with col2:
        st.subheader("カテゴリ別タスク数")
        category_stats = db.get_category_statistics()

        # シンプルなグラフ表示
        st.bar_chart(category_stats)

        st.subheader("優先度別タスク数")
        priority_stats = db.get_priority_statistics()

        # シンプルなグラフ表示
        st.bar_chart(priority_stats)

# フッター
st.markdown("---")
st.caption("© 2025 業務効率化TODOアプリ")
