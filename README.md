# NL2SQL Voice Assistant

Convert natural language to SQL queries using voice or text input - 100% Free!

## 🚀 Features

- **Voice Input**: Speak your queries naturally
- **NL to SQL**: Convert natural language to SQL using local AI models
- **RAG Integration**: Context-aware query generation
- **Visual Reports**: Charts and graphs from query results
- **Multi-format Export**: CSV, Excel, and PDF exports
- **Zero Cost**: All free, open-source tools

## 📋 Prerequisites

- Python 3.10+
- PostgreSQL 16+
- Windows 10/11 (or Linux/macOS)

## 🔧 Installation

1. **Clone or navigate to this project**
   ```bash
   cd C:\Users\nani0\PycharmProjects\nl2sql_assistant
   ```

2. **Install dependencies** (in progress)
   ```bash
   pip install -r requirements.txt
   ```

3. **Setup PostgreSQL database**
   - Open pgAdmin
   - Create database: `nl2sql_db`
   - Run the SQL scripts in `src/database/schema.sql`

4. **Configure database connection**
   - Edit `config.py` with your PostgreSQL credentials

## 🎯 Usage

```bash
python main.py
```

## 📚 Project Structure

```
nl2sql_assistant/
├── src/
│   ├── database/      # Database connection and queries
│   ├── llm/           # NL2SQL conversion with RAG
│   ├── voice/         # Speech-to-text and text-to-speech
│   ├── reports/       # Report generation and visualization
│   └── gui/           # PyQt6 GUI
├── data/              # Schema docs and FAISS index
├── tests/             # Unit tests
└── main.py            # Application entry point
```

## 🧪 Testing

```bash
pytest tests/ -v
```

## 📝 License

MIT License - Free for personal and commercial use

## 🤝 Contributing

Contributions welcome! This is a learning project following best practices.

## 📧 Support

For issues or questions, create an issue in the repository.

