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

def initialize_driver():
    """Initialize the Selenium WebDriver."""
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  # Run in headless mode (no GUI)
    driver = webdriver.Chrome(options=options)
    return driver

def get_finance_news(driver):
    """Scrape finance news from CNBC."""
    try:
        print("Navigating to the finance news page...")
        driver.get('https://www.cnbc.com/finance/')
        
        # Wait for the page to load and find the news elements
        wait = WebDriverWait(driver, 10)
        print("Waiting for news elements...")
        news_elements = wait.until(EC.presence_of_all_elements_located((By.TAG_NAME, 'a')))
        
        print("Extracting news...")
        news = []
        for element in news_elements:
            title = element.text.strip()
            link = element.get_attribute('href')
            if title:
                news.append({'title': title, 'link': link})
        
        print(f"Found {len(news)} finance news articles.")
        return news
    except Exception as e:
        print(f"Error scraping CNBC Finance: {e}")
        return []

def get_tech_news(driver):
    """Scrape tech news from The Verge."""
    try:
        print("Navigating to the tech news page...")
        driver.get('https://www.theverge.com/')
        
        # Wait for the page to load and find the news elements
        wait = WebDriverWait(driver, 10)
        print("Waiting for tech news elements...")
        news_elements = wait.until(EC.presence_of_all_elements_located((By.TAG_NAME, 'a')))
        
        print("Extracting tech news...")
        news = []
        for element in news_elements:
            title = element.text.strip()
            link = element.get_attribute('href')
            if title:
                news.append({'title': title, 'link': link})
        
        print(f"Found {len(news)} tech news articles.")
        return news
    except Exception as e:
        print(f"Error scraping The Verge: {e}")
        return []
    

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
@app.route('/send_newsletter', methods=['GET'])
def send_newsletter():
    """Fetch news and send a newsletter to all subscribers."""
    driver = initialize_driver()  # Initialize the driver here

    # Fetch finance news and tech news
    finance_news = get_finance_news(driver)
    tech_news = get_tech_news(driver)

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

    # Quit the driver after the newsletter is sent
    driver.quit()

    return jsonify({"message": "Newsletter sent successfully!"})


schedule.every().day.at("11:29").do(send_newsletter)

def run_scheduler():
    """Run the scheduler in the background."""
    while True:
        schedule.run_pending()
        time.sleep(60)

def main():
    # Initialize the driver
    driver = initialize_driver()

    # Scrape finance news
    print("Fetching finance news...")
    finance_news = get_finance_news(driver)
    print("Finance News:", finance_news)

    # Scrape tech news
    print("Fetching tech news...")
    tech_news = get_tech_news(driver)
    print("Tech News:", tech_news)

    # Close the driver after use
    driver.quit()

if __name__ == '__main__':
    # Initialize the database
    init_db()
    main()
