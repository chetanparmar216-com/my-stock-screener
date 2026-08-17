import streamlit as st
import pandas as pd
import yfinance as yf
from concurrent.futures import ThreadPoolExecutor

st.set_page_config(page_title="NSE F&O Trade Screener", layout="wide")
st.title("📊 Complete NSE F&O Screener (Intraday, BTST & Swing)")

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

@st.cache_data(ttl=300)
def fetch_stock_data(ticker):
    try:
        df_stock = yf.Ticker(ticker).history(period="6mo", interval="1d")
        if len(df_stock) < 50:
            return None

        df_stock['EMA_20'] = df_stock['Close'].ewm(span=20, adjust=False).mean()
        df_stock['EMA_50'] = df_stock['Close'].ewm(span=50, adjust=False).mean()
        df_stock['EMA_200'] = df_stock['Close'].ewm(span=200, adjust=False).mean()
        df_stock['Vol_Avg'] = df_stock['Volume'].rolling(window=10).mean()

        delta = df_stock['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df_stock['RSI'] = 100 - (100 / (1 + rs))

        curr = df_stock.iloc[-1]
        prev = df_stock.iloc[-2]

        return {
            "Symbol": ticker.replace(".NS", ""),
            "LTP": round(float(curr['Close']), 2),
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

with st.spinner("Fetching all F&O stocks data (please wait a few seconds)..."):
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(fetch_stock_data, FO_STOCKS))
    results = [r for r in results if r is not None]
    df = pd.DataFrame(results)

if df.empty:
    st.error("Market data fetch nahi ho paya. Refresh karein.")
else:
    tab1, tab2, tab3, tab4 = st.tabs(["⚡ Intraday Setup", "🌙 BTST Setup", "📈 Swing Trade Setup", "📋 All F&O Stocks"])

    with tab1:
        st.subheader("Intraday Momentum (Breakout + Volume)")
        intraday_df = df[(df['LTP'] > df['Prev_High']) & (df['Volume'] > 1.1 * df['Vol_Avg']) & (df['RSI'] >= 50)]
        if not intraday_df.empty:
            st.dataframe(intraday_df[['Symbol', 'LTP', 'Prev_High', 'RSI', 'Volume', 'Vol_Avg']], use_container_width=True)
        else:
            st.info("Abhi koi stock Intraday criteria match nahi kar raha.")

    with tab2:
        st.subheader("BTST (Closing Near High + Strong Volume)")
        btst_df = df[(df['LTP'] >= 0.98 * df['High']) & (df['LTP'] > df['Open']) & (df['LTP'] > df['EMA_20'])]
        if not btst_df.empty:
            st.dataframe(btst_df[['Symbol', 'LTP', 'High', 'EMA_20', 'RSI', 'Volume']], use_container_width=True)
        else:
            st.info("Abhi koi stock BTST criteria match nahi kar raha.")

    with tab3:
        st.subheader("Swing Setup (Trend Following)")
        swing_df = df[(df['LTP'] > df['EMA_50']) & (df['EMA_50'] > df['EMA_200']) & (df['RSI'] >= 45) & (df['RSI'] <= 70)]
        if not swing_df.empty:
            st.dataframe(swing_df[['Symbol', 'LTP', 'EMA_50', 'EMA_200', 'RSI']], use_container_width=True)
        else:
            st.info("Abhi koi stock Swing criteria match nahi kar raha.")

    with tab4:
        st.subheader("All F&O Stock Heatmap / Overview")
        st.dataframe(df[['Symbol', 'LTP', 'Prev_High', 'EMA_20', 'EMA_50', 'EMA_200', 'RSI', 'Volume']], use_container_width=True)
