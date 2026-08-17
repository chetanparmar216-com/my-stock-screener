import streamlit as st
import pandas as pd
import yfinance as yf
from concurrent.futures import ThreadPoolExecutor
import time

st.set_page_config(page_title="NSE F&O Auto-Screener", layout="wide")
st.title("📊 NSE F&O Screener (Auto-Refresh Mode)")

# Refresh settings sidebar me
st.sidebar.header("🔄 Refresh Settings")
refresh_interval = st.sidebar.slider("Auto Refresh Every (Seconds):", min_value=5, max_value=60, value=10)

FO_STOCKS = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS",
    "SBIN.NS", "BHARTIARTL.NS", "ITC.NS", "TATAMOTORS.NS", "LT.NS"
] # Testing ke liye choti list, aap isme poori list daal sakte hain

def fetch_stock_data(ticker):
    try:
        # Live 1-day interval ka latest data pull karna
        df_stock = yf.Ticker(ticker).history(period="5d", interval="1d")
        if len(df_stock) < 2: return None

        df_stock['EMA_20'] = df_stock['Close'].ewm(span=20, adjust=False).mean()
        df_stock['Vol_Avg'] = df_stock['Volume'].rolling(window=10).mean()

        curr = df_stock.iloc[-1]
        prev = df_stock.iloc[-2]
        vol_ratio = round(curr['Volume'] / curr['Vol_Avg'], 2) if curr['Vol_Avg'] > 0 else 1.0

        return {
            "Symbol": ticker.replace(".NS", ""),
            "LTP": round(float(curr['Close']), 2),
            "High": round(float(curr['High']), 2),
            "Prev_High": round(float(prev['High']), 2),
            "Vol_Ratio": f"{vol_ratio}x",
            "Time": time.strftime('%H:%M:%S')
        }
    except Exception:
        return None

# Streamlit Fragment jo sirf data table ko update karega bina screen ko jhatka diye
@st.fragment(run_every=refresh_interval)
def show_live_data():
    with ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(fetch_stock_data, FO_STOCKS))
    results = [r for r in results if r is not None]
    df = pd.DataFrame(results)

    if not df.empty:
        st.write(f"⏱️ **Last Updated At:** {df['Time'].iloc[0]}")
        
        tab1, tab2 = st.tabs(["⚡ Live Intraday Breakouts", "📋 Watchlist Overview"])
        with tab1:
            # Intraday rule: LTP > Previous Day High
            intraday = df[df['LTP'] > df['Prev_High']]
            if not intraday.empty:
                st.dataframe(intraday[['Symbol', 'LTP', 'Prev_High', 'Vol_Ratio']], use_container_width=True)
            else:
                st.info("Filhaal koi stock Previous Day High ke upar trade nahi kar raha hai.")
        with tab2:
            st.dataframe(df[['Symbol', 'LTP', 'High', 'Prev_High', 'Vol_Ratio']], use_container_width=True)

# Function call
show_live_data()
