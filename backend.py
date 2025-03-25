from fastapi import FastAPI, HTTPException
import sqlite3
import smtplib
from email.mime.text import MIMEText
import requests
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv
import re

# Load environment variables
load_dotenv()
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

# FastAPI app instance
app = FastAPI()

# Database Setup
conn = sqlite3.connect("subscribers.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS subscribers (email TEXT, category TEXT)")
conn.commit()

# Function to fetch finance news (Yahoo Finance) using Web Scraping
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

# Function to fetch tech news (TechCrunch) using Web Scraping
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

# Function to send email (SMTP setup)
def send_email(recipient_email, subject, body):
    try:
        # SMTP setup (using Gmail or Outlook for example)
        if re.match(r"[^@]+@[^@]+\.[^@]+", recipient_email):  # Check if the email is valid
            if "@gmail.com" in recipient_email:
                server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
                server.login(EMAIL_USER, EMAIL_PASSWORD)
            elif "@outlook.com" in recipient_email:
                server = smtplib.SMTP_SSL('smtp.office365.com', 465)
                server.login(EMAIL_USER, EMAIL_PASSWORD)
            else:
                raise Exception("Unsupported email domain.")
            
            msg = MIMEText(body)
            msg['Subject'] = subject
            msg['From'] = EMAIL_USER
            msg['To'] = recipient_email
            
            server.sendmail(EMAIL_USER, recipient_email, msg.as_string())
            server.quit()
            print(f"Email sent to {recipient_email} with subject '{subject}'")
        else:
            raise Exception(f"Invalid email address: {recipient_email}")
    except smtplib.SMTPAuthenticationError as e:
        raise HTTPException(status_code=500, detail=f"Authentication failed: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Email sending failed: {str(e)}")


# Endpoint to subscribe to a newsletter
@app.post("/subscribe/")
async def subscribe(email: str, category: str):
    try:
        # Add subscriber to the database
        cursor.execute("INSERT INTO subscribers (email, category) VALUES (?, ?)", (email, category))
        conn.commit()
        
        print(f"Subscription successful for {email} with category {category}")
        
        return {"message": "Subscription successful"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Subscription failed: {str(e)}")

# Endpoint to send a newsletter to subscribers
@app.get("/send_newsletter/")
async def send_newsletter():
    try:
        # Fetch the latest news (finance or tech, depending on the category)
        finance_news = fetch_finance_news()
        tech_news = fetch_tech_news()

        # Combine the news into one body for the email
        news_body = "Latest Finance News:\n\n"
        news_body += "\n".join(finance_news) + "\n\n"
        news_body += "Latest Tech News:\n\n"
        news_body += "\n".join(tech_news)

        # Debug print to check the content of the news body
        print(f"News Body to be sent:\n{news_body}")
        
        # Get the list of subscribers from the database
        cursor.execute("SELECT email, category FROM subscribers")
        subscribers = cursor.fetchall()
        
        # Debug print to check the list of subscribers
        print(f"Subscribers: {subscribers}")

        # Send the email to each subscriber
        for subscriber in subscribers:
            email, category = subscriber
            print(f"Processing subscription for: {email} (Category: {category})")
            
            if category.lower() == "finance":
                send_email(email, "Finance Newsletter", news_body)
            elif category.lower() == "tech":
                send_email(email, "Tech Newsletter", news_body)

        return {"message": "Newsletter sent successfully"}
    
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to send newsletter: {str(e)}")

# Start the FastAPI app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
