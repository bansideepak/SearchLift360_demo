# Conversational AI POC App

This is a demo project showcasing a **Conversational Commerce application** built using **FastAPI**, **Streamlit**, and a custom **MCP (Model Context Protocol)** server. It features API integrations for ecommerce and hotel booking functionality.

---

## 🚀 Features

- FastAPI backend serving as an MCP server
- AI-powered chatbot for product and hotel booking queries
- Streamlit frontend for live chat interface
- Uses Gemini LLM (via API) for intelligent responses
- .env based config for credentials

---

## 🧠 How It Works

1. **Frontend (`frontend/app.py`)**: A Streamlit UI that sends chat queries.
2. **Backend (`backend/`)**:
   - `main.py`: FastAPI server entrypoint
   - `chat_handler.py`: Custom tool logic
   - `mcp_server.py`: Sets up MCP server routes/tools/prompts
3. **APIs**: Integrates with REST APIs to fetch ecommerce and hotel data.

---

## 🗂️ Folder Structure

```
DEMO/
├── .env
├── .gitignore
├── backend/
│   ├── main.py
│   ├── mcp_server.py
│   ├── chat_handler.py
│   └── requirements.txt
├── frontend/
│   ├── app.py
│   └── requirements.txt
└── venv/ (virtual environment)
```

---

## 🛠️ Setup Instructions

```bash
# 1. Clone the repo or extract this folder
# 2. Create and activate a virtual environment (optional if using venv already)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install backend requirements
cd backend
pip install -r requirements.txt

# 4. Run the FastAPI server
uvicorn main:app --reload

# 5. In a new terminal, run the frontend
cd ../frontend
pip install -r requirements.txt
streamlit run app.py
```

---

## 🧪 Known Issues

- No frontend validation for input prompts.
- Backend tools need better error handling for API failures.
- `.env` must be set manually with valid API keys (e.g., Gemini).

---

## 🌱 Future Improvements

- Add user authentication
- Deploy to Hugging Face Spaces / Render
- Add hotel filtering & pagination
- Integrate WhatsApp via Twilio

---
