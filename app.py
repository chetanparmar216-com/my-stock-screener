import streamlit as st
import pandas as pd
import yfinance as yf

st.set_page_config(page_title="Custom Stock Screener", layout="wide")
st.title("📊 Intraday, BTST & Swing Stock Screener")

WATCHLIST = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS",
    "SBIN.NS", "BHARTIARTL.NS", "ITC.NS", "TATAMOTORS.NS", "LT.NS",
    "AXISBANK.NS", "KOTAKBANK.NS", "BAJFINANCE.NS", "MARUTI.NS", "TATASTEEL.NS"
]

@st.cache_data(ttl=300)
def fetch_and_calculate(ticker):
    try:
        data = yf.Ticker(ticker).history(period="6mo", interval="1d")
        if len(data) < 50:
            return None
            
        data['EMA_20'] = data['Close'].ewm(span=20, adjust=False).mean()
        data['EMA_50'] = data['Close'].ewm(span=50, adjust=False).mean()
        data['EMA_200'] = data['Close'].ewm(span=200, adjust=False).mean()
        data['Vol_Avg'] = data['Volume'].rolling(window=10).mean()
        
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        data['RSI'] = 100 - (100 / (1 + rs))
        
        curr = data.iloc[-1]
        prev = data.iloc[-2]
        
        return {
            "Symbol": ticker.replace(".NS", ""),
            "Close": round(float(curr['Close']), 2),
            "Open": round(float(curr['Open']), 2),
            "High": round(float(curr['High']), 2),
            "Low": round(float(curr['Low']), 2),
            "Volume": int(curr['Volume']),
            "Vol_Avg": int(curr['Vol_Avg']),
            "Prev_High": round(float(prev['High']), 2),
            "EMA_20": round(float(curr['EMA_20']), 2),
            "EMA_50": round(float(curr['EMA_50']), 2),
            "EMA_200": round(float(curr['EMA_200']), 2),
            "RSI": round(float(curr['RSI']), 2)
        }
    except Exception:
        return None

with st.spinner("Market data scan ho raha hai..."):
    results = []
    for ticker in WATCHLIST:
        res = fetch_and_calculate(ticker)
        if res:
            results.append(res)
    df = pd.DataFrame(results)

if df.empty:
    st.error("Market data fetch nahi ho paya. Kripya page refresh karein.")
else:
    tab1, tab2, tab3 = st.tabs(["⚡ Intraday Setup", "🌙 BTST Setup", "📈 Swing Trade Setup"])

    with tab1:
        st.subheader("Intraday Momentum (Breakout + Volume)")
        intraday_df = df[(df['Close'] > df['Prev_High']) & (df['Volume'] > 1.2 * df['Vol_Avg']) & (df['RSI'] >= 55)]
        if not intraday_df.empty:
            st.dataframe(intraday_df[['Symbol', 'Close', 'Prev_High', 'RSI', 'Volume', 'Vol_Avg']], use_container_width=True)
        else:
            st.info("Abhi koi stock Intraday criteria match nahi kar raha.")

    with tab2:
        st.subheader("BTST (Closing Near High + Volume)")
        btst_df = df[(df['Close'] >= 0.98 * df['High']) & (df['Close'] > df['Open']) & (df['Close'] > df['EMA_20']) & (df['Volume'] > 1.2 * df['Vol_Avg'])]
        if not btst_df.empty:
            st.dataframe(btst_df[['Symbol', 'Close', 'High', 'EMA_20', 'RSI', 'Volume']], use_container_width=True)
        else:
            st.info("Abhi koi stock BTST criteria match nahi kar raha.")

    with tab3:
        st.subheader("Swing Setup (Trend Following)")
        swing_df = df[(df['Close'] > df['EMA_50']) & (df['EMA_50'] > df['EMA_200']) & (df['RSI'] >= 50) & (df['RSI'] <= 68)]
        if not swing_df.empty:
            st.dataframe(swing_df[['Symbol', 'Close', 'EMA_50', 'EMA_200', 'RSI']], use_container_width=True)
        else:
            st.info("Abhi koi stock Swing criteria match nahi kar raha.")
