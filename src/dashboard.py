import streamlit as st
import pandas as pd
import json
from pathlib import Path

# Setup page configuration
st.set_page_config(page_title="WhatsApp Job Market Analyzer", layout="wide")

# Load the AI-analyzed data
@st.cache_data
def load_data():
    file_path = Path(__file__).parent / "../data/ai_analyzed_jobs.json"
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return pd.DataFrame(data)

df = load_data()

# --- HEADER ---
st.title("📊 WhatsApp Job Market Analyzer")
st.markdown("An AI-powered pipeline extracting unstructured job postings from chat groups into actionable market intelligence.")
st.divider()

# --- METRICS ROW ---
col1, col2, col3 = st.columns(3)
col1.metric("Total Job Posts Analyzed", len(df))
col2.metric("Unique Companies", df['company_name'].nunique())
# Flatten the list of skills to count unique ones
all_skills = [skill for sublist in df['required_skills'].dropna() for skill in sublist]
col3.metric("Total Unique Skills Demanded", len(set(all_skills)))

# --- CHARTS ---
st.subheader("🔥 Top In-Demand Skills")
# Count skill frequency and grab the top 15
skill_counts = pd.Series(all_skills).value_counts().head(15)
st.bar_chart(skill_counts)

# --- RAW DATA FILTERING ---
st.subheader("📋 Search the Database")
search_term = st.text_input("Filter by Job Title or Keyword:")

if search_term:
    filtered_df = df[df['job_title'].str.contains(search_term, case=False, na=False)]
else:
    filtered_df = df

# Display the dataframe cleanly, hiding the massive raw text column
st.dataframe(
    filtered_df[['date', 'job_title', 'company_name', 'location', 'required_skills']], 
    use_container_width=True
)