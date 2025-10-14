"""
feedback_analysis.py

A script/module to analyze feedback data from the backend, identify failure modes, and generate actionable insights for model/data improvement.
"""
import requests
import pandas as pd
import matplotlib.pyplot as plt
import json


import os

# --- CONFIG ---
API_URL = os.getenv("FEEDBACK_API_URL", "http://localhost:8000/feedbacks")
TOKEN = os.getenv("FEEDBACK_API_TOKEN")

def get_token():
    global TOKEN
    if not TOKEN or TOKEN == "YOUR_JWT_TOKEN_HERE":
        print("[INFO] Please provide your JWT token for backend authentication.")
        TOKEN = input("Enter JWT token: ").strip()
    return TOKEN

# --- FETCH FEEDBACK DATA ---
def fetch_feedbacks(api_url=API_URL, token=None, limit=1000):
    token = token or get_token()
    headers = {"Authorization": f"Bearer {token}"}
    params = {"limit": limit}
    try:
        resp = requests.get(api_url, headers=headers, params=params)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.HTTPError as e:
        print(f"[ERROR] HTTP error: {e} - {getattr(e.response, 'text', '')}")
        raise
    except Exception as e:
        print(f"[ERROR] Failed to fetch feedbacks: {e}")
        raise

# --- ANALYSIS FUNCTIONS ---
def analyze_feedback(feedbacks):
    df = pd.DataFrame(feedbacks)
    print("Total feedbacks:", len(df))
    print("\n--- Ratings Distribution ---")
    print(df['rating'].value_counts().sort_index())
    print("\n--- Average Rating ---")
    print(df['rating'].mean())
    print("\n--- Most Common Queries (low rating) ---")
    print(df[df['rating'] <= 2]['query'].value_counts().head(10))
    print("\n--- Most Common Comments (low rating) ---")
    print(df[df['rating'] <= 2]['comment'].value_counts().head(10))
    return df

# --- VISUALIZATION ---
def plot_ratings(df):
    df['rating'].value_counts().sort_index().plot(kind='bar', title='Feedback Ratings Distribution')
    plt.xlabel('Rating')
    plt.ylabel('Count')
    plt.show()

def plot_feedback_over_time(df):
    df['ts'] = pd.to_datetime(df['ts'])
    df.set_index('ts').resample('D')['rating'].mean().plot(title='Average Rating Over Time')
    plt.ylabel('Average Rating')
    plt.show()

# --- EXPORT ---
def export_feedbacks(df, filename="feedbacks_export.csv"):
    df.to_csv(filename, index=False)
    print(f"Exported feedbacks to {filename}")

if __name__ == "__main__":
    feedbacks = fetch_feedbacks()
    if not feedbacks:
        print("No feedbacks found or failed to fetch.")
        exit(1)
    df = analyze_feedback(feedbacks)
    if not df.empty:
        plot_ratings(df)
        plot_feedback_over_time(df)
        export_feedbacks(df)
    else:
        print("No feedback data to analyze.")
