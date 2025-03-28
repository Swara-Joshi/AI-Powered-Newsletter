# Newsletter AI

## 📌 Project Overview
Newsletter AI is a full-stack web application that automates news aggregation, summarization, sentiment analysis, and personalized email delivery. The application:

- Scrapes the latest finance and tech news using **Selenium** and **BeautifulSoup**.
- Uses **OpenAI's GPT model** for advanced content summarization.
- Provides a Flask-based web interface for user interaction.

## 🚀 Features
- **Web Scraping**: Extracts news articles from finance and tech websites.
- **AI Summarization & Sentiment Analysis**: Generates concise summaries and sentiment scores.
- **Email Newsletter Automation**: Sends personalized email newsletters to subscribers.
- **User Management**: Allows users to subscribe and manage their preferences.
- **Scheduler**: Automates daily news updates.

## 🏗️ Tech Stack
- **Backend**: Flask (Python)
- **Web Scraping**: Selenium, BeautifulSoup
- **AI Model**: OpenAI API (GPT)
- **Database**: SQLite 
- **Email Service**: SendGrid API
- **Scheduler**: `schedule` library
- **Frontend**: Streamlit

## ⚙️ Installation & Setup
### 1️⃣ Clone the Repository
```bash
git clone https://github.com/yourusername/newsletter-ai.git
cd newsletter-ai
```

### 2️⃣ Set Up a Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3️⃣ Install Dependencies
```bash
pip install -r requirements.txt
```

### 4️⃣ Set Up Environment Variables
Create a `.env` file and configure API keys:
```plaintext
OPENAI_API_KEY=your_openai_api_key
SENDGRID_API_KEY=your_sendgrid_api_key
EMAIL_SENDER=your_email@example.com
```

### 5️⃣ Run the Application
```bash
streamlit run frontend.py
python backend.py
```
Access the app at **http://127.0.0.1:5000/**

## 🎯 Usage Guide
1. **Subscribe to the Newsletter** via the web interface.
2. **Receive AI-generated News Summaries** via email daily.


## 🔥 Future Enhancements
- Add **customizable topics** for user preferences.
- Implement **real-time notifications** for breaking news.
- Introduce a **dashboard** for user analytics.


## 💡 Author
Developed by **Swara Joshi** 
