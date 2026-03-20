import streamlit as st
import pandas as pd
import time
import io
import os
import urllib.parse
from PIL import Image
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options

# --- 1. Page Config ---
st.set_page_config(page_title="Job Search AI", page_icon="💼", layout="wide")

# --- 2. Offline-Ready Driver Initialization ---
@st.cache_resource
def get_driver():
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    
    # Path to the driver you manually downloaded
    # Ensure 'msedgedriver.exe' is in the same folder as this script
    driver_path = os.path.join(os.getcwd(), "msedgedriver.exe")
    
    if not os.path.exists(driver_path):
        st.error(f"🚨 msedgedriver.exe not found at {driver_path}")
        st.info("Please download it from Microsoft's website and place it in the project folder.")
        st.stop()

    service = Service(executable_path=driver_path)
    return webdriver.Edge(service=service, options=options)

# --- 3. Custom CSS & Header ---
st.markdown("""
    <style>
    .stButton>button { width: 100%; background-color: #0078d4; color: white; font-weight: bold; }
    [data-testid="stAppViewContainer"] { background-color: #f3f2f1; }
    </style>
    """, unsafe_allow_html=True)

st.title("💼 Job Search AI (Offline-Ready Edge)")
st.markdown("---")

# --- 4. Sidebar ---
with st.sidebar:
    st.header("Search Settings")
    job_criteria = st.text_input("Job Search Criteria", placeholder="e.g. Software Engineer")
    st.markdown("---")
    st.write("**How to use:**")
    st.write("1. Open Edge and Login.")
    st.write("2. Once you see your feed, return here.")

# --- 5. Application Logic ---
if "step" not in st.session_state:
    st.session_state.step = "init"

# STEP 1: LOGIN (Manual)
if st.session_state.step == "init":
    st.subheader("Step 1: Authenticate")
    if st.button("🔗 Launch Microsoft Edge"):
        try:
            driver = get_driver()
            driver.get("https://www.linkedin.com/login")
            st.session_state.step = "login_wait"
            st.rerun()
        except Exception as e:
            st.error(f"Failed to launch: {e}")

# STEP 2: CONFIRMATION
if st.session_state.step == "login_wait":
    st.info("⚠️ Please log in to LinkedIn in the browser window. Do not close the window!")
    if st.button("✅ I'm Logged In - Start Search"):
        if not job_criteria:
            st.warning("Please enter job criteria in the sidebar.")
        else:
            st.session_state.step = "searching"
            st.rerun()

# STEP 3: SEARCHING
if st.session_state.step == "searching":
    driver = get_driver()
    
    # Target: Last 24 Hours via 'date_posted' sort
    query = f'"Hiring" AND "@" AND "{job_criteria}"'
    encoded_query = urllib.parse.quote(query)
    search_url = f"https://www.linkedin.com/search/results/content/?keywords={encoded_query}&sortBy=%22date_posted%22"
    
    with st.spinner("Scanning feed for the last 24 hours..."):
        try:
            driver.get(search_url)
            time.sleep(6) # Sufficient time for dynamic content loading

            # Visual confirmation for the user
            screenshot_png = driver.get_screenshot_as_png()
            st.image(Image.open(io.BytesIO(screenshot_png)), caption="Last Automated Action")

            # Parse HTML
            soup = BeautifulSoup(driver.page_source, "html.parser")
            post_containers = soup.find_all('div', {'class': 'update-components-text'})

            results = []
            for post in post_containers:
                clean_text = post.get_text(separator=" ").strip()
                # Basic check to ensure it's a content post
                if len(clean_text) > 20:
                    results.append({"Matching Post": clean_text})

            if results:
                st.success(f"Successfully retrieved {len(results)} posts!")
                st.dataframe(pd.DataFrame(results), use_container_width=True)
            else:
                st.warning("No matching posts found. Try broadening your criteria.")
                
        except Exception as e:
            st.error(f"Search Execution Error: {e}")

    if st.button("🔄 Restart Agent"):
        st.session_state.step = "login_wait"
        st.rerun()
