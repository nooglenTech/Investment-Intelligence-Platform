# 💼 Investment Insight Platform (IIP)

A full-stack, login-enabled internal platform to analyze Confidential Information Memorandums (CIMs), inspired by Reddit's feed design but structured to reduce groupthink and improve investment workflows.

---

## 🚀 Getting Started & How to Run

Follow these instructions to run the full-stack application locally, connected to your live AWS and OpenAI services.

### Prerequisites

* An AWS Account with S3 and RDS configured.
* An OpenAI API Key.
* Python 3.9+ and `pip`.
* Node.js (v16+) and `npm` or `yarn`.

### 1. Configure Backend Environment

Before running the backend, you must provide it with the necessary API keys and service endpoints.

1.  Navigate into the `cim-backend` directory.
2.  Create a file named `.env`.
3.  Copy the block below into your new `.env` file and replace the placeholder values with your actual secret keys and URLs.

    ```bash
    # .env file for local development
    
    # Found in AWS RDS -> Your DB -> Connectivity & security
    DATABASE_URL="postgresql://YOUR_DB_USER:YOUR_DB_PASSWORD@YOUR_RDS_ENDPOINT:5432/postgres"
    
    # Found at [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
    OPENAI_API_KEY="sk-..."
    
    # Found in the AWS S3 Console
    S3_BUCKET_NAME="your-s3-bucket-name"
    AWS_REGION="your-aws-region" # e.g., us-east-1
    
    # Found in AWS IAM -> Users -> Your User -> Security credentials -> Create access key
    AWS_ACCESS_KEY_ID="AKIA..."
    AWS_SECRET_ACCESS_KEY="..."
    ```

### 2. Run the Backend Server (Python + FastAPI)

1.  From the `cim-backend` directory, create a Python virtual environment and install the required packages:

    ```bash
    # Create the virtual environment
    py -m venv venv

    # Activate it (Windows)
    .\venv\Scripts\activate

    # Install dependencies
    cd cim-backend
    pip install -r requirements.txt
    ```

2.  With your virtual environment activated, start the server:

    ```bash
    uvicorn main:app --reload
    ```
    The backend API is now running and accessible at `http://localhost:8000`.

### 3. Run the Frontend Server (Next.js)

1.  In a **new terminal**, navigate to your `iip-frontend` directory.
2.  Install the Node.js dependencies:

    ```bash
    npm install
    ```

3.  Start the frontend development server:

    ```bash
    npm run dev
    ```
    The web application is now running and accessible at `http://localhost:3000`.

---

## 🧱 Platform Architecture

| Layer           | Technology         |
|----------------|--------------------|
| Frontend       | Retool / React     |
| Backend        | FastAPI (Python)   |
| Database       | PostgreSQL (Docker)|
| AI Analysis    | OpenAI GPT-4       |
| Storage        | AWS S3 (PDF uploads) |
| Hosting        | AWS (EC2/S3/Elastic Beanstalk planned) |
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

| File/Folder       | Purpose                        |
|-------------------|--------------------------------|
| `main.py`         | FastAPI app entry point        |
| `services.py`     | PDF parsing + AI prompt logic  |
| `models.py`       | SQLAlchemy DB schema           |
| `requirements.txt`| All backend dependencies       |
| `AnalysisCard.tsx`| Frontend display component     |

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
