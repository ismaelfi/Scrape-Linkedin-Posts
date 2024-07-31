# Linkedin Post Scraper 

## DISCLAIMER

This script is provided for educational purposes only. LinkedIn's terms of service prohibit scraping or any form of automated data collection.
Using this script to scrape LinkedIn's data is against their terms of service and can result in your account being banned.
Use this script at your own risk. The author is not responsible for any misuse of this script.

## Overview

This script uses Selenium and BeautifulSoup to scrape the latest posts from a specified LinkedIn user's activity page.
It extracts the content, reactions, and comments from each post and saves the data to a CSV file.

## Requirements

To run this script, you need to install the following Python packages and tools:
- Selenium: For web browser automation.
- BeautifulSoup: For parsing HTML and extracting data.
- Pandas: For data manipulation and exporting to CSV.
- ChromeDriver: The WebDriver for Google Chrome.
- Google Chrome Browser: The actual browser used by ChromeDriver.

## Installation Guide

### Step 1: Install Python Packages
You can install the required Python packages using pip. Run the following command in your terminal:
 ```sh
 pip install selenium beautifulsoup4 pandas
 ```

### Step 2: Install Google Chrome
Download and install Google Chrome from the official website.

### Step 3: Install ChromeDriver
Download ChromeDriver: Go to the ChromeDriver download page and download the version that matches your installed version of Chrome.
Install ChromeDriver:
Windows: Extract the downloaded file and place chromedriver.exe in a directory that's included in your system's PATH, or specify the path in your script.
macOS and Linux: Extract the downloaded file and place chromedriver in a directory that's included in your system's PATH, or specify the path in your script.

### Step 4: Create the Cookies File
Create a file named your_linkedin_cookies.txt in the same directory as the script.
This file should contain your LinkedIn cookies in Netscape format.
You can use browser extensions like "EditThisCookie" to export cookies from your LinkedIn session.
