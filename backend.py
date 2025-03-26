import os
import sqlite3
import requests
from flask import Flask, jsonify, request
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from bs4 import BeautifulSoup
import schedule
import time
from dotenv import load_dotenv
from threading import Thread

# Load environment variables from .env file
load_dotenv()

app = Flask(_name_)

# Load environment variables
SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY')
SENDER_EMAIL = os.getenv('SENDER_EMAIL')

# SQLite database setup
DATABASE = 'subscribers.db'

# Initialize the database
def init_db():
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

# Web scraping function to get Finance news from Yahoo Finance
def get_yahoo_finance_data():
    url = 'https://finance.yahoo.com/'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    news_items = []
    for item in soup.find_all('li', {'class': 'js-stream-content'}):
        title = item.find('h3')
        summary = item.find('p')
        link = item.find('a', {'href': True})

        if title and summary and link:
            news_items.append({
                'title': title.get_text(),
                'summary': summary.get_text() if summary else 'No summary available.',
                'link': 'https://finance.yahoo.com' + link['href']
            })

    return news_items

# Web scraping function to get Tech news from TechCrunch
def get_tech_news():
    url = 'https://techcrunch.com/'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    tech_news_items = []
    for item in soup.find_all('div', {'class': 'post-block'}):
        title = item.find('a', {'class': 'post-block_title_link'})
        summary = item.find('div', {'class': 'post-block__content'})
        link = title['href'] if title else None

        if title and summary and link:
            tech_news_items.append({
                'title': title.get_text(),
                'summary': summary.get_text() if summary else 'No summary available.',
                'link': link
            })

    return tech_news_items

# Send email function using SendGrid
def send_email(subject, content, to_emails):
    message = Mail(
        from_email=SENDER_EMAIL,
        to_emails=to_emails,
        subject=subject,
        html_content=content
    )

    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        print(f"Email sent to {to_emails}. Status code: {response.status_code}")
    except Exception as e:
        print(f"An error occurred: {e}")

# Route to send a newsletter
@app.route('/send_newsletter', methods=['GET'])
def send_newsletter():
    # Get both Finance and Tech News
    finance_news = get_yahoo_finance_data()
    tech_news = get_tech_news()

    # Combine both Finance and Tech news
    content = "<h1>Today's News: Finance & Tech</h1><h2>Finance News</h2><ul>"
    for item in finance_news:
        content += f"<li><strong>{item['title']}</strong><br>{item['summary']}<br><a href='{item['link']}'>Read more</a></li>"
    content += "</ul><h2>Tech News</h2><ul>"
    for item in tech_news:
        content += f"<li><strong>{item['title']}</strong><br>{item['summary']}<br><a href='{item['link']}'>Read more</a></li>"
    content += "</ul>"

    # Fetch all subscribers from the database
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT email FROM subscribers')
    subscribers = cursor.fetchall()
    conn.close()

    # Send the email to all subscribers
    for subscriber in subscribers:
        send_email("Daily Finance & Tech Newsletter", content, subscriber[0])

    return jsonify({"message": "Newsletter sent!"})

# Route to subscribe to the newsletter
@app.route('/subscribe', methods=['POST'])
def subscribe():
    email = request.json.get('email')

    if email:
        # Insert the email into the database
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('INSERT OR IGNORE INTO subscribers (email) VALUES (?)', (email,))
        conn.commit()
        conn.close()
        return jsonify({"message": "Subscribed"})
    else:
        return jsonify({"message": "Invalid email"}), 400

# Scheduler job to send newsletter every day at 8 AM
def job():
    with app.test_client() as c:
        c.get('/send_newsletter')  # Trigger the newsletter

# Schedule the job every day at 1:40 AM
schedule.every().day.at("02:05").do(job)

# Background scheduler to run the task
def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(60)  # Sleep for 1 minute

if _name_ == '_main_':
    # Initialize the database
    init_db()

    # Run the scheduler in a separate thread
    scheduler_thread = Thread(target=run_scheduler)
    scheduler_thread.start()

    # Run Flask app
    app.run(debug=True)