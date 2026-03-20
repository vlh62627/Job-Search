import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import urllib.parse
import time
import pandas as pd

# --- 1. Page Configuration & Styling ---
st.set_page_config(page_title="Job Search", page_icon="💼", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #0077b5; color: white; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. Header ---
st.title("💼 Job Search AI")
st.markdown("### Your automated assistant for LinkedIn hiring feeds")
st.divider()

# --- 3. Sidebar Configuration ---
with st.sidebar:
    st.header("Search Settings")
    job_criteria = st.text_input("Job Search Criteria", placeholder="e.g. Java Developer")
    st.info("Log in to LinkedIn in the browser window that opens before starting the search.")

# --- 4. Driver Initialization ---
@st.cache_resource
def get_driver():
    options = Options()
    # We do NOT use headless mode so the user can see the login screen
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    return webdriver.Chrome(options=options)

# --- 5. Main Logic ---
if "step" not in st.session_state:
    st.session_state.step = "init"

# Step 1: Login Request
if st.session_state.step == "init":
    st.subheader("Step 1: Authenticate")
    if st.button("🔗 Open LinkedIn to Login"):
        driver = get_driver()
        driver.get("https://www.linkedin.com/login")
        st.session_state.step = "login_wait"
        st.rerun()

# Step 2: Confirm Login
if st.session_state.step == "login_wait":
    st.warning("Please log in to your LinkedIn account in the browser window. Once you see your home feed, click the button below.")
    if st.button("✅ I am Logged In - Start Search"):
        if not job_criteria:
            st.error("Please provide job search criteria in the sidebar first!")
        else:
            st.session_state.step = "searching"
            st.rerun()

# Step 3: Search and Display
if st.session_state.step == "searching":
    driver = get_driver()
    st.info(f"Searching for: 'Hiring' AND '@' AND '{job_criteria}'")
    
    # Construct URL with "Past 24 Hours" filter (f_TPR=r86400)
    query = f'"Hiring" AND "@" AND "{job_criteria}"'
    encoded_query = urllib.parse.quote(query)
    search_url = f"https://www.linkedin.com/search/results/content/?keywords={encoded_query}&origin=FACETED_SEARCH&refresh=true&sortBy=%22date_posted%22"
    
    try:
        driver.get(search_url)
        time.sleep(5) # Wait for posts to load

        soup = BeautifulSoup(driver.page_source, "html.parser")
        # LinkedIn post text usually resides in these classes
        post_containers = soup.find_all('div', {'class': 'update-components-text'})

        results = []
        for post in post_containers:
            text = post.get_text(separator=" ").strip()
            # Basic validation that it's a "Hiring" post
            if "hiring" in text.lower() or "@" in text:
                results.append({"Post Content": text})

        if results:
            st.success(f"Found {len(results)} matching posts from the last 24 hours!")
            df = pd.DataFrame(results)
            st.table(df)
        else:
            st.warning("No matching posts found. Try scrolling the browser window to load more and click search again.")
            
    except Exception as e:
        st.error(f"An error occurred: {e}")

    if st.button("🔄 Start New Search"):
        st.session_state.step = "login_wait"
        st.rerun()
