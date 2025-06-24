# 🚀 MCP Resume Server

![GitHub repo size](https://img.shields.io/github/repo-size/shuklaji28/MCP_Resume?color=blue)
![GitHub last commit](https://img.shields.io/github/last-commit/shuklaji28/MCP_Resume?color=green)
![License](https://img.shields.io/github/license/shuklaji28/MCP_Resume?color=brightgreen)

Welcome to the 🧠 **MCP (Machine-Connectable Profile) Resume Server** — a lightweight FastAPI-based server that exposes your professional profile in a structured, machine-readable format for **Puch AI** to read and process.

> ✅ Designed to work with `/mcp connect <url> <token>` on Puch.  
> 📦 Built using: Python, FastMCP, pyngrok  
> 🌐 Supports both local and public (ngrok) deployments

---

## 📌 Key Features

- 📄 **Serves your resume** (base64-encoded) to `/mcp` endpoint
- 🧑‍💼 Includes your name, headline, summary, LinkedIn, and GitHub links
- ⚙️ Simple config with `.env`
- 🛰️ ngrok tunnel support for external access

---

## 🛠️ How It Works

The MCP server exposes a single **GET** endpoint:

📁 Project Structure
MCP_Resume/
- ├── main.py           # 🚀 FastAPI server
- ├── .env              # 🔐 Secrets and settings
- ├── ngrok.yml         # 🌐 ngrok config (optional)
- ├── resumes/
- │   └── resume.pdf    # 📄 Your actual resume
- └── README.md         # 📘 This file


⚙️ How to Run
🔧 Step 1: Clone and Install

git clone https://github.com/shuklaji28/MCP_Resume.git
cd MCP_Resume
pip install -r requirements.txt  # or manually install: fastapi, uvicorn, pyngrok, python-dotenv

🔧 Step 2: Configure .env
PUCH_AUTH_TOKEN=your_token
NGROK_AUTH_TOKEN=your_ngrok_token
NGROK_PATH=C:\\Users\\your_user\\Downloads\\ngrok\\ngrok.exe
RESUME_PATH=resumes/resume.pdf
PORT=8085

🔧 Step 3: Start the server
python main.py

You’ll see a tunnel URL like:

https://abc123.ngrok.io/ or https://7b3a-103-70-203-245.ngrok-free.app/mcp

📡 Connect to Puch AI
Paste the following into https://puch.ai interface:

/mcp connect https://abc123.ngrok.io/mcp your_puch_auth_token

🎉 Boom! You’re now machine-connectable.

💡 Tips


🔒 Never upload .env publicly — it contains your secrets

🌍 You can inspect your /mcp output using: https://mcp.puch.ai/inspector

👨‍💻 Author
Shresth Shukla 
🔗 [LinkedIn](https://linkedin.com/in/shresthshuklaji)
🧠 Passionate about [data engineering](https://uselessai.in), AI integrations, and building cool stuff.

📜 License
MIT License

⭐ If this project helped you get noticed, leave a star on the repo — it helps others discover it too!

