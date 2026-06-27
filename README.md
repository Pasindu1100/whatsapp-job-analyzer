# 📊 WhatsApp Job Market Analyzer: An Applied AI Pipeline

## 🚀 Project Overview
This project is an automated Data Engineering and Multimodal AI pipeline designed to extract, clean, and analyze unstructured job postings from regional WhatsApp community chats. 

Recruiters frequently share opportunities using a chaotic mix of text messages and graphic design posters. This project solves the problem of "dark data" by utilizing local Large Language Models (LLMs) and Vision-Language Models (VLMs) to convert unstructured chat histories and images into a highly structured, actionable JSON database, visualized through an interactive Streamlit dashboard.

## 🧠 System Architecture

The architecture is split into three distinct phases:

1. **Phase 1: Ingestion & Parsing (`src/parser.py`)**
   - Ingests raw `.txt` chat exports and associated media files (up to 300MB+ datasets).
   - Utilizes Python Regex to clean metadata (timestamps, senders) and reconstructs fragmented multiline messages.
   - Outputs a baseline `processed_jobs.json`.

2. **Phase 2: Multimodal AI Extraction (`src/analyzer.py`)**
   - **Text Pipeline:** Routes text-only messages to a local `gemma` LLM via Ollama to extract JSON entities (Job Title, Skills, Location).
   - **Vision Pipeline:** Detects image attachments, converts them to base64, and routes both the image and text to a local `llava` Vision model to read text directly off graphical job posters.
   - Outputs a normalized `ai_analyzed_jobs.json`.

3. **Phase 3: Market Intelligence Dashboard (`src/dashboard.py`)**
   - A Streamlit web application that consumes the structured AI output.
   - Calculates real-time metrics on the most frequently demanded skills and aggregates hiring trends.

## 🛠️ Tech Stack
- **Language:** Python 3.11+
- **AI Inference Engine:** Ollama (Local)
- **Models Used:** `gemma` (Text Extraction), `llava` (Vision-Language Processing)
- **Data Manipulation:** Pandas
- **Web Dashboard:** Streamlit
- **Automation (Optional Branch):** Playwright for live browser scraping.

## ⚙️ How to Run Locally

1. **Clone & Setup:**
   ```bash
   git clone [https://github.com/YOUR_USERNAME/whatsapp-job-analyzer.git](https://github.com/YOUR_USERNAME/whatsapp-job-analyzer.git)
   cd whatsapp-job-analyzer
   python -m venv venv
   source venv/Scripts/activate
   pip install -r requirements.txt


   ![alt text](image.png)