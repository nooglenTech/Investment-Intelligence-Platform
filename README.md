# 💼 Investment Insight Platform (IIP)

A full-stack, login-enabled internal platform to analyze Confidential Information Memorandums (CIMs), inspired by Reddit's feed design but structured to reduce groupthink and improve investment workflows.

---

## 🚀 Getting Started & How to Run

Follow these instructions to run the app locally.

### 1. 🐘 Start PostgreSQL (Database)

Make sure Docker is running and start the PostgreSQL container:

```bash
docker start pe-postgres
```

### 2. 🐍 Start the Backend Server (Python + FastAPI)

Activate your Python virtual environment and run the backend server:

```bash
cd cim-backend
.\venv\Scripts\activate
py main.py
```

### 3. 🌐 Expose API with Ngrok (for Retool or Frontend Access)

Open a new terminal, navigate to your Ngrok directory, and run:

```bash
cd ~/Downloads
.\ngrok.exe http 8000
```

Copy the forwarding URL (e.g., `https://abc123.ngrok.io`) and paste it into your Retool resource or frontend config.

---

## 🧱 Platform Architecture

| Layer           | Technology         |
|----------------|--------------------|
| Frontend       | Retool / React     |
| Backend        | FastAPI (Python)   |
| Database       | PostgreSQL (Docker)|
| AI Analysis    | OpenAI GPT-4       |
| Storage        | AWS S3 (PDF uploads) |
| Hosting        | AWS (EC2/S3/Elastic Beanstalk planned) |
| Authentication | Full login/signup support (planned via Auth0 or custom JWT) |

---

## 🔒 Platform Capabilities

### ✅ Core Features

- Secure **login** for each team member.
- Upload **CIM PDFs** and auto-generate structured AI analysis.
- **"Blind feedback" workflow** — users must submit their own analysis before viewing team comments.
- Clean Reddit-style feed of all current and past deals.
- **Tagging & status badges** to organize pipeline progress.
- Persistent storage of CIMs and analysis data using **PostgreSQL**.
- File storage (PDFs, metadata) in **AWS S3**.
- **Notifications** when new CIMs are uploaded (email/in-app planned).

---

## 🎨 UI/UX Design Summary

> ### "Analysis Before Influence"
> The user experience enforces independent thought before peer influence.

---

## 🏠 Page 1: Deal Flow Dashboard (Home)

Displays all CIMs as cards in a scrollable feed.

### Layout

- **Header Bar**:
  - Left: Team logo + “IIP”
  - Right: `+ Upload CIM`, search bar, user profile
- **CIM Post Card**:
  - 📄 Title: e.g. “Project Titan – SaaS Acquisition”
  - 🏷️ Tags: Industry, Stage, Revenue
  - 🟢 Status Badge:
    - 🔵 Feedback Required
    - 🟢 Review Complete
    - ⚪ Archived
  - 🔎 Action: `View Analysis & Add Feedback`

---

## 📊 Page 2: Analysis & Feedback View

Clicking a CIM card opens a two-column analysis + feedback view.

### Left Column: AI-Generated Report

- Company
- Industry
- Financials (actuals vs. estimates)
- Investment Thesis
- Red Flags
- Summary
- Confidence Score

Rendered cleanly with collapsible sections.

### Right Column: Blind Feedback Module

#### State A: Feedback Not Submitted

- Large text box prompt:  
  _"What is your initial analysis? Outline key thoughts, questions, concerns."_
- Action button: `Submit & View Team Feedback`
- No hints about other comments shown

#### State B: Feedback Submitted

- Your submitted analysis shown read-only
- Anonymous feedback from team members appears below
- Each comment shows **text only** and **relative timestamp** (e.g., “2h ago”)

---

## 🔁 Workflow in Action

1. **Upload CIM** → File is parsed, analyzed, and posted
2. **Team Notification** → (Coming soon) everyone is alerted to review
3. **Individual Review** → Team members view AI report but not each other's thoughts
4. **Submit Analysis** → User submits feedback
5. **View Team** → Blind feedback is revealed post-submission
6. **Discuss** → Meeting or chat can now happen with unbiased inputs

---

## 🧠 Future Enhancements

- 🔔 Slack/Email notifications for new deals
- 📆 Due date & reminder tracking
- 🔍 Advanced search/filtering
- 👥 Role-based access control
- 📥 Integrated chat or comments
- 🧾 Export to memo format

---

## 📁 File Locations

| File/Folder       | Purpose                        |
|-------------------|--------------------------------|
| `main.py`         | FastAPI app entry point        |
| `services.py`     | PDF parsing + AI prompt logic  |
| `models.py`       | SQLAlchemy DB schema           |
| `requirements.txt`| All backend dependencies       |
| `AnalysisCard.tsx`| Frontend display component     |

---

## 📦 Dependencies

Key backend packages (see `requirements.txt`):

- `fastapi`
- `sqlalchemy`
- `openai`
- `PyMuPDF`
- `psycopg2-binary`
- `python-dotenv`
- `uvicorn`
- `pydantic`
- `python-multipart`

---

## 📬 Contact

For internal use at **Author Capital Partners**. Reach out to Jet for access or deployment help.
