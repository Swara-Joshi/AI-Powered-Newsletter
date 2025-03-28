import os
import sqlite3
from flask import Flask, jsonify, request
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import schedule
import time
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from threading import Thread
import openai
from dotenv import load_dotenv

load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
openai.api_key = OPENAI_API_KEY

# Load environment variables
load_dotenv()

app = Flask(__name__)

SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY')
SENDER_EMAIL = os.getenv('SENDER_EMAIL')

DATABASE = 'subscribers.db'

from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

def initialize_driver():
    """Initialize and return a Chrome WebDriver."""
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    service = Service(ChromeDriverManager().install())  # Service needs to be imported
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver


def init_db():
    """Initialize the database and create the subscribers table if it doesn't exist."""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS subscribers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL
    )
    ''')
    conn.commit()
    conn.close()

def add_subscriber(email):
    """Add a new subscriber to the database."""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO subscribers (email) VALUES (?)", (email,))
        conn.commit()
    except sqlite3.IntegrityError:
        pass  # Email already exists in the database
    conn.close()
    
def get_subscribers():
    """Retrieve all subscribed emails from the database."""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT email FROM subscribers")
    subscribers = [row[0] for row in cursor.fetchall()]
    conn.close()
    return subscribers

def initialize_driver():
    """Initialize and return a Chrome WebDriver."""
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def get_finance_news(driver):
    """Scrape finance news from CNBC with improved selectors."""
    try:
        print("Navigating to the finance news page...")
        driver.get('https://www.cnbc.com/finance/')

        # Use more specific selectors to target actual news articles
        wait = WebDriverWait(driver, 10)
        print("Waiting for news elements...")
        
        # Target headline articles with more specific selector
        news_elements = wait.until(EC.presence_of_all_elements_located(
            (By.CSS_SELECTOR, 'div.Card-titleContainer a')
        ))
        
        print("Extracting news...")
        news = []
        
        for element in news_elements[:5]:  # Limit to 5 articles
            title = element.text.strip()
            link = element.get_attribute('href')
            
            if title and link and not link.endswith('#comments'):
                # Get summary from article
                article_summary = get_article_summary(link)
                news.append({'title': title, 'summary': article_summary, 'link': link})
                
                if len(news) >= 5:
                    break
                    
        return news
    except Exception as e:
        print(f"Error scraping CNBC Finance: {e}")
        return []

def get_article_summary(article_url):
    """Fetch article content and summarize it using GPT-4o Mini."""
    try:
        print(f"Fetching article from: {article_url}")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(article_url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract all paragraphs to get more content
        paragraphs = soup.find_all('p')
        article_text = ' '.join([p.get_text().strip() for p in paragraphs[:10]])  # Limit to first 10 paragraphs
        
        if not article_text:
            return "Summary not available - couldn't extract article content."
            
        # Use GPT-4o Mini to summarize
        return summarize_with_gpt4o_mini(article_text)
    except Exception as e:
        print(f"Error fetching or summarizing article from {article_url}: {e}")
        return "Summary not available due to technical error."

def summarize_with_gpt4o_mini(article_text):
    """Use GPT-4o Mini to generate a concise summary of an article."""
    try:
        if not article_text or len(article_text) < 50:
            return "Summary not available due to insufficient content."
            
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that summarizes news articles concisely in 2-3 sentences."},
                {"role": "user", "content": f"Summarize this article in 2-3 sentences:\n\n{article_text}"}
            ],
            max_tokens=150
        )
        
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error using GPT-4o Mini for summarization: {e}")
        return "Summary not available due to API error."

def summarize_with_gpt4(text):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Summarize the following article in 2-3 sentences:"},
                {"role": "user", "content": text}
            ],
            max_tokens=100
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error summarizing with GPT-4: {e}")
        return "Summary not available"
def get_tech_news(driver):
    """Scrape tech news from The Verge with improved selectors."""
    try:
        print("Navigating to the tech news page...")
        # Use the dedicated tech section instead of homepage
        driver.get('https://www.theverge.com/tech')
        
        wait = WebDriverWait(driver, 10)
        print("Waiting for tech news elements...")
        
        # Target main article headlines with specific selector
        news_elements = wait.until(EC.presence_of_all_elements_located(
            (By.CSS_SELECTOR, 'h2 a')  # More general selector
        ))
        
        print("Extracting tech news...")
        news = []
        
        for element in news_elements:
            title = element.text.strip()
            link = element.get_attribute('href')
            
            if title and link and 'theverge.com' in link and not link.endswith('#comments'):
                article_summary = get_article_summary(link)
                news.append({'title': title, 'summary': article_summary, 'link': link})
                
                if len(news) >= 5:
                    break
        
        print(f"Found {len(news)} tech news articles.")
        return news
    except Exception as e:
        print(f"Error scraping The Verge: {e}")
        return []


def send_email(subject, content, to_email):
    """Send an email using SendGrid with better error handling."""
    if not SENDGRID_API_KEY or not SENDER_EMAIL:
        print("SendGrid API key or sender email not configured.")
        return False

    message = Mail(
        from_email=SENDER_EMAIL,
        to_emails=to_email,
        subject=subject,
        html_content=content
    )

    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        print(f"Email sent to {to_email}. Status code: {response.status_code}")
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        if hasattr(e, 'body'):
            print(f"SendGrid error details: {e.body}")
        return False

@app.route('/subscribe', methods=['POST'])
def subscribe():
    """Handle subscription by adding an email to the database."""
    data = request.get_json()
    email = data.get('email')

    if not email:
        return jsonify({"error": "Email is required"}), 400

    # Add the email to the database
    add_subscriber(email)

    return jsonify({"message": f"Subscribed successfully with email: {email}"}), 200

@app.route('/send_newsletter', methods=['GET'])
def send_newsletter():
    """Fetch news and send a newsletter to all subscribers."""
    driver = initialize_driver()

    # Fetch finance news and tech news
    finance_news = get_finance_news(driver)
    tech_news = get_tech_news(driver)
    
    # Close the driver after use
    driver.quit()

    content = "<h1>Today's Finance & Tech News</h1>"
    
    # Finance News Section
    content += "<h2>Finance News</h2><ul>"
    if not finance_news:
        content += "<p>No Finance news available today.</p>"
    else:
        for item in finance_news:
            content += f"<li><strong>{item['title']}</strong>"
            if item['summary'] and item['summary'] != "Summary not available":
                content += f"<p>{item['summary']}</p>"
            content += f"<a href='{item['link']}'>Read more</a></li>"
    content += "</ul>"
    
    # Tech News Section
    content += "<h2>Tech News</h2><ul>"
    if not tech_news:
        content += "<p>No Tech news available today.</p>"
    else:
        for item in tech_news:
            content += f"<li><strong>{item['title']}</strong>"
            if item['summary'] and item['summary'] != "Summary not available":
                content += f"<p>{item['summary']}</p>"
            content += f"<a href='{item['link']}'>Read more</a></li>"
    content += "</ul>"

    subscribers = get_subscribers()
    
    if not subscribers:
        return jsonify({"message": "No subscribers found."}), 404

    success_count = 0
    for subscriber in subscribers:
        if send_email("Daily Finance & Tech Newsletter", content, subscriber):
            success_count += 1

    if success_count > 0:
        return jsonify({"message": f"Newsletter sent successfully to {success_count} subscribers!"}), 200
    else:
        return jsonify({"message": "Failed to send newsletters. Check SendGrid configuration."}), 500

def run_scheduler():
    """Run the scheduler to send newsletters at scheduled times."""
    schedule.every().day.at("08:00").do(send_newsletter)  # Schedule at 8 AM daily

    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute

# Start the scheduler in a separate thread
scheduler_thread = Thread(target=run_scheduler, daemon=True)
scheduler_thread.start()


# Start the scheduler in a separate thread
def start_background_scheduler():
    # Schedule to run daily at specific time
    schedule.every().day.at("20:32").do(lambda: requests.get('http://127.0.0.1:5000/send_newsletter'))
    thread = Thread(target=run_scheduler, daemon=True)
    thread.start()

if __name__ == "__main__":
    init_db()  # Ensure database is initialized
    start_background_scheduler()
    app.run(debug=True)
