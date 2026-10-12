# 🤖 AI Code Reviewer

![License](https://img.shields.io/badge/license-MIT-green)
![Build](https://img.shields.io/badge/build-passing-brightgreen)
![Status](https://img.shields.io/badge/deployed-Railway-blue)
![Frontend](https://img.shields.io/badge/frontend-Netlify-green)

AI Code Reviewer is a web application that allows developers to submit their code and receive instant, AI-generated feedback on **bugs**, **suggestions**, **readability**, **efficiency**, and a **corrected version** (if applicable). It also compares the submitted code with ideal sample solutions and stores all submissions in a history log.

---

## 🔀 About this fork

Forked from [Vashu2003/AI-Code-Reviewer](https://github.com/Vashu2003/AI-Code-Reviewer). The original app, UI and deployment are Vashu Singh's work. This fork adds:

- **Review modes**: General, Security, Performance or Code Style, chosen in the UI and sent to the model as a focused instruction.
- **Structured model output**: Gemini returns JSON that matches a Pydantic schema (`ReviewResult`) through the `google-genai` SDK. This replaces the regex parsing of Markdown headings, which silently produced empty or wrong fields whenever the model changed its formatting.
- **Plagiarism-resistant similarity** (`Backend/app/similarity.py`): code is normalised to tokens (identifiers → `ID`, literals → `STR`/`NUM`, comments and docstrings removed) and compared with a token-sequence match and with winnowing fingerprints, the algorithm behind MOSS. A copy with renamed variables, new comments and reordered functions scores 88% (raw `difflib` gave 12%); unrelated code stays around 40%.
- **Backend fixes**: per-request DB sessions through a FastAPI dependency (sessions used to leak whenever a request failed), a blocking Gemini call no longer run inside `async def`, input validation (unknown review modes and languages get a 422), case-insensitive sample lookup, suggestions stored as JSON (suggestions containing commas used to be split), history sorted newest first with pagination, and automatic columns for databases created by older versions.
- **Security**: removed a Gemini API key that was hard-coded in `render.yaml`, made CORS origins configurable through `ALLOWED_ORIGINS`, and stopped tracking the local SQLite database.
- **Tests and CI**: 18 pytest tests, with the Gemini call mocked, run on every push via GitHub Actions.

Run the backend tests:

```bash
cd Backend
pip install -r requirements.txt -r requirements-dev.txt
pytest
```

---

## 🌐 Live Demo

🚀 [Live App on Netlify](https://devaudit0.netlify.app/)

---

## 📁 Project Structure

```
AI-Code-Reviewer/
├── Backend/ # FastAPI backend
│ ├── app/ # Main app files
│ │ ├── main.py
│ │ ├── models.py
│ │ ├── database.py
│ │ ├── schemas.py
│ │ └── ai_utils.py
│ ├── requirements.txt
│ └── start.sh
├── Frontend/ # React + Tailwind frontend (Vite)
│ ├── src/
│ │ ├── components/
│ │ ├── pages/
│ │ ├── App.jsx
│ │ └── main.jsx
│ ├── public/
│ ├── vite.config.js
│ └── .env
└── README.md
```

---

## 🧠 Features

- ✅ Submit Python or JavaScript code
- 🧠 AI-generated feedback using Gemini API
- 📊 Readability & efficiency scoring
- 🐞 Bug detection & suggestions
- 💡 Improved code recommendations
- 🧩 Similarity check with ideal sample answers
- 🕓 Submission history viewer
- 🧑‍🏫 Admin panel to add sample answers
- 💻 Monaco-based code editor

---

## 💡 Tech Stack

**Frontend**

- React (Vite)
- TailwindCSS
- Axios
- Monaco Editor
- Chart.js
- Lucide Icons
- Deployed on **Netlify**

**Backend**

- FastAPI
- SQLAlchemy + SQLite
- Google Generative AI (Gemini 2.5 Pro)
- Uvicorn
- Deployed on **Railway**

---

## 🔧 Setup Instructions

### ⚙️ Backend

```bash
cd Backend
python -m venv venv
source venv/bin/activate  # Or venv\Scripts\activate on Windows
pip install -r requirements.txt

# Set up .env
echo "GEMINI_API_KEY=your-api-key-here" > .env

# Run server
uvicorn app.main:app --reload
```

### ⚙️ Frontend

```bash
cd Frontend
npm install

# Create .env file
echo "VITE_API_BASE_URL=http://localhost:8000" > .env

npm run dev
```

### ⚙️ Environment Variables

- Backend

```bash
GEMINI_API_KEY=your-api-key-here
```

- Frontend

```bash
VITE_API_BASE_URL=http://localhost:8000
```

---

### Screenshots

<h2>📸 Screenshots</h2>
<div align="center">
<table>
  <tr>
    <td><img src="Frontend/src/assets/ScreenShots/Screenshot 2025-07-05 210133.png" alt="Home Page" width="300"/></td>
    <td><img src="Frontend/src/assets/ScreenShots/Screenshot 2025-07-05 211454.png" alt="Submit Code Page" width="300"/></td>
    <td><img src="Frontend/src/assets/ScreenShots/Screenshot 2025-07-05 210331.png" alt="Feedback Panel" width="300"/></td>
  </tr>
  <tr>
    <td align="center"><strong>Home Page</strong></td>
    <td align="center"><strong>Submit Code Page</strong></td>
    <td align="center"><strong>Feedback Panel</strong></td>
  </tr>
  <tr>
    <td><img src="Frontend/src/assets/ScreenShots/Screenshot 2025-07-05 210441.png" alt="Add Sample" width="300"/></td>
    <td><img src="Frontend/src/assets/ScreenShots/Screenshot 2025-07-05 210457.png" alt="History" width="300"/></td>
    <td><img src="Frontend/src/assets/ScreenShots/Screenshot 2025-07-05 210523.png" alt="Mobile View" width="300"/></td>
  </tr>
  <tr>
    <td align="center"><strong>Add Sample Answer</strong></td>
    <td align="center"><strong>Sample Answers</strong></td>
    <td align="center"><strong>Submission History</strong></td>
  </tr>
</table>
</div>

---
### 📝 License

## MIT License © 2025 Vashu Singh

### Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/)
- [React](https://reactjs.org/)
- [TailwindCSS](https://tailwindcss.com/)
- [Axios](https://axios-http.com/)
- [Monaco Editor](https://microsoft.github.io/monaco-editor/)
- [Chart.js](https://www.chartjs.org/)
- [Lucide Icons](https://lucide.dev/)
- [Netlify](https://www.netlify.com/)
- [Railway](https://railway.app/)
