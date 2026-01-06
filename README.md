# 📚 Midad Books | كتب مداد

Simple inventory & sales management for Arabic bookshops.  
Built with **Streamlit + SQLModel + SQLite**.

## ✨ Features

- **📚 Inventory** - Add/edit books, track stock & prices
- **💰 Sales** - Record sales → stock auto-decreases (transactional)
- **📊 Analytics** - Revenue, profit, stock value

## 🚀 Quick Start

```bash
uv run streamlit run app.py
```

Open `http://localhost:8501`

## 📁 Structure

```
├── app.py              # Streamlit UI
├── src/
│   └── database.py     # SQLModel models + operations
├── data/
│   └── midad.db        # SQLite database (auto-created)
├── pyproject.toml      # UV dependencies
└── uv.lock
```

## 🛠️ Tech Stack

- **UV** - Fast Python package manager
- **Streamlit** - Web UI
- **SQLModel** - Type-safe ORM (Pydantic + SQLAlchemy)
- **SQLite** - Embedded database

---

*Made with ❤️ for Midad Books | صُنع بحب لكتب مداد*
