import streamlit as st
import pandas as pd
import yfinance as yf
from concurrent.futures import ThreadPoolExecutor
import time

st.set_page_config(page_title="NSE F&O Ultimate Pro Screener", layout="wide")

# Custom Styling (Font 16px & High Readability)
st.markdown("""
    <style>
        html, body, [class*="css"] {
            font-size: 16px !important;
        }
        h1 { font-size: 26px !important; }
        h2, h3 { font-size: 20px !important; }
        .stDataFrame div { font-size: 16px !important; }
        button[data-baseweb="tab"] {
            font-size: 16px !important;
            font-weight: bold !important;
        }
        .stSidebar [class*="css"] { font-size: 16px !important; }
    </style>
""", unsafe_allow_html=True)

st.title("🎯 NSE Level-Based Expert Screener (Clean Numbers)")

# Sidebar Settings
st.sidebar.header("⚙️ Scanner Controls")
auto_refresh = st.sidebar.checkbox("🔄 Enable Auto-Refresh", value=False)
refresh_sec = st.sidebar.slider("Refresh Interval (Sec):", min_value=10, max_value=120, value=30, disabled=not auto_refresh)

if st.sidebar.button("🔄 Force Refresh Now"):
    st.rerun()

# Complete Active NSE F&O Stocks List
FO_STOCKS = [
    "AARTIIND.NS", "ABB.NS", "ABBOTINDIA.NS", "ABCAPITAL.NS", "ABFRL.NS", "ACC.NS", "ADANIENT.NS",
    "ADANIPORTS.NS", "ALKEM.NS", "AMBUJACEM.NS", "APOLLOHOSP.NS", "APOLLOTYRE.NS", "ASHOKLEY.NS",
    "ASIANPAINT.NS", "ASTRAL.NS", "ATUL.NS", "AUBANK.NS", "AUROPHARMA.NS", "AXISBANK.NS",
    "BAJAJ-AUTO.NS", "BAJAJFINSV.NS", "BAJFINANCE.NS", "BALKRISIND.NS", "BALRAMCHIN.NS",
    "BANDHANBNK.NS", "BANKBARODA.NS", "BATAINDIA.NS", "BEL.NS", "BERGEPAINT.NS", "BHARATFORG.NS",
    "BHARTIARTL.NS", "BHEL.NS", "BIOCON.NS", "BOSCHLTD.NS", "BPCL.NS", "BRITANNIA.NS",
    "BSOFT.NS", "CANBK.NS", "CANFINHOME.NS", "CHAMBLFERT.NS", "CHOLAFIN.NS", "CIPLA.NS",
    "COALINDIA.NS", "COFORGE.NS", "COLPAL.NS", "CONCOR.NS", "COROMANDEL.NS", "CROMPTON.NS",
    "CUB.NS", "CUMMINSIND.NS", "DABUR.NS", "DALBHARAT.NS", "DEEPAKNTR.NS", "DIVISLAB.NS",
    "DIXON.NS", "DLF.NS", "DRREDDY.NS", "EICHERMOT.NS", "ESCORTS.NS", "EXIDEIND.NS",
    "FEDERALBNK.NS", "GAIL.NS", "GLENMARK.NS", "GMRINFRA.NS", "GNFC.NS", "GODREJCP.NS",
    "GODREJPROP.NS", "GRANULES.NS", "GRASIM.NS", "GUJGASLTD.NS", "HAL.NS", "HAVELLS.NS",
    "HCLTECH.NS", "HDFCAMC.NS", "HDFCBANK.NS", "HDFCLIFE.NS", "HEROMOTOCO.NS", "HINDALCO.NS",
    "HINDCOPPER.NS", "HINDPETRO.NS", "HINDUNILVR.NS", "ICICIBANK.NS", "ICICIGI.NS",
    "ICICIPRULI.NS", "IDEA.NS", "IDFC.NS", "IDFCFIRSTB.NS", "IEX.NS", "IGL.NS", "INDHOTEL.NS",
    "INDIACEM.NS", "INDIAMART.NS", "INDIGO.NS", "INDUSINDBK.NS", "INDUSTOWER.NS", "INFY.NS",
    "IOC.NS", "IPCALAB.NS", "IRCTC.NS", "ITC.NS", "JINDALSTEL.NS", "JKCEMENT.NS", "JSWSTEEL.NS",
    "JUBLFOOD.NS", "KOTAKBANK.NS", "LALPATHLAB.NS", "LAURUSLABS.NS", "LICHSGFIN.NS", "LT.NS",
    "LTIM.NS", "LTTS.NS", "LUPIN.NS", "M&M.NS", "M&MFIN.NS", "MANAPPURAM.NS", "MARICO.NS",
    "MARUTI.NS", "MCDOWELL-N.NS", "MCX.NS", "METROPOLIS.NS", "MFSL.NS", "MGL.NS", "MOTHERSON.NS",
    "MPHASIS.NS", "MRF.NS", "MUTHOOTFIN.NS", "NATIONALUM.NS", "NAUKRI.NS", "NAVINFLUOR.NS",
    "NESTLEIND.NS", "NMDC.NS", "NTPC.NS", "OBEROIRLTY.NS", "OFSS.NS", "ONGC.NS", "PAGEIND.NS",
    "PEL.NS", "PERSISTENT.NS", "PETRONET.NS", "PFC.NS", "PIDILITIND.NS", "PIIND.NS", "PNB.NS",
    "POLYCAB.NS", "POWERGRID.NS", "PVRINOX.NS", "RAMCOCEM.NS", "RATNAMANI.NS", "RECLTD.NS",
    "RELIANCE.NS", "SAIL.NS", "SBILIFE.NS", "SBIN.NS", "SHREECEM.NS", "SIEMENS.NS", "SRF.NS",
    "SUNPHARMA.NS", "SUNTV.NS", "TATACHEM.NS", "TATACONSUM.NS", "TATAMOTORS.NS", "TATAPOWER.NS",
    "TATASTEEL.NS", "TCS.NS", "TECHM.NS", "RAMCO.NS", "TIINDIA.NS", "TORNTPHARM.NS",
    "TORNTPOWER.NS", "TRENT.NS", "TVSMOTOR.NS", "UBL.NS", "ULTRACEMCO.NS", "UPL.NS",
    "VEDL.NS", "VOLTAS.NS", "WIPRO.NS", "ZEEL.NS", "ZYDUSLIFE.NS"
]

@st.cache_data(ttl=600)
def fetch_stock_data(ticker):
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period="5d")
        if df.empty or len(df) < 2:
            return None
        
        curr_price = df['Close'].iloc[-1]
        prev_close = df['Close'].iloc[-2]
        high = df['High'].iloc[-2]
        low = df['Low'].iloc[-2]
        close = df['Close'].iloc[-2]
        
        # Pivot Points calculation based on previous day
        pivot = (high + low + close) / 3
        r1 = (2 * pivot) - low
        s1 = (2 * pivot) - high
        
        change_pct = ((curr_price - prev_close) / prev_close) * 100
        
        return {
            "Stock": ticker.replace(".NS", ""),
            "Price": round(curr_price, 2),
            "Change %": round(change_pct, 2),
            "Pivot": round(pivot, 2),
            "Support 1": round(s1, 2),
            "Resistance 1": round(r1, 2),
            "Volume": int(df['Volume'].iloc[-1])
        }
    except Exception:
        return None

def fetch_all_data():
    results = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(fetch_stock_data, ticker) for ticker in FO_STOCKS]
        for future in futures:
            res = future.result()
            if res:
                results.append(res)
    return pd.DataFrame(results)

# Main UI Execution
with st.spinner("Fetching live market data for NSE F&O stocks... Please wait."):
    df_data = fetch_all_data()

if df_data.empty:
    st.error("Could not fetch data. Please check your internet connection or try again later.")
else:
    st.success(f"Successfully loaded data for {len(df_data)} F&O stocks.")
    
    # Search & Filter controls
    col1, col2 = st.columns([2, 2])
    with col1:
        search_query = st.text_input("🔍 Search Stock:", "").upper()
    
    if search_query:
        df_data = df_data[df_data["Stock"].str.contains(search_query)]

    # Display DataFrame
    st.dataframe(
        df_data.style.format({
            "Price": "₹{:.2f}",
            "Change %": "{:+.2f}%",
            "Pivot": "₹{:.2f}",
            "Support 1": "₹{:.2f}",
            "Resistance 1": "₹{:.2f}",
            "Volume": "{:,}"
        }),
        use_container_width=True,
        height=500
    )

# Auto-refresh implementation using experimental rerun / time sleep
if auto_refresh:
    time.sleep(refresh_sec)
    st.rerun()
