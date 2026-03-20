import streamlit as st
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from bs4 import BeautifulSoup
import urllib.parse
import time
import pandas as pd
import io
from PIL import Image

# --- 1. Page Config ---
st.set_page_config(page_title="Job Search AI", page_icon="💼", layout="wide")

# --- 2. Driver Initialization (Microsoft Edge) ---
@st.cache_resource
def get_driver():
    options = Options()
    # Ensure the browser is visible for manual login
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    
    # Automatically manages the EdgeDriver
    service = Service(EdgeChromiumDriverManager().install())
    return webdriver.Edge(service=service, options=options)

# --- 3. UI Header ---
st.title("💼 Job Search AI (Edge Mode)")
st.markdown("### Search LinkedIn Hiring Feeds using Microsoft Edge")

# --- 4. Sidebar ---
with st.sidebar:
    st.header("Search Settings")
    job_criteria = st.text_input("Job Search Criteria", placeholder="e.g. Senior QA Engineer")
    st.info("Log in manually in the Edge window that opens.")

# --- 5. Application Logic ---
if "step" not in st.session_state:
    st.session_state.step = "init"

# STEP 1: LOGIN
if st.session_state.step == "init":
    if st.button("🔗 Open Edge to Login"):
        try:
            driver = get_driver()
            driver.get("https://www.linkedin.com/login")
            st.session_state.step = "login_wait"
            st.rerun()
        except Exception as e:
            st.error(f"Could not launch Edge: {e}")

# STEP 2: SEARCH
if st.session_state.step == "login_wait":
    st.warning("Log in to LinkedIn in the Edge window. Once you see your feed, click below.")
    if st.button("✅ I am Logged In - Start Search"):
        if not job_criteria:
            st.error("Please enter search criteria in the sidebar!")
        else:
            st.session_state.step = "searching"
            st.rerun()

if st.session_state.step == "searching":
    driver = get_driver()
    
    # Construct URL for last 24 hours
    query = f'"Hiring" AND "@" AND "{job_criteria}"'
    encoded_query = urllib.parse.quote(query)
    search_url = f"https://www.linkedin.com/search/results/content/?keywords={encoded_query}&sortBy=%22date_posted%22"
    
    with st.spinner("Extracting posts from the last 24 hours..."):
        try:
            driver.get(search_url)
            time.sleep(5) # Let content load

            # Capture a screenshot for the UI
            png = driver.get_screenshot_as_png()
            st.image(Image.open(io.BytesIO(png)), caption="Current Search View")

            soup = BeautifulSoup(driver.page_source, "html.parser")
            posts = soup.find_all('div', {'class': 'update-components-text'})

            results = []
            for post in posts:
                text = post.get_text(separator=" ").strip()
                results.append({"Post Content": text})

            if results:
                st.success(f"Found {len(results)} posts!")
                st.table(pd.DataFrame(results))
            else:
                st.warning("No posts found. Try scrolling the Edge window and clicking search again.")
                
        except Exception as e:
            st.error(f"Search failed: {e}")

    if st.button("🔄 New Search"):
        st.session_state.step = "login_wait"
        st.rerun()
