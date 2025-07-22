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
# 💼 Investment Insight Platform (IIP)

A full-stack, AI-powered internal platform to streamline the analysis of Confidential Information Memorandums (CIMs), reduce groupthink through a blind-feedback workflow, and integrate external market data for more informed decision-making.

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
    DATABASE_URL="postgresql://YOUR_DB_USER:YOUR_DB_PASSWORD@YOUR_RDS_ENDPOINT:5432/postgres"
    OPENAI_API_KEY="sk-..."
    S3_BUCKET_NAME="your-s3-bucket-name"
    AWS_REGION="your-aws-region" # e.g., us-east-1
    AWS_ACCESS_KEY_ID="AKIA..."
    AWS_SECRET_ACCESS_KEY="..."
    ```

### 2. Run the Backend & Frontend Servers

Follow the instructions in the original `README.md` to start both the Python backend and the Next.js frontend servers in separate terminals.

---

## 🧱 Platform Architecture

| Layer          | Technology                     | Purpose                               |
|----------------|--------------------------------|---------------------------------------|
| Frontend       | Next.js (React)                | User Interface & Experience           |
| Backend        | FastAPI (Python)               | API, Business Logic, Orchestration    |
| Database       | PostgreSQL (AWS RDS)           | Storing deal, feedback & analysis data|
| AI Analysis    | OpenAI GPT-4 Series            | CIM text analysis & summarization     |
| File Storage   | AWS S3                         | Storing uploaded PDF documents        |
| External Data  | GF Data API (Planned)          | Live private market transaction data  |
| Hosting        | AWS Amplify & Elastic Beanstalk (Planned) | Scalable deployment for frontend/backend |
| Authentication | Clerk / Auth0 (Planned)        | Secure user login and management      |

---

## 🗺️ Project Roadmap & Future Enhancements

This project is designed to evolve from a CIM analysis tool into a comprehensive deal evaluation platform.

### Phase 1: Core Functionality (In Progress)

* [✅] **AI-Powered CIM Analysis:** Upload CIM PDFs to AWS S3 and auto-generate a detailed, structured summary using OpenAI.
* [✅] **Persistent Storage:** Store all deal data and analysis in a secure AWS RDS PostgreSQL database.
* [✅] **Blind Feedback Workflow:** Users must submit their own qualitative and quantitative feedback before viewing anonymous team comments, reducing cognitive bias.
* [✅] **Interactive Dashboard:** A clean, Reddit-style feed of all deals, showing key financial metrics at a glance.
* [ ] **Secure User Login:** Implement a full authentication system for team members.
* [ ] **View/Download CIM:** Add a button to each deal page to open the original PDF from S3 in a new tab or an in-app viewer.

### Phase 2: Intelligence & Workflow Automation (Next Steps)

* **Advanced AI Summary:** Enhance the OpenAI prompt to be more nuanced and detailed. Add a dedicated "Growth Section" to extract and display historical and projected growth rates (CAGR) for Revenue, EBITDA, and FCF, as well as the industry's CAGR.
* **Professional Feedback Module:** Evolve the star-rating system into a more professional set of inputs relevant to submitting an IOI (e.g., sliders or dropdowns for Valuation, Growth, Risk, etc.).
* **Automated CIM Ingestion:** Develop a service to query a dedicated email inbox (e.g., `cims@yourfirm.com`), automatically extract PDF attachments, and create new deals in the IIP, transitioning from manual uploads.

### Phase 3: Data Integration & Valuation Tools (Future Vision)

* **GF Data Integration:** Connect to the GF Data API. On each deal page, automatically query for relevant industry transaction data based on the deal's NAICS code. Display valuation multiples (e.g., Revenue, EBITDA) in a graph or table to provide live market context for typical valuations.
* **Valuation Graphics:** Develop interactive charts that model valuation ranges based on key inputs (e.g., growth rates, desired IRR, standard deviation, size premium) to enforce price discipline, similar to existing Excel models.
* **Advanced Filtering & Search:** Implement a robust search and filtering system on the dashboard based on industry, size, status, and other key factors.

---

## 🎨 UI/UX Design Summary

> ### "Analysis Before Influence"
> The user experience enforces independent thought before peer influence.

The platform provides a clean, data-dense interface designed for efficiency. The two-column analysis view separates the objective AI report from the subjective team feedback, creating a clear workflow for evaluation.
