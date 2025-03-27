import os
import sqlite3
from flask import Flask, jsonify, request
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import schedule
import time
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from threading import Thread

# Load environment variables
load_dotenv()

app = Flask(__name__)

SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY')
SENDER_EMAIL = os.getenv('SENDER_EMAIL')

DATABASE = 'subscribers.db'

# Selenium Setup
chrome_options = Options()
chrome_options.add_argument("--headless")  # Run in headless mode (no UI)
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

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

def get_subscribers():
    """Retrieve all subscribed emails from the database."""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT email FROM subscribers")
    subscribers = [row[0] for row in cursor.fetchall()]
    conn.close()
    return subscribers

def wait_for_element(driver, by, value, timeout=10):
    """Wait for an element to be present on the page."""
    return WebDriverWait(driver, timeout).until(EC.presence_of_all_elements_located((by, value)))

def get_yahoo_finance_data():
    """Scrape latest finance news from Yahoo Finance using Selenium."""
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    url = 'https://finance.yahoo.com/'
    driver.get(url)
    
    finance_news = []
    try:
        articles = wait_for_element(driver, By.CSS_SELECTOR, "h3 a")
        for article in articles[:5]:  # Get top 5 news articles
            title = article.text.strip()
            link = article.get_attribute("href")
            if title and link:
                finance_news.append({'title': title, 'summary': 'No summary available.', 'link': link})
    except Exception as e:
        print(f"Error scraping Yahoo Finance: {e}")
    finally:
        driver.quit()

    return finance_news if finance_news else [{'title': 'No Finance news available.', 'summary': '', 'link': ''}]

def get_tech_news():
    """Scrape latest tech news from TechCrunch using Selenium."""
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    url = 'https://techcrunch.com/'
    driver.get(url)
    
    tech_news = []
    try:
        articles = wait_for_element(driver, By.CSS_SELECTOR, "div.post-block")
        for article in articles[:5]:  # Get top 5 news articles
            title_tag = article.find_element(By.CSS_SELECTOR, "a.post-block__title__link")
            summary_tag = article.find_element(By.CSS_SELECTOR, "div.post-block__content")
            title = title_tag.text.strip()
            summary = summary_tag.text.strip()
            link = title_tag.get_attribute("href")
            if title and link:
                tech_news.append({'title': title, 'summary': summary, 'link': link})
    except Exception as e:
        print(f"Error scraping TechCrunch: {e}")
    finally:
        driver.quit()

    return tech_news if tech_news else [{'title': 'No Tech news available.', 'summary': '', 'link': ''}]

def send_email(subject, content, to_email):
    """Send an email using SendGrid."""
    if not SENDGRID_API_KEY or not SENDER_EMAIL:
        print("SendGrid API key or sender email not configured.")
        return

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
    except Exception as e:
        print(f"Error sending email: {e}")

@app.route('/send_newsletter', methods=['GET'])
def send_newsletter():
    """Fetch news and send a newsletter to all subscribers."""
    finance_news = get_yahoo_finance_data()
    tech_news = get_tech_news()

    content = "<h1>Today's Finance & Tech News</h1><h2>Finance News</h2><ul>"
    
    if not finance_news or finance_news[0]['title'] == "No Finance news available.":
        content += "<p>No Finance news available today.</p>"
    else:
        content += "".join(f"<li><strong>{item['title']}</strong><br>{item['summary']}<br><a href='{item['link']}'>Read more</a></li>"
                           for item in finance_news)

    content += "</ul><h2>Tech News</h2><ul>"
    
    if not tech_news or tech_news[0]['title'] == "No Tech news available.":
        content += "<p>No Tech news available today.</p>"
    else:
        content += "".join(f"<li><strong>{item['title']}</strong><br>{item['summary']}<br><a href='{item['link']}'>Read more</a></li>"
                           for item in tech_news)

    content += "</ul>"

    subscribers = get_subscribers()
    
    if not subscribers:
        return jsonify({"message": "No subscribers found."}), 404

    for subscriber in subscribers:
        send_email("Daily Finance & Tech Newsletter", content, subscriber)

    return jsonify({"message": "Newsletter sent successfully!"})

@app.route('/subscribe', methods=['POST'])
def subscribe():
    """Allow users to subscribe to the newsletter."""
    email = request.json.get('email')
    
    if not email:
        return jsonify({"message": "Invalid email"}), 400

    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('INSERT OR IGNORE INTO subscribers (email) VALUES (?)', (email,))
        conn.commit()
        conn.close()
        
        return jsonify({"message": "Subscription successful!"})
    
    except sqlite3.Error as e:
        return jsonify({"message": f"Database error: {e}"}), 500


def job():
    """Scheduled job to send newsletter daily."""
    with app.test_client() as c:
        c.get('/send_newsletter')

schedule.every().day.at("11:05").do(job)

def run_scheduler():
    """Run the scheduler in the background."""
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == '__main__':
    print("Finance News:", get_yahoo_finance_data())
    print("Tech News:", get_tech_news())
# app.run(debug=True, use_reloader=False)