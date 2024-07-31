"""
DISCLAIMER:
This script is provided for educational purposes only. LinkedIn's terms of service prohibit scraping or any form of automated data collection.
Using this script to scrape LinkedIn's data is against their terms of service and can result in your account being banned.
Use this script at your own risk. The author is not responsible for any misuse of this script.
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from bs4 import BeautifulSoup as bs
import csv

# Function to load cookies from a Netscape format cookies.txt file
def load_cookies(browser, file_path):
    with open(file_path, 'r') as file:
        for line in file:
            if not line.startswith('#') and line.strip():
                fields = line.strip().split('\t')
                if len(fields) == 7:
                    cookie = {
                        'domain': fields[0],
                        'flag': fields[1],
                        'path': fields[2],
                        'secure': fields[3],
                        'expiration': fields[4],
                        'name': fields[5],
                        'value': fields[6]
                    }
                    browser.add_cookie({
                        'name': cookie['name'],
                        'value': cookie['value'],
                        'domain': cookie['domain'],
                        'path': cookie['path'],
                        'expiry': int(cookie['expiration']) if cookie['expiration'] else None
                    })

# Initialize Chrome options
chrome_options = Options()
chrome_options.add_argument('--headless')  # Run in headless mode
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')

# Initialize the Chrome driver
print("Initializing the Chrome driver...")
browser = webdriver.Chrome(options=chrome_options)

# Set the window size
browser.set_window_size(1920, 1080)

# Open LinkedIn login page
print("Opening LinkedIn login page...")
browser.get('https://www.linkedin.com/')

# Load cookies from the file
print("Loading cookies...")
load_cookies(browser, 'your_linkedin_cookies.txt')  # Change the path to your cookies file if necessary

# Refresh the page to apply cookies
browser.refresh()

# Wait for the main navigation bar to be visible
print("Waiting for the main navigation bar after applying cookies...")
try:
    WebDriverWait(browser, 30).until(EC.presence_of_element_located((By.CSS_SELECTOR, '#global-nav .global-nav__me')))
    print("Navigation bar found. Proceeding with scraping...")
except TimeoutException:
    print("TimeoutException: Navigation bar not found after applying cookies. Check if the cookies are correct.")

# Set LinkedIn page URL for scraping
user_profile_url = 'https://www.linkedin.com/in/emmanuelmacron/recent-activity/all/'  # Change to the desired profile URL

# Navigate to the user's recent activity page
print(f"Navigating to the user's recent activity page: {user_profile_url}...")
browser.get(user_profile_url)

# Wait for the page to load completely
print("Waiting for the user's recent activity page to load completely...")
time.sleep(5)

# Set parameters for scrolling through the page
SCROLL_PAUSE_TIME = 2  # Time to pause between scrolls
LOAD_PAUSE_TIME = 10  # Time to wait after scrolling to load new posts
MAX_POSTS = 50  # Number of posts to load
SCROLL_THRESHOLD = 5  # Number of posts to load before scrolling

# Scroll through the page until the required number of posts are loaded
print("Scrolling through the page to load all content...")
posts_data = []
post_count = 0

csv_file = "user_posts.csv"  # Name of the CSV file to save data

# Create the CSV file with headers
with open(csv_file, mode='w', encoding='utf-8', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['Content', 'Reactions', 'Comments'])

while post_count < MAX_POSTS:
    # Parse the page source with BeautifulSoup
    user_page = browser.page_source
    linkedin_soup = bs(user_page.encode("utf-8"), "html.parser")

    # Extract post containers from the HTML
    containers = linkedin_soup.find_all("div", {"class": "social-details-social-counts"})

    # Helper functions for reaction conversions
    def convert_abbreviated_to_number(s):
        if 'K' in s:
            return int(float(s.replace('K', '')) * 1000)
        elif 'M' in s:
            return int(float(s.replace('M', '')) * 1000000)
        else:
            return int(s)

    # Main loop to process each container
    print("Processing each container to extract post data...")
    for container in containers:
        if post_count >= MAX_POSTS:
            break

        try:
            post_content_container = container.find_previous("div", {"class": "update-components-text"})
            post_content = post_content_container.text.strip() if post_content_container else "No content"
        except Exception as e:
            print(e)
            post_content = "No content"

        try:
            post_reactions = container.find("li", {"class": "social-details-social-counts__reactions"}).find("button")["aria-label"].split(" ")[0].replace(',', '')
        except:
            post_reactions = "0"
        try:
            post_comments = container.find("li", {"class": "social-details-social-counts__comments"}).find("button")["aria-label"].split(" ")[0].replace(',', '')
        except:
            post_comments = "0"

        # Convert reactions and comments to numeric values
        post_reactions_numeric = convert_abbreviated_to_number(post_reactions)
        post_comments_numeric = convert_abbreviated_to_number(post_comments)

        posts_data.append({
            'Content': post_content,
            'Reactions': post_reactions_numeric,
            'Comments': post_comments_numeric,
        })

        post_count += 1
        print(f"Post {post_count} saved.")

        # Save the post data to the CSV file immediately
        with open(csv_file, mode='a', encoding='utf-8', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([post_content, post_reactions_numeric, post_comments_numeric])

    # Scroll down to load more posts
    print("Scrolling down to load more posts...")
    browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(LOAD_PAUSE_TIME)

print("Finished scrolling and processing posts.")

# Close the browser
browser.quit()

print(f"Data exported to {csv_file}")
