# 🏥 Data Health Governor

An intelligent, automated workflow for database health monitoring, data quality issue detection, human-in-the-loop approval, and automatic remediation.

<img width="1234" height="527" alt="Screenshot 2025-12-04 140706" src="https://github.com/user-attachments/assets/fe8cfbc7-f63f-45a4-a518-b045f661c993" />


### 📖 Overview
Data Health Governor is an end-to-end automation solution designed to maintain the integrity and quality of database systems. Built on n8n, this project orchestrates a sophisticated pipeline that combines AI-powered analysis (LLMs), human oversight, and automated SQL remediation to ensure data remains clean, consistent, and reliable.

The Business Challenge
Modern databases inevitably accumulate "data debt":


Placeholder values (e.g., "N/A", "UNKNOWN") that skew analytics.


Inconsistent formats (e.g., mixed date styles) causing query failures.


Orphaned keys and NULLs in critical fields.

Traditional cleanup requires manual table-by-table scanning, which is time-consuming and error-prone. This project automates the "Trust but Verify" mindset: automatically finding issues, but never fixing them without explicit human approval.


## 🏗️ Architecture & Workflow
The solution is divided into four sequential stages to ensure safety and transparency.

### Stage 1: Intelligent Investigation
Goal: Scan the database and identify issues without human intervention.

The workflow triggers (manually or on a schedule) and activates the Master Data Investigator Agent. This AI agent:

Reads the full schema and samples data from the PostgreSQL database.

Identifies specific quality issues (NULLs, constraints, formats).

Outputs a structured JSON list of issues.


Splits the issues: Those fixable by SQL are sent to the approval queue; others are logged for manual review.


<img width="1205" height="587" alt="Screenshot 2025-12-04 140525" src="https://github.com/user-attachments/assets/e1fbba67-b879-44ab-a675-7957cafb3af1" />


### Stage 2: Human-in-the-Loop Approval
Goal: Ensure no data is mutated without stakeholder consent.

Before any SQL is run, the system acts as a governance gatekeeper:

Availability Check: Sends an initial email asking if the stakeholder is available to review fixes.


Wait for Trigger: The workflow pauses until the user clicks "YES".

<img width="520" height="619" alt="Screenshot 2025-12-04 140543" src="https://github.com/user-attachments/assets/13756490-cd0a-4f2a-8ccb-61be33f73cfb" />


Once confirmed, the system loops through specific issues one by one. The user receives a detailed breakdown of the issue and the proposed SQL fix, with options to Approve or Decline.

<img width="1539" height="589" alt="Screenshot 2025-12-04 131029" src="https://github.com/user-attachments/assets/21dc0569-2ee3-4d62-8219-039f3a3e30a5" />


### Stage 3: Automated Remediation (SQL Fixing)
Goal: Execute approved fixes safely and log the results.

Upon receiving approval, the Data Issue Fixer Agent:

Generates the precise SQL query required for the fix.

Passes the query to the SQL Query Executor, a dedicated sub-workflow designed for safe execution.

Verifies the fix was successful and captures the exact query used for the audit trail.

<img width="1527" height="583" alt="Screenshot 2025-12-04 131115" src="https://github.com/user-attachments/assets/5b5fbc1d-d2a3-4a4b-ae94-8c116d9e6b90" />


Sub-Workflow: SQL Query Executor
To maintain modularity and security, raw SQL execution is handled by a separate micro-workflow.

<img width="587" height="339" alt="Screenshot 2025-12-04 141335" src="https://github.com/user-attachments/assets/5f6ee3d1-98aa-4ce1-845e-bd3b5ff57989" />


Stage 4: Comprehensive Reporting
Goal: Provide full visibility and an audit trail.

Finally, the Data Health Reporter Agent aggregates all actions—fixed issues, skipped issues, and pending manual reviews—into a polished report.


Google Docs Generation: Creates a professionally formatted document with headings and bullet points.


Delivery: Emails the stakeholder a direct link to the final report.

<img width="777" height="634" alt="Screenshot 2025-12-04 135809" src="https://github.com/user-attachments/assets/f0582558-bd31-4aa6-a4e2-c8b3fd34741c" />



### 🛠️ Tech Stack
Orchestration: n8n (Workflow Automation)

Database: PostgreSQL

AI/LLM:

Groq (Llama 3 / Mixtral): For high-speed schema analysis and issue detection.

Google Gemini: For complex reasoning and report generation.

Integrations:

Gmail: For interactive approval emails.

Google Docs/Drive: For report generation and storage.


### 🔮 Future Roadmap

Slack Integration: Replace email approvals with interactive Slack Block Kit buttons for faster turnaround.

Dashboarding: Push health metrics to a BI tool (PowerBI/Tableau) to track data quality over time.

Auto-Rollback: Implement immediate transaction rollback if the "Row Count" of a fix exceeds a safety threshold.
