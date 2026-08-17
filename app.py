import streamlit as st
import pandas as pd
import yfinance as yf
from concurrent.futures import ThreadPoolExecutor

st.set_page_config(page_title="NSE F&O Institutional Screener", layout="wide")
st.title("📊 NSE Screener with Institutional & FII/DII Activity")

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

        # Moving Averages & Volume
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

        # Institutional Money Flow: On-Balance Volume (OBV)
        obv = [0]
        for i in range(1, len(df_stock)):
            if df_stock['Close'].iloc[i] > df_stock['Close'].iloc[i - 1]:
                obv.append(obv[-1] + df_stock['Volume'].iloc[i])
            elif df_stock['Close'].iloc[i] < df_stock['Close'].iloc[i - 1]:
                obv.append(obv[-1] - df_stock['Volume'].iloc[i])
            else:
                obv.append(obv[-1])
        df_stock['OBV'] = obv
        df_stock['OBV_EMA'] = df_stock['OBV'].ewm(span=20, adjust=False).mean()

        curr = df_stock.iloc[-1]
        prev = df_stock.iloc[-2]

        vol_ratio = round(curr['Volume'] / curr['Vol_Avg'], 2) if curr['Vol_Avg'] > 0 else 1.0

        # Institutional Signal Logic
        inst_action = "Neutral"
        if curr['Close'] > prev['Close'] and vol_ratio >= 1.8 and curr['OBV'] > curr['OBV_EMA']:
            inst_action = "🟢 Heavy Buying"
        elif curr['Close'] < prev['Close'] and vol_ratio >= 1.8 and curr['OBV'] < curr['OBV_EMA']:
            inst_action = "🔴 Heavy Selling"

        return {
            "Symbol": ticker.replace(".NS", ""),
            "LTP": round(float(curr['Close']), 2),
            "Open": round(float(curr['Open']), 2),
            "High": round(float(curr['High']), 2),
            "Low": round(float(curr['Low']), 2),
            "Volume": int(curr['Volume']),
            "Vol_Ratio": f"{vol_ratio}x",
            "Prev_High": round(float(prev['High']), 2),
            "EMA_20": round(float(curr['EMA_20']), 2),
            "EMA_50": round(float(curr['EMA_50']), 2),
            "EMA_200": round(float(curr['EMA_200']), 2),
            "RSI": round(float(curr['RSI']), 2),
            "Institutional Flow": inst_action
        }
    except Exception:
        return None

with st.spinner("Scanning F&O Universe & Institutional Activity..."):
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(fetch_stock_data, FO_STOCKS))
    results = [r for r in results if r is not None]
    df = pd.DataFrame(results)

if df.empty:
    st.error("Market data fetch nahi ho paya. Refresh karein.")
else:
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "⚡ Intraday", "🌙 BTST", "📈 Swing", "🏛️ Institutional Activity", "📋 All F&O"
    ])

    with tab1:
        st.subheader("Intraday Momentum (Breakout + Volume)")
        intraday_df = df[(df['LTP'] > df['Prev_High']) & (df['RSI'] >= 50)]
        st.dataframe(intraday_df[['Symbol', 'LTP', 'Prev_High', 'RSI', 'Vol_Ratio', 'Institutional Flow']], use_container_width=True)

    with tab2:
        st.subheader("BTST (Strong Close + Institutional Push)")
        btst_df = df[(df['LTP'] >= 0.98 * df['High']) & (df['LTP'] > df['Open']) & (df['LTP'] > df['EMA_20'])]
        st.dataframe(btst_df[['Symbol', 'LTP', 'High', 'EMA_20', 'RSI', 'Vol_Ratio', 'Institutional Flow']], use_container_width=True)

    with tab3:
        st.subheader("Swing Setup (Trend Following)")
        swing_df = df[(df['LTP'] > df['EMA_50']) & (df['EMA_50'] > df['EMA_200']) & (df['RSI'] >= 45) & (df['RSI'] <= 70)]
        st.dataframe(swing_df[['Symbol', 'LTP', 'EMA_50', 'EMA_200', 'RSI', 'Institutional Flow']], use_container_width=True)

    with tab4:
        st.subheader("🏛️ Institutional Accumulation & Distribution Footprints")
        st.caption("Filters: Volume >= 1.8x Average + On-Balance Volume (OBV) Trend Confirmation")
        inst_df = df[df['Institutional Flow'] != "Neutral"]
        if not inst_df.empty:
            st.dataframe(inst_df[['Symbol', 'LTP', 'Institutional Flow', 'Vol_Ratio', 'RSI', 'EMA_20']], use_container_width=True)
        else:
            st.info("Filhaal kisi bhi F&O stock me abnormally high institutional volume trigger nahi hua hai.")

    with tab5:
        st.subheader("All F&O Stock Overview")
        st.dataframe(df[['Symbol', 'LTP', 'Institutional Flow', 'Vol_Ratio', 'RSI', 'EMA_20', 'EMA_50', 'EMA_200']], use_container_width=True)
