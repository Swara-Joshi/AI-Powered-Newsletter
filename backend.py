from fastapi import FastAPI
import sqlite3
import smtplib
from email.mime.text import MIMEText
import requests
import openai
import yfinance as yf
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

# Database Setup
conn = sqlite3.connect("subscribers.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS subscribers (email TEXT, category TEXT, openai_api_key TEXT)")
conn.commit()


# Create the FastAPI app
app = FastAPI()

# Fetch Finance News (Yahoo Finance) using Web Scraping
def fetch_finance_news():
    url = "https://finance.yahoo.com/"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    
    news_list = []
    articles = soup.find_all("li", class_="js-stream-content")  # Find all finance news
    for article in articles[:5]:  # Get top 5 finance news articles
        title = article.find("h3").get_text() if article.find("h3") else "No Title"
        link = article.find("a")["href"] if article.find("a") else "#"
        news_list.append(f"{title} - https://finance.yahoo.com{link}")
    
    return news_list

# Fetch Tech News (TechCrunch) using Web Scraping
def fetch_tech_news():
    url = "https://techcrunch.com/"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    
    news_list = []
    articles = soup.find_all("a", class_="post-block__title__link", limit=5)  # TechCrunch articles
    for article in articles:
        title = article.get_text().strip()
        link = article["href"]
        news_list.append(f"{title} - {link}")
    
    return news_list

# Endpoint to check if Finance News is being scraped correctly
@app.get("/scrape_finance/")
def scrape_finance():
    finance_news = fetch_finance_news()
    return {"finance_news": finance_news}

# Endpoint to check if Tech News is being scraped correctly
@app.get("/scrape_tech/")
def scrape_tech():
    tech_news = fetch_tech_news()
    return {"tech_news": tech_news}
