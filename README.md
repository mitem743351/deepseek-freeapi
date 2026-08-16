# DeepSeek Desktop 🤖

A polished, local desktop chat experience for the free DeepSeek web service.

## What is this?

DeepSeek Desktop is a custom desktop GUI for the free chat experience at [chat.deepseek.com](https://chat.deepseek.com). It uses your existing free web account through the unofficial [`p2d-deepseek`](https://pypi.org/project/p2d-deepseek/) client.

- No paid API key is required.
- Authentication uses the `userToken` from your own DeepSeek browser session.
- Conversations and settings remain on your computer in local SQLite/JSON files.

## Requirements

- Python 3.11 or newer
- A free DeepSeek account
- Tk support for Python (normally included on Windows and macOS; Linux package names commonly include `python3-tk`)

Install all Python dependencies with:

```bash
pip install -r requirements.txt
```

## Setup

1. **Clone or download the project.**

   ```bash
   git clone https://github.com/mitem743351/deepseek-freeapi.git
   cd deepseek-freeapi
   ```

2. **Install the dependencies.** A virtual environment is recommended.

   ```bash
   python -m venv .venv
   # Windows: .venv\Scripts\activate
   # macOS/Linux: source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Get your DeepSeek auth token.**

   - Go to [chat.deepseek.com](https://chat.deepseek.com).
   - Log in with your account.
   - Press **F12** to open Developer Tools.
   - Go to the **Application** tab.
   - Select **Local Storage → chat.deepseek.com**.
   - Find the **`userToken`** key.
   - Copy its value. Treat this value like a password.

4. **Start the app.**

   ```bash
   python main.py
   ```

5. **Paste the token when prompted.** DeepSeek Desktop stores it locally in `.env` and `data/auth_token.json`; both paths are excluded from Git.

## Features

- Real-time streamed DeepSeek responses without blocking the interface
- DeepSeek V4 Flash and V4 Pro model selection
- DeepThink reasoning and live web-search toggles
- Multi-turn web-session memory for active conversations
- Responsive user and assistant message bubbles
- Markdown, tables, blockquotes, and Pygments syntax highlighting
- Copy controls for complete messages and fenced code blocks
- Dark, light, and system themes
- Animated typing indicator and automatic scrolling
- Local SQLite conversation history
- Chat search across titles and message content
- Conversation rename and delete actions
- Token management, history clearing, and Markdown export
- PyInstaller-friendly resource and writable-data paths

## Tech Stack

| Area | Technology |
| --- | --- |
| Language | Python 3.11+ |
| Desktop UI | CustomTkinter |
| DeepSeek integration | p2d-deepseek (free web account token) |
| Concurrency | `threading` + `queue.Queue` |
| History | SQLite (`sqlite3`) |
| Markdown | Python-Markdown + tkinterweb |
| Highlighting | Pygments |
| Images | Pillow |
| Configuration | JSON + python-dotenv |

Runtime data is created automatically:

```text
data/chat_history.db
data/auth_token.json
```

## Security Notes

Your `userToken` grants access to your DeepSeek web session. Never share it, paste it into an issue, or commit it to source control. If it is exposed, sign out of DeepSeek sessions and obtain a fresh token. The `.env` and `data/` paths are intentionally ignored by Git.

## ⚠️ Disclaimer

This project is unofficial and is not affiliated with, endorsed by, or supported by DeepSeek. It relies on a reverse-engineered web interface that may change without notice. Use it responsibly and in moderation, follow DeepSeek's terms and applicable policies, and only authenticate with an account you own.
