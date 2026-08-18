import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
import time

st.set_page_config(page_title="NSE F&O 1:3 Level Screener (Intraday Real-Time)", layout="wide")

# Custom Styling
st.markdown("""
    <style>
        html, body, [class*="css"] { font-size: 16px !important; }
        h1 { font-size: 26px !important; }
        h2, h3 { font-size: 20px !important; }
        .stDataFrame div { font-size: 16px !important; }
        button[data-baseweb="tab"] { font-size: 16px !important; font-weight: bold !important; }
        .stSidebar [class*="css"] { font-size: 16px !important; }
    </style>
""", unsafe_allow_html=True)

st.title("🎯 NSE Real-Time Level Screener (Intraday Logic)")

# Sidebar Settings
st.sidebar.header("⚙️ Scanner Controls")
auto_refresh = st.sidebar.checkbox("🔄 Enable Auto-Refresh", value=True)
refresh_sec = st.sidebar.slider("Refresh Interval (Sec):", min_value=15, max_value=120, value=30, disabled=not auto_refresh)

# Session Log for Preserving Triggered Stocks
if "screener_log" not in st.session_state:
    st.session_state.screener_log = {}

if st.sidebar.button("🔄 Reset Alerts & Force Refresh"):
    st.session_state.screener_log = {}
    st.cache_data.clear()
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
    "FEDERALBNK.NS", "GAIL.NS", "GLENMARK.NS", "GMRAIRPORT.NS", "GNFC.NS", "GODREJCP.NS",
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
    "TRENT.NS", "TVSMOTOR.NS", "UBL.NS", "ULTRACEMCO.NS", "UNIONBANK.NS", "UPL.NS",
    "VEDL.NS", "VOLTAS.NS", "WIPRO.NS", "ZEEL.NS", "ZYDUSLIFE.NS"
]

@st.cache_data(ttl=30)
def load_all_market_data():
    try:
        # Daily data for Daily Pivots, Levels & ATR
        daily_data = yf.download(FO_STOCKS, period="6mo", interval="1d", group_by='ticker', threads=True, progress=False)
        # 5m Intraday data for exact volume surges & candle-level trigger timestamps
        intra_data = yf.download(FO_STOCKS, period="5d", interval="5m", group_by='ticker', threads=True, progress=False)
        
        processed = []

        for ticker in FO_STOCKS:
            try:
                if ticker not in daily_data.columns.levels[0] or ticker not in intra_data.columns.levels[0]:
                    continue
                
                df_daily = daily_data[ticker].dropna().copy()
                df_intra = intra_data[ticker].dropna().copy()

                if len(df_daily) < 30 or len(df_intra) < 20:
                    continue

                # Daily EMAs and ATR
                df_daily['EMA_20'] = df_daily['Close'].ewm(span=20, adjust=False).mean()
                df_daily['EMA_50'] = df_daily['Close'].ewm(span=50, adjust=False).mean()
                df_daily['EMA_200'] = df_daily['Close'].ewm(span=200, adjust=False).mean()

                tr1 = df_daily['High'] - df_daily['Low']
                tr2 = (df_daily['High'] - df_daily['Close'].shift()).abs()
                tr3 = (df_daily['Low'] - df_daily['Close'].shift()).abs()
                tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
                atr = tr.rolling(14).mean().iloc[-1]

                prev = df_daily.iloc[-2]
                prev_high = round(float(prev['High']), 2)
                prev_low = round(float(prev['Low']), 2)
                prev_close = round(float(prev['Close']), 2)

                pivot = (prev_high + prev_low + prev_close) / 3.0
                r1 = round((2 * pivot) - prev_low, 2)
                s1 = round((2 * pivot) - prev_high, 2)

                buy_entry = round(max(prev_high, r1), 2)
                buy_sl = round(max(pivot, prev_high - (0.8 * atr)), 2)
                buy_risk_points = max(buy_entry - buy_sl, buy_entry * 0.003)
                buy_target = round(buy_entry + (buy_risk_points * 3), 2)
                qty_1k_risk = int(1000 // buy_risk_points) if buy_risk_points > 0 else 1

                sell_entry = round(min(prev_low, s1), 2)
                sell_sl = round(min(pivot, prev_low + (0.8 * atr)), 2)
                sell_risk_points = max(sell_sl - sell_entry, sell_entry * 0.003)
                sell_target = round(sell_entry - (sell_risk_points * 3), 2)
                qty_1k_risk_short = int(1000 // sell_risk_points) if sell_risk_points > 0 else 1

                # Intraday Indicators (5m candle basis)
                df_intra['Vol_Avg_Intra'] = df_intra['Volume'].rolling(window=10).mean()
                df_intra['OBV'] = (np.sign(df_intra['Close'].diff()).fillna(0) * df_intra['Volume']).cumsum()
                df_intra['OBV_EMA'] = df_intra['OBV'].ewm(span=20, adjust=False).mean()

                delta = df_intra['Close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / (loss.replace(0, np.nan))
                df_intra['RSI'] = (100 - (100 / (1 + rs))).fillna(50)

                # Filter today's intraday sessions
                today_date = df_intra.index[-1].date()
                today_candles = df_intra[df_intra.index.date == today_date].copy()

                if today_candles.empty:
                    continue

                curr_candle = today_candles.iloc[-1]
                ltp = round(float(curr_candle['Close']), 2)
                open_p = round(float(today_candles.iloc[0]['Open']), 2)
                high_p = round(float(today_candles['High'].max()), 2)
                change_pct = round(((ltp - prev_close) / prev_close) * 100, 2)
                
                vol_ratio = round(float(curr_candle['Volume'] / curr_candle['Vol_Avg_Intra']), 2) if curr_candle['Vol_Avg_Intra'] > 0 else 1.0

                # Check exact candle when Buy / Sell / Institutional criteria were met
                buy_hits = today_candles[today_candles['High'] >= buy_entry]
                sell_hits = today_candles[today_candles['Low'] <= sell_entry]

                heavy_buy_hits = today_candles[
                    (today_candles['Close'] > prev_close) & 
                    (today_candles['Volume'] >= today_candles['Vol_Avg_Intra'] * 1.3) & 
                    (today_candles['OBV'] > today_candles['OBV_EMA'])
                ]
                
                heavy_sell_hits = today_candles[
                    (today_candles['Close'] < prev_close) & 
                    (today_candles['Volume'] >= today_candles['Vol_Avg_Intra'] * 1.3) & 
                    (today_candles['OBV'] < today_candles['OBV_EMA'])
                ]

                buy_time = buy_hits.index[0].strftime("%H:%M") if not buy_hits.empty else "-"
                sell_time = sell_hits.index[0].strftime("%H:%M") if not sell_hits.empty else "-"
                heavy_buy_time = heavy_buy_hits.index[0].strftime("%H:%M") if not heavy_buy_hits.empty else "-"
                heavy_sell_time = heavy_sell_hits.index[0].strftime("%H:%M") if not heavy_sell_hits.empty else "-"

                status = "Neutral"
                if not heavy_buy_hits.empty and curr_candle['Close'] > prev_close:
                    status = "🟢 Heavy Buying"
                elif not heavy_sell_hits.empty and curr_candle['Close'] < prev_close:
                    status = "🔴 Heavy Selling"

                breakout_distance = round(((ltp - buy_entry) / buy_entry) * 100, 2)

                processed.append({
                    "Symbol": ticker.replace(".NS", ""),
                    "LTP": ltp,
                    "Open": open_p,
                    "High": high_p,
                    "Change %": change_pct,
                    "Vol_Ratio": f"{vol_ratio}x",
                    "Raw_Ratio": vol_ratio,
                    "RSI": round(float(curr_candle['RSI']), 2),
                    "Buy": buy_entry,
                    "Stop_Loss": buy_sl,
                    "Target": buy_target,
                    "Quantity (₹1000 Risk)": qty_1k_risk,
                    "Sell": sell_entry,
                    "Stop_Loss_SHORT": sell_sl,
                    "Target_SHORT": sell_target,
                    "Quantity_SHORT": qty_1k_risk_short,
                    "Breakout_Distance": breakout_distance,
                    "Status": status,
                    "Buy_Time": buy_time,
                    "Sell_Time": sell_time,
                    "Heavy_Buy_Time": heavy_buy_time,
                    "Heavy_Sell_Time": heavy_sell_time,
                    "EMA_20": round(float(df_daily['EMA_20'].iloc[-1]), 2),
                    "EMA_50": round(float(df_daily['EMA_50'].iloc[-1]), 2),
                    "EMA_200": round(float(df_daily['EMA_200'].iloc[-1]), 2)
                })
            except Exception:
                continue
        return pd.DataFrame(processed)
    except Exception:
        return pd.DataFrame()

# Function to maintain persistent alerts throughout the session
def maintain_persistent_data(df_current, category_key, time_col):
    if df_current.empty:
        return df_current
    
    if category_key not in st.session_state.screener_log:
        st.session_state.screener_log[category_key] = pd.DataFrame()

    history_df = st.session_state.screener_log[category_key]
    
    # Merge new detections with existing detections and keep first triggered timestamp
    combined = pd.concat([history_df, df_current]).drop_duplicates(subset=['Symbol'], keep='first')
    st.session_state.screener_log[category_key] = combined
    return combined

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
    st.caption(f"⏱️ Dashboard Active: {time.strftime('%H:%M:%S IST')} | Stocks Loaded: {len(df)}")

    tab_best, tab_gainers, tab_losers, tab_buy, tab_short, tab_btst, tab_swing, tab_heavy_buy, tab_heavy_sell = st.tabs([
        "⭐ Best Stock Selection",
        "🚀 Top Gainers", "🔻 Top Losers", 
        "⚡ Level BUY Signals", "📉 Level SHORT Signals", 
        "🌙 BTST Setups", "📈 Swing Trading", 
        "🏛️ Heavy Buying", "🏛️ Heavy Selling"
    ])

    with tab_best:
        st.subheader("⭐ Best Fresh Entry Picks (Strict 1:3 Target)")
        best = df[
            (df['LTP'] >= df['Buy'] * 0.998) & 
            (df['Breakout_Distance'] <= 1.5) & 
            (df['Status'] == "🟢 Heavy Buying") & 
            (df['Raw_Ratio'] >= 1.2) & 
            (df['RSI'] >= 50)
        ].sort_values(by="Raw_Ratio", ascending=False).head(2)

        if not best.empty:
            best_persistent = maintain_persistent_data(best, "best", "Buy_Time")
            cols_best = ['Symbol', 'Buy_Time', 'LTP', 'Change %', 'Buy', 'Stop_Loss', 'Target', 'Quantity (₹1000 Risk)']
            st.dataframe(apply_table_style(best_persistent[cols_best].rename(columns={'Buy_Time': 'Trigger Time'})), use_container_width=True)
        else:
            st.info("Filhaal koi stock fresh entry range (+0% se +1.5%) me nahi hai.")

    with tab_gainers:
        st.subheader("🚀 Top 15 Gainers Today")
        top_g = df[df['Change %'] > 0].sort_values(by="Change %", ascending=False).head(15)
        cols_g = ['Symbol', 'Buy_Time', 'LTP', 'Change %', 'Buy', 'Stop_Loss', 'Target', 'Quantity (₹1000 Risk)']
        st.dataframe(apply_table_style(top_g[cols_g].rename(columns={'Buy_Time': 'Trigger Time'})), use_container_width=True)

    with tab_losers:
        st.subheader("🔻 Top 15 Losers Today")
        top_l = df[df['Change %'] < 0].sort_values(by="Change %", ascending=True).head(15)
        cols_l = ['Symbol', 'Sell_Time', 'LTP', 'Change %', 'Sell', 'Stop_Loss_SHORT', 'Target_SHORT', 'Quantity_SHORT']
        st.dataframe(apply_table_style(top_l[cols_l].rename(columns={'Sell_Time': 'Trigger Time'})), use_container_width=True)

    with tab_buy:
        st.subheader("⚡ Level BUY Signals")
        buy_signals = df[(df['Buy_Time'] != "-") & (df['Breakout_Distance'] <= 2.0)].sort_values(by="Change %", ascending=False)
        if not buy_signals.empty:
            buy_persistent = maintain_persistent_data(buy_signals, "buy_lvl", "Buy_Time")
            cols_b = ['Symbol', 'Buy_Time', 'LTP', 'Change %', 'Buy', 'Stop_Loss', 'Target', 'Quantity (₹1000 Risk)']
            st.dataframe(apply_table_style(buy_persistent[cols_b].rename(columns={'Buy_Time': 'Trigger Time'})), use_container_width=True)
        else:
            st.info("Filhaal koi stock breakout level trigger nahi kar raha hai.")

    with tab_short:
        st.subheader("📉 Level SHORT Signals")
        sell_signals = df[df['Sell_Time'] != "-"].sort_values(by="Change %", ascending=True)
        if not sell_signals.empty:
            sell_persistent = maintain_persistent_data(sell_signals, "short_lvl", "Sell_Time")
            cols_s = ['Symbol', 'Sell_Time', 'LTP', 'Change %', 'Sell', 'Stop_Loss_SHORT', 'Target_SHORT', 'Quantity_SHORT']
            st.dataframe(apply_table_style(sell_persistent[cols_s].rename(columns={'Sell_Time': 'Trigger Time'})), use_container_width=True)
        else:
            st.info("Filhaal koi stock Support breakdown trigger nahi kar raha hai.")

    with tab_btst:
        st.subheader("🌙 BTST Setups")
        btst_df = df[(df['LTP'] >= (df['High'] * 0.98)) & (df['LTP'] > df['Open']) & (df['LTP'] > df['EMA_20'])].sort_values(by="Change %", ascending=False)
        if not btst_df.empty:
            cols_btst = ['Symbol', 'Buy_Time', 'LTP', 'Change %', 'Buy', 'Stop_Loss', 'Target', 'Quantity (₹1000 Risk)']
            st.dataframe(apply_table_style(btst_df[cols_btst].rename(columns={'Buy_Time': 'Trigger Time'})), use_container_width=True)

    with tab_swing:
        st.subheader("📈 Swing Trading Setups")
        swing_df = df[(df['LTP'] > df['EMA_50']) & (df['EMA_50'] > df['EMA_200']) & (df['RSI'] >= 45) & (df['RSI'] <= 70)]
        if not swing_df.empty:
            cols_sw = ['Symbol', 'Buy_Time', 'LTP', 'Change %', 'Buy', 'Stop_Loss', 'Target', 'Quantity (₹1000 Risk)']
            st.dataframe(apply_table_style(swing_df[cols_sw].rename(columns={'Buy_Time': 'Trigger Time'})), use_container_width=True)
        else:
            st.info("Filhaal koi stock Swing setup criteria match nahi kar raha hai.")

    with tab_heavy_buy:
        st.subheader("🏛️ Institutional Heavy Buying")
        buying_df = df[df['Heavy_Buy_Time'] != "-"].sort_values(by="Raw_Ratio", ascending=False)
        if not buying_df.empty:
            buying_persistent = maintain_persistent_data(buying_df, "heavy_buy", "Heavy_Buy_Time")
            cols_hb = ['Symbol', 'Heavy_Buy_Time', 'LTP', 'Change %', 'Buy', 'Stop_Loss', 'Target', 'Quantity (₹1000 Risk)']
            st.dataframe(apply_table_style(buying_persistent[cols_hb].rename(columns={'Heavy_Buy_Time': 'Trigger Time'})), use_container_width=True)
        else:
            st.info("Filhaal koi stock Heavy Buying condition match nahi kar raha hai.")

    with tab_heavy_sell:
        st.subheader("🏛️ Institutional Heavy Selling")
        selling_df = df[df['Heavy_Sell_Time'] != "-"].sort_values(by="Raw_Ratio", ascending=False)
        if not selling_df.empty:
            selling_persistent = maintain_persistent_data(selling_df, "heavy_sell", "Heavy_Sell_Time")
            cols_hs = ['Symbol', 'Heavy_Sell_Time', 'LTP', 'Change %', 'Sell', 'Stop_Loss_SHORT', 'Target_SHORT', 'Quantity_SHORT']
            st.dataframe(apply_table_style(selling_persistent[cols_hs].rename(columns={'Heavy_Sell_Time': 'Trigger Time'})), use_container_width=True)
        else:
            st.info("Filhaal koi stock Heavy Selling condition match nahi kar raha hai.")

    if auto_refresh:
        time.sleep(refresh_sec)
        st.rerun()
        
