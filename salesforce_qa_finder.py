import requests
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import streamlit as st
import pandas as pd
import re
import time
import feedparser
from fuzzywuzzy import fuzz
from googleapiclient.discovery import build
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import logging
 
# Logging Setup
logging.basicConfig(filename="logs.txt", level=logging.ERROR, format="%(asctime)s - %(levelname)s - %(message)s")
 
# Google Custom Search API Setup
GOOGLE_API_KEYS = ["YOUR_GOOGLE_API_KEY1", "YOUR_GOOGLE_API_KEY2"]  # Multiple API Keys for Quota Handling
SEARCH_ENGINE_ID = "YOUR_SEARCH_ENGINE_ID"
current_api_key_index = 0  # To switch between API Keys
 
# AI-Powered Job Search Queries
search_queries = [
    "Salesforce QA Engineer Pune OR Remote",
    "Salesforce Tester Pune OR Remote",
    "Salesforce Automation Tester Pune OR Remote",
    "Salesforce Test Engineer Pune OR Remote",
    "Salesforce UAT Tester Pune OR Remote",
    "Salesforce API Tester Pune OR Remote",
    "Provar Salesforce QA Pune OR Remote",
    "Selenium with Salesforce Testing Pune OR Remote"
]
 
# Function 1: Google Custom Search API with Pagination
async def google_search(num_results=10, max_results=50):
    global current_api_key_index
    jobs = []
    start_index = 1
 
    while len(jobs) < max_results:
        try:
            service = build("customsearch", "v1", developerKey=GOOGLE_API_KEYS[current_api_key_index])
            result = service.cse().list(q=" OR ".join(search_queries), cx=SEARCH_ENGINE_ID, num=num_results, start=start_index).execute()
            if "items" in result:
                for item in result["items"]:
                    title = item["title"]
                    link = item["link"]
                    exp = extract_experience(title)
 
                    if any(word in title.lower() for word in ["pune", "remote", "hybrid"]):
                        jobs.append({"title": title, "link": link, "experience": exp, "source": "Google API"})
 
            start_index += num_results  # Move to the next page
 
        except Exception as e:
            logging.error(f"Google API Error: {e}")
            current_api_key_index = (current_api_key_index + 1) % len(GOOGLE_API_KEYS)
            continue  # Try next API Key
 
    return jobs
 
# Function 2: Async Web Scraping (Indeed Jobs for Pune & Remote)
async def scrape_indeed_jobs():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
 
driver.get("https://www.indeed.com/jobs?q=Salesforce+QA&l=Pune&remotejob=remote")
# Function 2: Async Web Scraping (Indeed Jobs for Pune & Remote)
async def scrape_indeed_jobs():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    driver.get("https://www.indeed.com/jobs?q=Salesforce+QA&l=Pune&remotejob=remote")

    jobs = []
    try:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "job_seen_beacon")))

        job_cards = driver.find_elements(By.CLASS_NAME, "job_seen_beacon")

        for job in job_cards[:20]:  # Get more results
            title = job.find_element(By.TAG_NAME, "h2").text
            link = job.find_element(By.TAG_NAME, "a").get_attribute("href")
            exp = extract_experience(title)

            if any(word in title.lower() for word in ["pune", "remote", "hybrid"]):
                jobs.append({"title": title, "link": link, "experience": exp, "source": "Indeed"})

    except Exception as e:
        logging.error(f"Error scraping Indeed: {e}")

    driver.quit()
    return jobs

 
# AI Scam Detection (No Fake Jobs)
def is_real_job(job_title):
    scam_keywords = ["easy money", "work from home", "no experience required", "daily payment"]
    return not any(keyword.lower() in job_title.lower() for keyword in scam_keywords)
 
# AI Duplicate Removal
def remove_duplicates(jobs):
    unique_jobs = []
    for job in jobs:
        if not any(fuzz.ratio(job["title"], seen_job["title"]) > 90 for seen_job in unique_jobs):
            unique_jobs.append(job)
    return unique_jobs
 
# Extract Experience from Job Title & Description
def extract_experience(title):
    match = re.search(r'(\d+)[+-]?\s*(?:years?|yrs?|y)', title, re.IGNORECASE)
return int(match.group(1)) if match else 0  
 
# Run Job Searches Asynchronously
async def fetch_all_jobs():
    google_jobs, indeed_jobs = await asyncio.gather(google_search(num_results=10, max_results=50), scrape_indeed_jobs())
    return google_jobs + indeed_jobs
 
# Streamlit UI
async def main():
    st.title("🚀 AI-Powered Salesforce QA Job Finder (Ultra-Fast, 100% Free)")
    st.write("Find the best Salesforce QA jobs in Pune (Hybrid/Onsite) or 100% Remote with AI Matching!")
 
    with st.spinner("Fetching jobs... Please wait."):
        all_jobs = await fetch_all_jobs()
 
    # Apply AI Filtering
    filtered_jobs = [job for job in all_jobs if is_real_job(job["title"])]
    unique_jobs = remove_duplicates(filtered_jobs)
    sorted_jobs = sorted(unique_jobs, key=lambda x: x["experience"])
 
    # Experience Filter
    experience_filter = st.slider("Minimum Experience", min_value=0, max_value=10, value=2)
    filtered_jobs_by_experience = [job for job in sorted_jobs if job["experience"] >= experience_filter]
 
    # Display Results
    if filtered_jobs_by_experience:
        df = pd.DataFrame(filtered_jobs_by_experience)
        st.write("### 🔍 Latest Jobs (Sorted by Experience & No Fake Jobs):")
        st.table(df)
 
        st.write("### 🌐 Click to Apply:")
        for job in filtered_jobs_by_experience:
            st.write(f"**[{job['title']} ({job['experience']} years)]({job['link']})** - 🏢 *{job['source']}*")
    else:
        st.warning("No jobs found! Try adjusting your filters or searching again later.")
 
if __name__ == "__main__":
    asyncio.run(main())  # Indented under the if statement
