#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
DISCLAIMER:
This script is provided for educational purposes only. LinkedIn's terms of service prohibit
scraping or any form of automated data collection. Using this script to scrape LinkedIn's data
is against their terms of service and can result in your account being banned.
Use this script at your own risk. The author is not responsible for any misuse of this script.
"""

import time
import csv
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from bs4 import BeautifulSoup as bs

# ---------------------------------------------------------------------------------------
# Function to load cookies from a Netscape-format cookies.txt file into Selenium's browser
# ---------------------------------------------------------------------------------------
def load_cookies(browser, file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
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
                        'expiry': int(cookie['expiration']) if cookie['expiration'].isdigit() else None
                    })

# ---------------------------------------------------------------------------------------
# Helper function to convert abbreviated reaction/comment strings (e.g., "1K") to integers
# ---------------------------------------------------------------------------------------
def convert_abbreviated_to_number(s):
    s = s.upper().strip()
    if 'K' in s:
        return int(float(s.replace('K', '')) * 1000)
    elif 'M' in s:
        return int(float(s.replace('M', '')) * 1000000)
    else:
        # If it's just a normal number or empty, attempt to parse it
        try:
            return int(s)
        except ValueError:
            return 0

# ---------------------------------------------------------------------------------------
# Main script
# ---------------------------------------------------------------------------------------
def main():
    # --------------------------------
    # Customize these variables
    # --------------------------------
    user_profile_url = "https://www.linkedin.com/in/williamhgates/recent-activity/all/"  
    cookies_file = "your_linkedin_cookies.txt "  # Path to your cookies (Netscape format)
    csv_file = "user_posts_extended.csv"    # CSV output file
    MAX_POSTS = 20                          # Increase to get enough unique posts
    MAX_SCROLL_ATTEMPTS = 40               # Increase how many times we scroll
    MAX_NO_NEW_POSTS_IN_A_ROW = 3          # If we see 3 scrolls with no new posts, stop
    
    # --------------------------------
    # Set up Chrome (headless) driver
    # --------------------------------
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    
    print("[*] Initializing Chrome driver...")
    browser = webdriver.Chrome(options=chrome_options)
    
    print("[*] Setting window size...")
    browser.set_window_size(1920, 1080)
    
    # --------------------------------
    # Log in by loading cookies
    # --------------------------------
    print(f"[*] Going to LinkedIn home page and loading cookies from {cookies_file} ...")
    browser.get('https://www.linkedin.com/')
    time.sleep(2)
    
    # Load cookies
    load_cookies(browser, cookies_file)
    
    # Refresh to apply cookies
    browser.refresh()
    print("[*] Cookies loaded; refreshing page to apply them...")
    
    # Ensure page is loaded
    try:
        WebDriverWait(browser, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#global-nav"))
        )
        print("[*] Successfully logged in (navigation bar found).")
    except TimeoutException:
        print("[!] Navigation bar not found after applying cookies. Exiting.")
        browser.quit()
        return
    
    # --------------------------------
    # Navigate to the desired profile
    # --------------------------------
    print(f"[*] Navigating to {user_profile_url} ...")
    browser.get(user_profile_url)
    time.sleep(5)  # Let the page load
    
    # Prepare CSV
    print(f"[*] Creating CSV file: {csv_file}")
    with open(csv_file, mode='w', encoding='utf-8', newline='') as file:
        writer = csv.writer(file)
        # Write header row
        writer.writerow([
            "Post_ID",
            "Post_URL",
            "Post_Author_Name",
            "Post_Author_Profile",
            "Post_Author_JobTitle",
            "Post_Time",
            "Post_Content",
            "Post_Reactions",
            "Post_Comments",
            "Post_Impressions",
            "Date_Collected"
        ])
    
    # Use a set to track post IDs to avoid duplicates
    unique_post_ids = set()
    post_count = 0
    
    # Scroll parameters
    LOAD_PAUSE_TIME = 4
    scroll_attempts = 0
    no_new_posts_count = 0

    print("[*] Starting to scroll and collect post data...")
    while post_count < MAX_POSTS and scroll_attempts < MAX_SCROLL_ATTEMPTS and no_new_posts_count < MAX_NO_NEW_POSTS_IN_A_ROW:
        
        soup = bs(browser.page_source, "html.parser")
        
        # Each post is generally in an element: <div class="feed-shared-update-v2 ..."/>
        post_wrappers = soup.find_all("div", {"class": "feed-shared-update-v2"})
        
        new_posts_in_this_pass = 0  # track how many brand-new posts we discovered in this pass
        
        for pw in post_wrappers:
            # ---
            # 1) Post ID & Post URL
            # ---
            post_id = None
            post_url = None
            
            detail_link_tag = pw.find("a", {"class": "update-components-mini-update-v2__link-to-details-page"})
            if detail_link_tag and detail_link_tag.get("href"):
                post_url = detail_link_tag["href"].strip()
                if "urn:li:activity:" in post_url:
                    part = post_url.split("urn:li:activity:")[-1].replace("/", "")
                    post_id = part
            
            # Also check data-urn
            if not post_id:
                data_urn = pw.get("data-urn", "")
                if "urn:li:activity:" in data_urn:
                    post_id = data_urn.split("urn:li:activity:")[-1]
            
            # If we still can't find ID, skip
            if not post_id:
                continue
            
            # If we already have this post in our set, skip it
            if post_id in unique_post_ids:
                continue
            
            # Mark it as new
            unique_post_ids.add(post_id)
            new_posts_in_this_pass += 1

            # Convert relative URL to absolute
            if post_url and post_url.startswith("/feed/update/"):
                post_url = "https://www.linkedin.com" + post_url
            
            # ---
            # 2) Post Author name, profile link, job title, posted time
            # ---
            author_name = None
            author_profile_link = None
            author_jobtitle = None
            post_time = None
            
            actor_container = pw.find("div", {"class": "update-components-actor__container"})
            if actor_container:
                # Author name
                name_tag = actor_container.find("span", {"class": "update-components-actor__title"})
                if name_tag:
                    inner_span = name_tag.find("span", {"dir": "ltr"})
                    if inner_span:
                        author_name = inner_span.get_text(strip=True)
                
                # Profile link
                actor_link = actor_container.find("a", {"class": "update-components-actor__meta-link"})
                if actor_link and actor_link.get("href"):
                    author_profile_link = actor_link["href"].strip()
                    if author_profile_link.startswith("/in/"):
                        author_profile_link = "https://www.linkedin.com" + author_profile_link
                
                # Job title
                jobtitle_tag = actor_container.find("span", {"class": "update-components-actor__description"})
                if jobtitle_tag:
                    author_jobtitle = jobtitle_tag.get_text(strip=True)
                
                # Time posted
                time_tag = actor_container.find("span", {"class": "update-components-actor__sub-description"})
                if time_tag:
                    post_time = time_tag.get_text(strip=True)
            
            # ---
            # 3) Post content
            # ---
            post_content = None
            content_div = pw.find("div", {"class": "update-components-text"})
            if content_div:
                post_content = content_div.get_text(separator="\n", strip=True)
            
            # ---
            # 4) Reactions, Comments, Impressions
            # ---
            post_reactions = 0
            post_comments = 0
            post_impressions = 0
            
            social_counts_div = pw.find("div", {"class": "social-details-social-counts"})
            if social_counts_div:
                # Reactions
                reaction_item = social_counts_div.find("li", {"class": "social-details-social-counts__reactions"})
                if reaction_item:
                    button_tag = reaction_item.find("button")
                    if button_tag and button_tag.has_attr("aria-label"):
                        raw_reactions = button_tag["aria-label"].split(" ")[0]
                        post_reactions = convert_abbreviated_to_number(raw_reactions)
                
                # Comments
                comment_item = social_counts_div.find("li", {"class": "social-details-social-counts__comments"})
                if comment_item:
                    cbutton_tag = comment_item.find("button")
                    if cbutton_tag and cbutton_tag.has_attr("aria-label"):
                        raw_comments = cbutton_tag["aria-label"].split(" ")[0]
                        post_comments = convert_abbreviated_to_number(raw_comments)
            
            # Impressions
            impressions_span = pw.find("span", {"class": "analytics-entry-point"})
            if impressions_span:
                possible_text = impressions_span.get_text(strip=True)
                if "impressions" in possible_text.lower():
                    raw_impressions = possible_text.lower().replace("impressions", "").strip()
                    raw_impressions = raw_impressions.split(" ")[0]
                    post_impressions = convert_abbreviated_to_number(raw_impressions)
            
            date_collected = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            
            # Print for debugging
            print(f"[+] Found new Post ID {post_id}. So far we have {post_count + 1} unique posts.")
            print(f"    URL: {post_url}")
            print(f"    Author: {author_name} | {author_profile_link}")
            print(f"    Content snippet: {post_content[:70]}{'...' if len(post_content or '')>70 else ''}")
            
            # Write to CSV
            with open(csv_file, mode='a', encoding='utf-8', newline='') as file:
                writer = csv.writer(file)
                writer.writerow([
                    post_id or "",
                    post_url or "",
                    author_name or "",
                    author_profile_link or "",
                    author_jobtitle or "",
                    post_time or "",
                    post_content or "",
                    post_reactions,
                    post_comments,
                    post_impressions,
                    date_collected
                ])
            
            # Increase final count
            post_count += 1
            if post_count >= MAX_POSTS:
                break
        
        # If we found no new posts in this pass, increment no_new_posts_count
        # otherwise reset it
        if new_posts_in_this_pass == 0:
            no_new_posts_count += 1
        else:
            no_new_posts_count = 0
        
        # Scroll further only if we haven't reached MAX_POSTS
        if post_count < MAX_POSTS:
            print("[*] Scrolling to load more posts...")
            browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(LOAD_PAUSE_TIME)
            scroll_attempts += 1
    
    print(f"[*] Finished after collecting {post_count} unique posts.")
    print("[*] Closing browser.")
    browser.quit()
    print(f"[*] Data saved to {csv_file}")

# ---------------------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------------------
if __name__ == "__main__":
    main()