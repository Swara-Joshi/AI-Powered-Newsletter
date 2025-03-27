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
# import ssl

# Disable SSL verification (for testing purposes only, not recommended for production)
# ssl._create_default_https_context = ssl._create_unverified_context

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

def add_subscriber(email):
    """Add a new subscriber to the database."""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO subscribers (email) VALUES (?)", (email,))
        conn.commit()
    except sqlite3.IntegrityError:
        pass  # Email already exists in the database, ignore this error
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

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options

def initialize_driver():
    chrome_options = Options()
    # Add any options you need here, for example:
    chrome_options.add_argument('--headless')  # If you want to run in headless mode

    # Create the service object and pass it to the driver
    service = Service(ChromeDriverManager().install())

    # Initialize the driver with the service object and options
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver



def get_finance_news(driver):
    """Scrape finance news from CNBC with retry logic and get summaries. Only returns the top 5 news."""
    try:
        print("Navigating to the finance news page...")
        driver.get('https://www.cnbc.com/finance/')

        # Wait for the page to load and find the news elements
        wait = WebDriverWait(driver, 10)
        print("Waiting for news elements...")
        news_elements = wait.until(EC.presence_of_all_elements_located((By.TAG_NAME, 'a')))
        
        # Extract news with retry for stale element reference error
        print("Extracting news...")
        news = []
        for _ in range(3):  # Retry up to 3 times
            try:
                for element in news_elements:
                    title = element.text.strip()
                    link = element.get_attribute('href')
                    if title:
                        # Now fetch the summary from the article page
                        article_summary = get_article_summary(link)
                        news.append({'title': title, 'summary': article_summary, 'link': link})
                    if len(news) >= 5:  # Limit to 5 articles
                        break
                break  # Exit if no error occurs
            except Exception as e:
                print(f"Error while extracting: {e}")
                news_elements = wait.until(EC.presence_of_all_elements_located((By.TAG_NAME, 'a')))  # Re-fetch elements
        
        if not news:
            print("No finance news found.")
        return news[:5]  # Return only the first 5 news articles
    except Exception as e:
        print(f"Error scraping CNBC Finance: {e}")
        return []


def get_article_summary(article_url):
    """Fetch the first paragraph of the article as a summary."""
    try:
        print(f"Fetching article summary from: {article_url}")
        # Send a GET request to the article page
        response = requests.get(article_url)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find the first paragraph or content block to extract summary
        paragraph = soup.find('p')
        if paragraph:
            return paragraph.get_text().strip()
        return "Summary not available"
    except Exception as e:
        print(f"Error fetching summary for {article_url}: {e}")
        return "Summary not available"

def get_tech_news(driver):
    """Scrape tech news from The Verge and return top 5 latest from the last 24 hours with summaries."""
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
            
            # Check if link and title exist
            if title and link:
                # Now fetch the summary from the article page
                article_summary = get_article_summary(link)
                news.append({'title': title, 'summary': article_summary, 'link': link})
        
        # Only return the top 5 news items
        top_news = news[:5]

        print(f"Found {len(top_news)} tech news articles (top 5).")
        return top_news
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
    with app.app_context():
        """Fetch news and send a newsletter to all subscribers."""
        driver = initialize_driver()  # Initialize the driver here

        # Fetch finance news and tech news
        finance_news = get_finance_news(driver)
        tech_news = get_tech_news(driver)

        content = "<h1>Today's Finance & Tech News</h1><h2>Finance News</h2><ul>"
        
        if not finance_news or finance_news[0]['title'] == "No Finance news available.":
            content += "<p>No Finance news available today.</p>"
        else:
            content += "".join(f"<li><strong>{item['title']}</strong><br><a href='{item['link']}'>Read more</a></li>"
                            for item in finance_news)

        content += "</ul><h2>Tech News</h2><ul>"
        
        if not tech_news or tech_news[0]['title'] == "No Tech news available.":
            content += "<p>No Tech news available today.</p>"
        else:
            content += "".join(f"<li><strong>{item['title']}</strong><br><i>{item['summary']}</i><br><a href='{item['link']}'>Read more</a></li>"
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

# Schedule the newsletter to be sent daily at 11:48
schedule.every().day.at("18:59").do(send_newsletter)

def run_scheduler():
    schedule.every(1).minute.do(send_newsletter)  # Run the job every minute
    while True:
        schedule.run_pending()
        time.sleep(1)

# Start the scheduler in a separate thread
def start_background_scheduler():
    thread = Thread(target=run_scheduler)
    thread.start()

if __name__ == "__main__":
    init_db()  # Ensure database is initialized
    start_background_scheduler()
    app.run(debug=True)
