# 📊 Data Analytics Portfolio

> A collection of end-to-end data science and AI projects covering statistical analysis, inventory optimization, sales performance, and intelligent database automation.

---

## 🗂️ Projects

| Project | Description | Tools |
|---|---|---|
| [Vendor Performance & Inventory Analysis](#-vendor-performance--inventory-analysis) | EDA + AI-powered analyst on 1.5GB+ beverage industry data | Python, MCP, Groq AI, SQLite |
| [Product Sales Performance](#-product-sales-performance) | Sales trend analysis across products, categories and time periods | Python, Pandas, Matplotlib |
| [Data Health Governor](#-data-health-governor) | Automated database health monitoring with human-in-the-loop approval | n8n, PostgreSQL, Groq, Gemini |

---

## 🏪 Vendor Performance & Inventory Analysis

A two-part project on a real-world beverage industry dataset (1.5GB+).

**Part 1 — Manual Analysis:** End-to-end EDA and statistical hypothesis testing across 10,692 products and 200+ vendors. Key finding: low-volume vendors deliver 41.57% profit margins vs 31.18% for top vendors — a statistically significant paradox (p < 0.05). Identified $2.71M in trapped inventory capital across 198 brands.

**Part 2 — AI Analyst:** Built a local AI analyst using Anthropic's MCP Protocol and Groq AI (LLaMA 3.3-70B) that queries the same database using plain English — handling 1.5GB+ data that no online LLM can process. Supports two interfaces: terminal (natural language → SQL) and MCP Inspector v0.21.1 (browser-based tool testing).

📁 [View Project](./vendor_sales_analysis/)

---

## 📈 Product Sales Performance

Analysis of sales data across various products, locations, and time periods to identify revenue drivers, seasonal trends, and consumer purchase behavior. Enables data-driven decisions for inventory optimization and product strategy.

📁 [View Project](./Product_Sales_Performance/)

---

## 🏥 Data Health Governor

An intelligent n8n automation workflow for database health monitoring. Combines AI-powered issue detection (Groq + Gemini) with human-in-the-loop email approval before executing any SQL fixes. Generates a full audit report in Google Docs after every run. Follows a "Trust but Verify" approach — never mutates data without explicit stakeholder consent.

📁 [View Project](./Data_Health_Governor/)

---

## 👤 Author

**Krishna Kant Sahu**
- GitHub: [@Krishnakant25](https://github.com/Krishnakant25)

---

*More projects coming soon.*
