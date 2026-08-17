import streamlit as st
import pandas as pd
import yfinance as yf
import time

st.set_page_config(page_title="NSE F&O Expert Screener", layout="wide")

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

st.title("🎯 NSE Level-Based Trade Screener")

# Sidebar Settings
st.sidebar.header("⚙️ Scanner Controls")
auto_refresh = st.sidebar.checkbox("🔄 Enable Auto-Refresh", value=True)
refresh_sec = st.sidebar.slider("Refresh Interval (Sec):", min_value=10, max_value=120, value=30, disabled=not auto_refresh)

if st.sidebar.button("🔄 Force Refresh Now"):
    st.rerun()

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

def load_all_market_data():
    try:
        data = yf.download(FO_STOCKS, period="6mo", interval="1d", group_by='ticker', threads=True, progress=False)
        processed = []
        
        for ticker in FO_STOCKS:
            try:
                if ticker not in data.columns.levels[0]:
                    continue
                df_stock = data[ticker].dropna()
                if len(df_stock) < 50:
                    continue

                df_stock['EMA_20'] = df_stock['Close'].ewm(span=20, adjust=False).mean()
                df_stock['EMA_50'] = df_stock['Close'].ewm(span=50, adjust=False).mean()
                df_stock['EMA_200'] = df_stock['Close'].ewm(span=200, adjust=False).mean()
                df_stock['Vol_Avg'] = df_stock['Volume'].rolling(window=10).mean()

                delta = df_stock['Close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / loss
                df_stock['RSI'] = 100 - (100 / (1 + rs))

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
                
                ltp = round(float(curr['Close']), 2)
                open_p = round(float(curr['Open']), 2)
                high_p = round(float(curr['High']), 2)
                prev_high = round(float(prev['High']), 2)
                prev_low = round(float(prev['Low']), 2)
                vol_ratio = round(curr['Volume'] / curr['Vol_Avg'], 2) if curr['Vol_Avg'] > 0 else 1.0
                change_pct = round(((float(curr['Close']) - float(prev['Close'])) / float(prev['Close'])) * 100, 2)

                inst_action = "Neutral"
                if ltp > prev['Close'] and vol_ratio >= 1.4 and curr['OBV'] > curr['OBV_EMA']:
                    inst_action = "🟢 Heavy Buying"
                elif ltp < prev['Close'] and vol_ratio >= 1.4 and curr['OBV'] < curr['OBV_EMA']:
                    inst_action = "🔴 Heavy Selling"

                # Core Actionable Levels
                buy_entry = round(prev_high * 1.001, 2)
                buy_sl = round(prev_high * 0.992, 2)
                buy_risk = max(round(buy_entry - buy_sl, 2), round(buy_entry * 0.005, 2))
                buy_target = round(buy_entry + (buy_risk * 2), 2)

                sell_entry = round(prev_low * 0.999, 2)
                sell_sl = round(prev_low * 1.008, 2)
                sell_risk = max(round(sell_sl - sell_entry, 2), round(sell_entry * 0.005, 2))
                sell_target = round(sell_entry - (sell_risk * 2), 2)

                breakout_distance = round(((ltp - prev_high) / prev_high) * 100, 2)

                processed.append({
                    "Symbol": ticker.replace(".NS", ""),
                    "LTP": ltp,
                    "Open": open_p,
                    "High": high_p,
                    "Change %": change_pct,
                    "Vol_Ratio": f"{vol_ratio}x",
                    "Raw_Ratio": vol_ratio,
                    "RSI": round(float(curr['RSI']), 2),
                    "Buy": buy_entry,
                    "Stop_Loss": buy_sl,
                    "Target": buy_target,
                    "Sell": sell_entry,
                    "Stop_Loss_SHORT": sell_sl,
                    "Target_SHORT": sell_target,
                    "Breakout_Distance": breakout_distance,
                    "Prev_High": prev_high,
                    "Prev_Low": prev_low,
                    "Status": inst_action,
                    "EMA_20": round(float(curr['EMA_20']), 2),
                    "EMA_50": round(float(curr['EMA_50']), 2),
                    "EMA_200": round(float(curr['EMA_200']), 2)
                })
            except Exception:
                continue
        return pd.DataFrame(processed)
    except Exception:
        return pd.DataFrame()

def apply_table_style(df_subset):
    format_rules = {
        "Change %": "{:+.2f}%", "LTP": "{:.2f}", "RSI": "{:.2f}", "Open": "{:.2f}", "High": "{:.2f}",
        "Buy": "{:.2f}", "Stop_Loss": "{:.2f}", "Target": "{:.2f}",
        "Sell": "{:.2f}", "Stop_Loss_SHORT": "{:.2f}", "Target_SHORT": "{:.2f}",
        "EMA_20": "{:.2f}", "EMA_50": "{:.2f}", "EMA_200": "{:.2f}"
    }
    active_formats = {k: v for k, v in format_rules.items() if k in df_subset.columns}
    
    def highlight_rows(row):
        color = ''
        if 'Change %' in row:
            if row['Change %'] > 0:
                color = 'color: #00FF66; font-weight: bold;'
            elif row['Change %'] < 0:
                color = 'color: #FF3366; font-weight: bold;'
        styles = [''] * len(row)
        for col_name in ['LTP', 'Change %']:
            if col_name in row.index:
                styles[row.index.get_loc(col_name)] = color
        return styles

    return df_subset.style.format(active_formats).apply(highlight_rows, axis=1)

df = load_all_market_data()

if df.empty:
    st.error("Market data load nahi hua. Page refresh karein.")
else:
    st.caption(f"⏱️ Last auto-updated: {time.strftime('%H:%M:%S IST')} | Mode: {'🔄 Auto-Refresh ON' if auto_refresh else '⏸️ Auto-Refresh OFF'}")

    tab_best, tab_gainers, tab_losers, tab_buy, tab_short, tab_btst, tab_swing, tab_heavy_buy, tab_heavy_sell = st.tabs([
        "⭐ Best Stock Selection",
        "🚀 Top Gainers", "🔻 Top Losers", 
        "⚡ Level BUY Signals", "📉 Level SHORT Signals", 
        "🌙 BTST Setups", "📈 Swing Trading", 
        "🏛️ Heavy Buying", "🏛️ Heavy Selling"
    ])

    with tab_best:
        st.subheader("⭐ Best Fresh Entry Picks")
        best_candidates = df[
            (df['LTP'] >= df['Prev_High']) & 
            (df['Breakout_Distance'] <= 1.5) & 
            (df['Status'] == "🟢 Heavy Buying") & 
            (df['Raw_Ratio'] >= 1.3) & 
            (df['RSI'] >= 52) & 
            (df['LTP'] > df['EMA_20'])
        ].sort_values(by="Raw_Ratio", ascending=False).head(2)

        if not best_candidates.empty:
            st.dataframe(apply_table_style(best_candidates[['Symbol', 'LTP', 'Change %', 'Buy', 'Stop_Loss', 'Target']]), use_container_width=True)
        else:
            st.info("Filhaal koi stock fresh entry range (+0% se +1.5%) me nahi hai.")

    with tab_gainers:
        st.subheader("🚀 Top 15 Gainers Today")
        st.dataframe(apply_table_style(df[df['Change %'] > 0].sort_values(by="Change %", ascending=False).head(15)[['Symbol', 'LTP', 'Change %', 'Buy', 'Stop_Loss', 'Target']]), use_container_width=True)

    with tab_losers:
        st.subheader("🔻 Top 15 Losers Today")
        st.dataframe(apply_table_style(df[df['Change %'] < 0].sort_values(by="Change %", ascending=True).head(15)[['Symbol', 'LTP', 'Change %', 'Sell', 'Stop_Loss_SHORT', 'Target_SHORT']]), use_container_width=True)

    with tab_buy:
        st.subheader("⚡ Level BUY Signals (Fresh Breakout < 1.5%)")
        buy_signals = df[(df['LTP'] >= df['Prev_High']) & (df['Breakout_Distance'] <= 1.5) & (df['Raw_Ratio'] >= 1.2)].sort_values(by="Change %", ascending=False)
        if not buy_signals.empty:
            st.dataframe(apply_table_style(buy_signals[['Symbol', 'LTP', 'Change %', 'Buy', 'Stop_Loss', 'Target']]), use_container_width=True)
        else:
            st.info("Filhaal koi stock fresh Breakout zone me nahi hai.")

    with tab_short:
        st.subheader("📉 Level SHORT Signals")
        sell_signals = df[(df['LTP'] <= df['Prev_Low']) & (df['Raw_Ratio'] >= 1.2)].sort_values(by="Change %", ascending=True)
        if not sell_signals.empty:
            st.dataframe(apply_table_style(sell_signals[['Symbol', 'LTP', 'Change %', 'Sell', 'Stop_Loss_SHORT', 'Target_SHORT']]), use_container_width=True)
        else:
            st.info("Filhaal koi stock Support breakdown trigger nahi kar raha hai.")

    with tab_btst:
        st.subheader("🌙 BTST Setups")
        btst_df = df[(df['LTP'] >= 0.98 *
