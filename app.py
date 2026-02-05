import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os
import requests
import time
from datetime import datetime, timedelta
from dateutil import parser
from dotenv import load_dotenv
from transformers import pipeline
import stock_data 

st.set_page_config(page_title="Market Analysis Dashboard", layout="wide", page_icon="📈")
load_dotenv()

st.markdown("""
    <style>
    .css-15zrgzn {display: none}
    .css-10trblm {display: none}
    a.anchor-link {display: none !important;}
    div.stButton > button {width: 100%; border-radius: 8px;}
    [data-testid="stSidebar"] div.stButton > button {text-align: left;}
    </style>
    """, unsafe_allow_html=True)

WATCHLIST_FILE = "my_watchlist.txt"

def load_watchlist_from_file():
    if os.path.exists(WATCHLIST_FILE):
        with open(WATCHLIST_FILE, "r") as f:
            return [line.strip() for line in f.readlines() if line.strip()]
    return []

def save_watchlist_to_file(current_list):
    with open(WATCHLIST_FILE, "w") as f:
        for ticker in current_list:
            f.write(f"{ticker}\n")

@st.cache_resource
def load_ai_model():
    model_path = "./finetuned_stock_model"
    try:
        classifier = pipeline("sentiment-analysis", model=model_path, tokenizer=model_path)
        return classifier
    except Exception as e:
        st.error(f"Error loading model: {e}")
        return None

stock_classifier = load_ai_model()

@st.cache_data(ttl=3600, show_spinner=False)
def get_stock_price(ticker, days, user_token):
    base_url = os.getenv("TARGET_PRICE_URL") 
    
    if not user_token or not base_url:
        return pd.DataFrame()

    headers = {"Authorization": f"Bearer {user_token}", "User-Agent": "Mozilla/5.0"}
    target_url = f"{base_url}/{ticker}"
    
    end_date_obj = datetime.now()
    start_date_obj = end_date_obj - timedelta(days=days)
    
    all_price_data = []
    curr_date = start_date_obj
    
    progress_text = "Fetching price history..."
    my_bar = st.progress(0, text=progress_text)
    total_days_range = (end_date_obj - start_date_obj).days
    
    try:
        while curr_date < end_date_obj:
            batch_end = min(curr_date + timedelta(days=30), end_date_obj)
            
            params = {
                "period": "HS_PERIOD_DAILY",
                "start_date": curr_date.strftime("%Y-%m-%d"),
                "end_date": batch_end.strftime("%Y-%m-%d"),
                "limit": 50,
                "page": 1
            }
            
            response = requests.get(target_url, headers=headers, params=params)
            
            if response.status_code == 200:
                batch_result = response.json().get('data', {}).get('result', [])
                if batch_result:
                    all_price_data.extend(batch_result)
            elif response.status_code == 401:
                return pd.DataFrame() 
            
            curr_date = batch_end
            
            if total_days_range > 0:
                days_done = (curr_date - start_date_obj).days
                percent = min(days_done / total_days_range, 1.0)
                my_bar.progress(percent, text=f"Fetching prices: {curr_date.strftime('%Y-%m-%d')}...")

            time.sleep(0.05) 
            
    except Exception:
        pass
    
    my_bar.empty()
    
    if all_price_data:
        df = pd.DataFrame(all_price_data)
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            return df.drop_duplicates(subset=['date']).sort_values('date')
            
    return pd.DataFrame()

@st.cache_data(ttl=900, show_spinner=False)
def get_stock_sentiment(ticker, days, user_token):
    base_url = os.getenv("TARGET_STREAM_URL")
    
    if not user_token or not base_url:
        return None

    headers = {"Authorization": f"Bearer {user_token}", "User-Agent": "Mozilla/5.0"}
    target_url = f"{base_url}/{ticker}"
    
    cutoff_date = datetime.now() - timedelta(days=days)
    
    all_messages = []
    current_cursor = None
    max_loops = 20  
    is_finished = False

    progress_text = f"Analyzing sentiment for last {days} days..."
    my_bar = st.progress(0, text=progress_text)

    try:
        for i in range(max_loops):
            if is_finished: break
            
            my_bar.progress(min((i + 1) / max_loops, 0.9), text=f"Scanning stream (Batch {i+1})...")

            params = {"category": "STREAM_CATEGORY_ALL", "limit": 20}
            if current_cursor:
                params["last_stream_id"] = current_cursor

            response = requests.get(target_url, headers=headers, params=params)
            
            if response.status_code == 200:
                data_json = response.json()
                stream_list = data_json.get('data', {}).get('stream', [])
                next_cursor = data_json.get('data', {}).get('pagination', {}).get('next_cursor')

                if not stream_list: break 

                for msg in stream_list:
                    try:
                        created_at = msg.get('created_at')
                        if not created_at: continue
                        msg_date = parser.parse(created_at).replace(tzinfo=None)
                        
                        if msg_date < cutoff_date:
                            is_finished = True
                            break 
                        
                        content = msg.get('content_original', msg.get('content', ''))
                        
                        if content and stock_classifier:
                            try:
                                ai_res = stock_classifier(content[:512])[0]
                                score = ai_res['score']
                                raw_label = ai_res['label']

                                if score < 0.75:
                                    label = "NEUTRAL 😐"
                                elif raw_label == 'LABEL_1':
                                    label = "BULLISH 🚀"
                                else:
                                    label = "BEARISH 🔻"
                                
                                all_messages.append(label)
                            except: pass
                    except: continue
                
                if next_cursor:
                    current_cursor = next_cursor
                else:
                    break
            else:
                break
            time.sleep(0.05) 

    except Exception:
        pass
    
    my_bar.empty()

    if all_messages:
        total = len(all_messages)
        bullish = all_messages.count("BULLISH 🚀")
        bearish = all_messages.count("BEARISH 🔻")
        neutral = all_messages.count("NEUTRAL 😐")
        
        stats = {"BULLISH": bullish, "BEARISH": bearish, "NEUTRAL": neutral}
        dominant_key = max(stats, key=stats.get)
        
        dominant_label = dominant_key
        if "BULLISH" in dominant_key: dominant_label += " 🚀"
        elif "BEARISH" in dominant_key: dominant_label += " 🔻"
        else: dominant_label += " 😐"
        
        return {
            "total": total,
            "stats": stats,
            "dominant": dominant_label,
            "bullish_pct": (bullish/total)*100
        }
    
    return None

st.markdown("<h1 style='text-align: left; pointer-events: none;'>Market Analysis Dashboard</h1>", unsafe_allow_html=True)
st.markdown("Monitor your portfolio, analyze market sentiment using finetuned ML, and discover diversification opportunities.")

st.sidebar.header("🔑 Authentication")
user_raw_token = st.sidebar.text_input("Enter Auth Token", type="password").strip()

if 'active_ticker' not in st.session_state: st.session_state.active_ticker = "" 
if 'ticker_input_widget' not in st.session_state: st.session_state.ticker_input_widget = ""
if 'watchlist' not in st.session_state: st.session_state.watchlist = load_watchlist_from_file()

def on_ticker_input_change():
    st.session_state.active_ticker = st.session_state.ticker_input_widget

def set_ticker_callback(new_ticker):
    st.session_state.active_ticker = new_ticker
    st.session_state.ticker_input_widget = new_ticker

def update_watchlist(new_list):
    st.session_state.watchlist = new_list
    save_watchlist_to_file(new_list)

st.sidebar.divider()
st.sidebar.header("Portfolio Input")

ticker_input = st.sidebar.text_input(
    "Enter Stock Ticker (e.g., BBCA)", 
    key="ticker_input_widget",
    on_change=on_ticker_input_change
)

timeframe_option = st.sidebar.selectbox("Sentiment Timeframe", ["1 Day", "3 Days"])
days_back = 1 if timeframe_option == "1 Day" else 3

if st.sidebar.button("🔍 Analyze Stock"):
    on_ticker_input_change()

st.sidebar.divider()
st.sidebar.subheader("🌟 My Watchlist")
if st.session_state.watchlist:
    for stock in st.session_state.watchlist:
        st.sidebar.button(
            f"📄 {stock}", 
            key=f"wl_btn_{stock}", 
            on_click=set_ticker_callback, 
            args=(stock,)
        )
else:
    st.sidebar.caption("No favorites yet.")

if not user_raw_token:
    st.warning("🔒 **Locked:** Please enter your Auth Token in the sidebar to access the dashboard.")
    st.stop() 

current_ticker = st.session_state.active_ticker.strip().upper()

if current_ticker:
    user_sector = stock_data.get_ticker_sector(current_ticker)
    
    col1, col2, col3 = st.columns([2, 3, 2])
    col1.metric("Ticker", current_ticker)
    col2.metric("Sector", user_sector)
    
    with col3:
        st.write("") 
        if current_ticker in st.session_state.watchlist:
            if st.button("⭐ Remove Watchlist", type="primary", key="wl_remove"):
                new_list = [x for x in st.session_state.watchlist if x != current_ticker]
                update_watchlist(new_list)
                st.rerun()
        else:
            if st.button("☆ Add to Watchlist", key="wl_add"):
                new_list = st.session_state.watchlist + [current_ticker]
                update_watchlist(new_list)
                st.rerun()

    if user_sector != "Unknown":
        st.success("✅ Sector Identified")
    else:
        st.warning("⚠️ Unknown Sector")

    st.divider()

    st.subheader(f"📊 Technical & Sentiment Analysis: {current_ticker}")
    
    with st.spinner(f"Loading data for {current_ticker}..."):
        df_price = get_stock_price(current_ticker, days=180, user_token=user_raw_token) 
        sentiment_data = get_stock_sentiment(current_ticker, days=days_back, user_token=user_raw_token)

    if df_price.empty and sentiment_data is None:
        st.error("❌ **Data Fetch Failed.** Check your Token or Ticker Symbol.")
    else:
        if not df_price.empty:
            fig = go.Figure(data=[go.Candlestick(x=df_price['date'],
                            open=df_price['open'], high=df_price['high'],
                            low=df_price['low'], close=df_price['close'])])
            fig.update_layout(title=f"{current_ticker} Daily Price Trend", xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Price data not found.")

        if sentiment_data:
            s_col1, s_col2, s_col3 = st.columns(3)
            s_col1.info(f"Dominant Sentiment: **{sentiment_data['dominant']}**")
            s_col2.progress(sentiment_data['bullish_pct'] / 100, text=f"Bullish Score: {sentiment_data['bullish_pct']:.1f}%")
            s_col3.write(f"Sample Size: {sentiment_data['total']} chat streams")
        else:
            st.warning("Sentiment data not found.")

        st.divider()

        st.subheader("💡 Diversification Recommendations")
        if user_sector != "Unknown":
            candidates = stock_data.get_diversification_candidates(user_sector, [current_ticker])
            st.write(f"Since your portfolio contains **{user_sector}**, AI suggests looking at these sectors:")
            
            cand_cols = st.columns(len(candidates))
            for idx, cand in enumerate(candidates):
                with cand_cols[idx]:
                    st.markdown(f"### {cand}")
                    cand_sector = stock_data.get_ticker_sector(cand)
                    st.caption(f"{cand_sector}")
                    
                    with st.spinner("Analyzing..."):
                        cand_sent = get_stock_sentiment(cand, days=days_back, user_token=user_raw_token)
                    
                    if cand_sent:
                        pct = cand_sent['bullish_pct']
                        dom = cand_sent['dominant']
                        if "BULLISH" in dom: st.success(f"{dom} ({pct:.0f}%)")
                        elif "BEARISH" in dom: st.error(f"{dom} ({pct:.0f}%)")
                        else: st.warning(f"{dom} ({pct:.0f}%)")
                    else:
                        st.info("No Data")
                    
                    st.button(
                        f"Open Chart {cand}", 
                        key=f"btn_{cand}", 
                        on_click=set_ticker_callback, 
                        args=(cand,)
                    )
        else:
            st.info("Diversification recommendations are available for known stocks only.")

else:
    st.info("👈 Please enter your Auth Token and a Ticker in the sidebar to start.")