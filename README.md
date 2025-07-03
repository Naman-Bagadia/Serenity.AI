# SerenityAI---FusionHacks1---Hackathon

🔮 Serenity AI – Full Project Setup (Frontend + Backend + AI)

🌐 Frontend: HTML + JavaScript + CSS
🧠 Backend: Python + Hume Voice AI + FastAPI

📦 PART 1: Set Up the Backend (Python AI with Hume Voice API)
✅ Step 1: Install Python & Virtual Environment
Install Python 3.9+ from https://www.python.org.

Open terminal (CMD or PowerShell).

Create and activate a virtual environment:
python -m venv serenity_env
serenity_env\Scripts\activate   # Windows
source serenity_env/bin/activate # macOS/Linux

Step 2: Add Dependencies (requirements.txt)

hume[microphone]
fastapi
uvicorn
jinja2

then install 

pip install -r requirements.txt

Step 3: Create Project Files & Folders
Create a folder structure like this:

SerenityAI_Backend/
│
├── ai_server.py         ← Python backend (AI interaction)
├── requirements.txt     ← Required libraries
├── templates/
│   └── index.html       ← Optional (for browser display)

✅ Step 4: Create AI Server (ai_server.py)erver.py:

Replace "your-hume-api-key" with your real API key.

✅ Step 5: Add index.html to templates/

✅ Step 6: Run the Backend

run the backend
uvicorn ai_server:app --reload

🌐 PART 2: Frontend (HTML + JavaScript + CSS)

✅ Step 1: Create Frontend Files
In frontend/ folder:

--------------------------------------------------------------------------------------------------------------------------------------------------------------

📘 Final README Sample (use before launching)
🚀 Welcome to Serenity AI!
Before launching the backend, please make sure to:

Create a folder called templates inside the backend/ folder.

Add a basic index.html file to that templates folder.

Install dependencies from requirements.txt.

Launch the backend using:

bash
Copy
Edit
uvicorn ai_server:app --reload
Open the frontend/index.html in your browser or run a local web server.

✅ You're now ready to interact with Serenity AI – your emotional voice assistant powered by Hume.


