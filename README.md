# Investment Insight Platform (IIP)

This document outlines the UI/UX design proposal and operational instructions for the Investment Insight Platform (IIP). The platform is designed to blend the familiar, efficient UI of Reddit with a specific, bias-reducing workflow required for Confidential Information Memorandum (CIM) analysis.

---

## 🚀 Getting Started & How to Run

Follow these steps to get the platform running locally.

### 1. Database (PostgreSQL)

First, ensure your Docker container for the PostgreSQL database is running.

1.  Open the **Docker Desktop** application.
2.  Open a terminal and run the following command:
    ```bash
    docker start pe-postgres
    ```

### 2. Backend Server (Python)

Next, activate the Python virtual environment and start the backend server.

1.  Open the `cim-backend` folder in VS Code.
2.  Open a new terminal within VS Code.
3.  Activate the virtual environment:
    ```bash
    .\venv\Scripts\activate
    ```
4.  Run the main application file:
    ```python
    py main.py
    ```

### 3. Ngrok Tunnel

Finally, expose your local server to the internet using Ngrok to connect with Retool.

1.  Open a second, separate terminal window.
2.  Navigate to your Ngrok executable's directory (e.g., Downloads):
    ```bash
    cd ~/Downloads
    ```
3.  Start the tunnel, pointing it to the local port your backend is running on (port 8000):
    ```bash
    .\ngrok.exe http 8000
    ```
4.  Go into your **Retool resources** and update the backend API endpoint with the new forwarding URL provided by Ngrok.

---

## UI/UX Design Proposal

> ### **Core Principle: "Analysis Before Influence"**
> Every design decision is guided by this principle. A user must provide their own analysis before they can see the analysis of their teammates to reduce confirmation bias.

---

## Page 1: The Deal Flow Dashboard (The "Home Page")

This is the main screen users see upon logging in. It provides a clean, high-level overview of all active and past deals in a feed-style layout.

### Layout

* **Header**: A simple bar at the top containing:
    * **Left**: Company/Team Logo and the platform name ("IIP").
    * **Right**: A prominent **`+ Upload CIM`** button, a search bar, and a user profile icon.
* **Main Content Area**: A feed of "CIM Posts," styled professionally for data-driven analysis. Each post is a self-contained card.

### The "CIM Post" Card

Each card in the feed represents a single CIM and contains essential, at-a-glance information.

* **CIM Title**: e.g., "Project Titan - SaaS Acquisition" (derived from the filename).
* **AI-Generated Tags**: A row of tags pulled from the AI summary (e.g., `Industry: Enterprise SaaS`, `Stage: Growth Equity`, `Revenue: $25M ARR`) for quick filtering.
* **Status Badge**: A colored badge indicating the user's required action:
    * 🔵 **Feedback Required**: You have not submitted your feedback yet.
    * 🟢 **Review Complete**: You have submitted your feedback.
    * ⚪ **Archived**: The deal process is complete.
* **Action Button**: A single, clear button: **`View Analysis & Add Feedback`**.

---

## Page 2: The Analysis & Feedback Page

Clicking `View Analysis & Add Feedback` takes the user to this page, which features a two-column layout.

### Column 1: AI-Generated Analysis (The "Report")

This column is dedicated to the structured JSON output from the backend, presented in a clean, readable format with collapsible sections.

* **Header**: CIM Title.
* **Sections**:
    * Executive Summary (expanded by default)
    * Financials (key metrics, charts)
    * Products & Services
    * Market & Competition
    * Key Risks & Mitigants
    * Team

### Column 2: The "Blind" Feedback Module

This is the most critical part of the UX. Its appearance changes based on whether the user has submitted their feedback.

* **State A: User Has NOT Submitted Feedback**
    * A large, inviting text area is the main focus, prompted with: **"What is your initial analysis? Please outline your key thoughts, questions, and concerns below."**
    * A single action button: **`Submit & View Team Feedback`**.
    * A message below the module reads: *"The team's feedback will become visible once you submit your own analysis."* No hints are given about the number of comments or who has commented.

* **State B: User HAS Submitted Feedback**
    * The input text area is replaced by a read-only view of **"Your Submitted Analysis."**
    * Below this, the **"Team Feedback"** section appears.
    * **Anonymity**: Each comment is presented in a simple card with only the text and a relative timestamp (e.g., "Submitted 2 hours ago"). No names or profile pictures are displayed.

---

## The Workflow in Action

This design directly enables the core function of gathering blind, anonymous feedback from team members.

1.  **Upload**: A team member clicks **`+ Upload CIM`**. The file is processed by the backend, and the deal appears on the dashboard.
2.  **Notification** (Future Feature): The system notifies all team members that a new CIM is ready for review.
3.  **Individual Review**: Each team member logs in and sees the new CIM on their dashboard with the 🔵 **Feedback Required** status.
4.  **Forced Independent Thought**: They click into the Analysis Page. They can read the AI summary but **cannot** see any colleague's thoughts. They are forced to form their own opinion and write it down.
5.  **Reveal**: Once they click **`Submit & View Team Feedback`**, their analysis is saved, and they immediately see the anonymous thoughts of everyone else who has already commented.
6.  **Unbiased Discussion**: With all independent thoughts documented, the team can now proceed to a discussion or meeting, having minimized initial groupthink and confirmation bias.