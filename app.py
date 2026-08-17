import streamlit as st
import pandas as pd
import yfinance as yf
from concurrent.futures import ThreadPoolExecutor
import time

st.set_page_config(page_title="NSE Level-Based Pro Screener", layout="wide")

# Custom CSS for Font Size 16px & High Readability Dark Theme
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

st.title("🎯 NSE Level-Based Trade Screener (Key Price Triggers)")

# Sidebar Settings
st.sidebar.header("⚙️ Scanner Controls")
auto_refresh = st.sidebar.checkbox("🔄 Enable Auto-Refresh", value=True)
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
    "POLYCAB.NS", "POWERGRID.NS", "PVRINOX.NS", "RAMCOCEM.NS", "RBLBANK.NS", "RECLTD.NS",
    "RELIANCE.NS", "SAIL.NS", "SBICARD.NS", "SBILIFE.NS", "SBIN.NS", "SHREECEM.NS",
    "SHRIRAMFIN.NS", "SIEMENS.NS", "SRF.NS", "SUNPHARMA.NS", "SUNTV.NS", "SYNGENE.NS",
    "TATACHEM.NS", "TATACOMM.NS", "TATACONSUM.NS", "TATAMOTORS.NS", "TATAPOWER.NS",
    "TATASTEEL.NS", "TCS.NS", "TECHM.NS", "TITAN.NS", "TORNTPHARM.NS", "TORNTPOWER.NS",
    "TRENT.NS", "TVSMOTOR.NS", "UBL.NS", "ULTRACEMCO.NS", "UPL.NS", "VEDL.NS", "VOLTAS.NS",
    "WIPRO.NS", "ZEEL.NS", "ZYDUSLIFE.NS"
]

def fetch_stock_data(ticker):
    try:
        df_stock = yf.Ticker(ticker).history(period="6mo", interval="1d")
        if len(df_stock) < 50:
            return None

        # Technical Indicators
        df_stock['EMA_20'] = df_stock['Close'].ewm(span=20, adjust=False).mean()
        df_stock['EMA_50'] = df_stock['Close'].ewm(span=50, adjust=False).mean()
        df_stock['EMA_200'] = df_stock['Close'].ewm(span=200, adjust=False).mean()
        df_stock['Vol_Avg'] = df_stock['Volume'].rolling(window=10).mean()

        # RSI (14)
        delta = df_stock['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df_stock['RSI'] = 100 - (100 / (1 + rs))

        curr = df_stock.iloc[-1]
        prev = df_stock.iloc[-2]
        
        ltp = round(float(curr['Close']), 2)
        prev_high = round(float(prev['High']), 2)
        prev_low = round(float(prev['Low']), 2)
        vol_ratio = round(curr['Volume'] / curr['Vol_Avg'], 2) if curr['Vol_Avg'] > 0 else 1.0
        change_pct = round(((curr['Close'] - prev['Close']) / prev['Close']) * 100, 2)

        # 1. LEVEL BASED BUY CALCULATION (Breakout over Resistance)
        buy_trigger = prev_high
        buy_entry = round(buy_trigger * 1.001, 2) # Buy when it trades above resistance
        buy_sl = round(buy_trigger * 0.992, 2)     # SL just below the breakout level
        buy_risk = max(round(buy_entry - buy_sl, 2), round(buy_entry * 0.005, 2))
        buy_target = round(buy_entry + (buy_risk * 2), 2)

        # Signal Status for Buying
        if ltp >= buy_entry and vol_ratio >= 1.2:
            buy_status = "🚀 Breakout Confirmed"
        elif ltp >= buy_trigger * 0.995:
            buy_status = "⏳ Near Resistance Level"
        else:
            buy_status = "Inactive"

        # 2. LEVEL BASED SHORT CALCULATION (Breakdown below Support)
        sell_trigger = prev_low
        sell_entry = round(sell_trigger * 0.999, 2) # Sell when it breaks below support
        sell_sl = round(sell_trigger * 1.008, 2)     # SL just above breakdown level
        sell_risk = max(round(sell_sl - sell_entry, 2), round(sell_entry * 0.005, 2))
        sell_target = round(sell_entry - (sell_risk * 2), 2)

        # Signal Status for Selling
        if ltp <= sell_entry and vol_ratio >= 1.2:
            sell_status = "🔻 Breakdown Confirmed"
        elif ltp <= sell_trigger * 1.005:
            sell_status = "⏳ Near Support Level"
        else:
            sell_status = "Inactive"

        return {
            "Symbol": ticker.replace(".NS", ""),
            "LTP": ltp,
            "Change %": change_pct,
            "Vol_Ratio": f"{vol_ratio}x",
            "Raw_Ratio": vol_ratio,
            "RSI": round(float(curr['RSI']), 2),
            "Resistance_Level": buy_trigger,
            "Buy_Above_Level": buy_entry,
            "Stop_Loss_BUY": buy_sl,
            "Target_BUY": buy_target,
            "Buy_Status": buy_status,
            "Support_Level": sell_trigger,
            "Sell_Below_Level": sell_entry,
            "Stop_Loss_SELL": sell_sl,
            "Target_SELL": sell_target,
            "Sell_Status": sell_status,
            "EMA_20": round(float(curr['EMA_20']), 2),
            "EMA_50": round(float(curr['EMA_50']), 2),
            "EMA_200": round(float(curr['EMA_200']), 2)
        }
    except Exception:
        return None

fragment_refresh = refresh_sec if auto_refresh else None

@st.fragment(run_every=fragment_refresh)
def render_screener_dashboard():
    with st.spinner("Analyzing Key Resistance & Support Levels..."):
        with ThreadPoolExecutor(max_workers=12) as executor:
            results = list(executor.map(fetch_stock_data, FO_STOCKS))
        results = [r for r in results if r is not None]
        df = pd.DataFrame(results)

    if df.empty:
        st.error("Market data load nahi hua. Page refresh karein.")
        return

    st.caption(f"⏱️ Last auto-updated: {time.strftime('%H:%M:%S IST')} | Mode: {'🔄 Auto-Refresh ON' if auto_refresh else '⏸️ Auto-Refresh OFF'}")

    tab_buy, tab_sell, tab_pullback, tab_gainers, tab_losers, tab_all = st.tabs([
        "🎯 Level-Based BUY Signals",
        "🎯 Level-Based SHORT Signals",
        "📈 Pullback (Swing Setups)",
        "🚀 Top Gainers",
        "🔻 Top Losers",
        "📋 All F&O Stocks"
    ])

    with tab_buy:
        st.subheader("🎯 Key Resistance Breakout Setups (Buy Above Level)")
        # Show stocks that are near breakout level or already confirmed breakout
        buy_filtered = df[df['Buy_Status'] != "Inactive"].sort_values(by="Change %", ascending=False)
        if not buy_filtered.empty:
            st.dataframe(buy_filtered[['Symbol', 'LTP', 'Resistance_Level', 'Buy_Above_Level', 'Stop_Loss_BUY', 'Target_BUY', 'Vol_Ratio', 'RSI', 'Buy_Status']], use_container_width=True)
        else:
            st.info("Filhaal koi stock Key Resistance Level ke paas trade nahi kar raha hai.")

    with tab_sell:
        st.subheader("🎯 Key Support Breakdown Setups (Sell Below Level)")
        # Show stocks that are near support level or already confirmed breakdown
        sell_filtered = df[df['Sell_Status'] != "Inactive"].sort_values(by="Change %", ascending=True)
        if not sell_filtered.empty:
            st.dataframe(sell_filtered[['Symbol', 'LTP', 'Support_Level', 'Sell_Below_Level', 'Stop_Loss_SELL', 'Target_SELL', 'Vol_Ratio', 'RSI', 'Sell_Status']], use_container_width=True)
        else:
            st.info("Filhaal koi stock Key Support Level ke paas trade nahi kar raha hai.")

    with tab_pullback:
        st.subheader("📈 Pullback Swing Buy (Testing Key EMA 20 Support)")
        pullback_df = df[(df['LTP'] > df['EMA_50']) & (df['EMA_50'] > df['EMA_200']) & (df['LTP'] <= df['EMA_20'] * 1.015) & (df['LTP'] >= df['EMA_20'] * 0.985)]
        if not pullback_df.empty:
            st.dataframe(pullback_df[['Symbol', 'LTP', 'EMA_20', 'EMA_50', 'RSI', 'Vol_Ratio']], use_container_width=True)
        else:
            st.info("Filhaal koi trend-following pullback support level par nahi hai.")

    with tab_gainers:
        st.subheader("🚀 Top Gainers Today")
        st.dataframe(df[df['Change %'] > 0].sort_values(by="Change %", ascending=False).head(15)[['Symbol', 'LTP', 'Change %', 'Vol_Ratio', 'RSI']], use_container_width=True)

    with tab_losers:
        st.subheader("🔻 Top Losers Today")
        st.dataframe(df[df['Change %'] < 0].sort_values(by="Change %", ascending=True).head(15)[['Symbol', 'LTP', 'Change %', 'Vol_Ratio', 'RSI']], use_container_width=True)

    with tab_all:
        st.subheader("📋 Complete F&O Performance & Levels")
        st.dataframe(df[['Symbol', 'LTP', 'Change %', 'Vol_Ratio', 'RSI', 'Resistance_Level', 'Support_Level', 'EMA_20', 'EMA_50', 'EMA_200']], use_container_width=True)

render_screener_dashboard()
