import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np

def detect_wave2_opportunity(symbol="CL=F", interval="4h", period="90d"):
    df = yf.download(tickers=symbol, period=period, interval=interval, progress=False)
    df = df[['Open', 'High', 'Low', 'Close', 'Volume']].dropna().reset_index()
    df['EMA21'] = df['Close'].ewm(span=21, adjust=False).mean()

    # Identify swing points
    df['local_min'] = (df['Low'] < df['Low'].shift(1)) & (df['Low'] < df['Low'].shift(-1))
    df['local_max'] = (df['High'] > df['High'].shift(1)) & (df['High'] > df['High'].shift(-1))

    local_lows = df[df['local_min']].copy()
    local_lows['index'] = local_lows.index
    local_lows['swing_low'] = df['Low'].loc[local_lows['index']].values
    sorted_lows = local_lows.sort_values(by='swing_low').reset_index(drop=True)

    local_highs = df[df['local_max']].copy()
    local_highs['index'] = local_highs.index

    candidate_rows = []

    if len(sorted_lows) < 2 or len(local_highs) < 1:
        return None, "Not enough swing points", pd.DataFrame()

    for i in range(len(sorted_lows)):
        try:
            wave1_low_idx = int(sorted_lows.loc[i, 'index'])
            wave1_low_price = float(df.iloc[wave1_low_idx]['Low'])

            wave1_high_candidates = local_highs[local_highs['index'] > wave1_low_idx + 3]
            for j in range(len(wave1_high_candidates)):
                wave1_high_idx = int(wave1_high_candidates.iloc[j]['index'])
                wave1_high_price = float(df.iloc[wave1_high_idx]['High'])

                wave1_range = wave1_high_price - wave1_low_price
                if wave1_range < 2.0:
                    continue

                wave2_candidates = sorted_lows[sorted_lows['index'] > wave1_high_idx + 3]
                if wave2_candidates.empty:
                    continue

                wave2_idx = int(wave2_candidates.iloc[0]['index'])
                wave2_price = float(df.iloc[wave2_idx]['Low'])

                retrace = (wave1_high_price - wave2_price) / wave1_range
                if retrace > 1.0:
                    continue

                reversal_candle = ""
                c1 = df.iloc[wave2_idx - 1]
                c2 = df.iloc[wave2_idx]

                if c2['Close'] > c2['Open'] and c1['Close'] < c1['Open'] and c2['Close'] > c1['Open'] and c2['Open'] < c1['Close']:
                    reversal_candle = "Bullish Engulfing"
                elif (c2['Low'] < c1['Low']) and (c2['Close'] > c2['Open']) and ((c2['High'] - c2['Low']) > 2 * abs(c2['Open'] - c2['Close'])):
                    reversal_candle = "Hammer"

                vol_surge = c2['Volume'] > df['Volume'].rolling(window=10).mean().iloc[wave2_idx]
                ema_nearby = abs(c2['Close'] - df['EMA21'].iloc[wave2_idx]) / c2['Close'] < 0.01

                candidate_rows.append({
                    "W1 Low": round(wave1_low_price, 2),
                    "W1 High": round(wave1_high_price, 2),
                    "W2 Low": round(wave2_price, 2),
                    "Retrace %": round(retrace, 3),
                    "Candle": reversal_candle or "None",
                    "Volume Spike": "Yes" if vol_surge else "No",
                    "EMA Confluence": "Yes" if ema_nearby else "No",
                    "Confirmed": reversal_candle and vol_surge and ema_nearby and (0.382 <= retrace <= 0.786)
                })

                if reversal_candle and vol_surge and ema_nearby and (0.382 <= retrace <= 0.786):
                    fib_1618 = wave1_low_price + wave1_range * 1.618
                    fib_200 = wave1_low_price + wave1_range * 2.0
                    fib_2618 = wave1_low_price + wave1_range * 2.618

                    return {
                        "wave1_low": round(wave1_low_price, 2),
                        "wave1_high": round(wave1_high_price, 2),
                        "wave2_low": round(wave2_price, 2),
                        "retrace_ratio": round(retrace, 3),
                        "reversal_candle": reversal_candle,
                        "volume_surge": vol_surge,
                        "ema_confluence": ema_nearby,
                        "entry_index": wave2_idx,
                        "current_price": float(df['Close'].iloc[-1]),
                        "fib_targets": {
                            "1.618": round(fib_1618, 2),
                            "2.0": round(fib_200, 2),
                            "2.618": round(fib_2618, 2)
                        }
                    }, None, pd.DataFrame(candidate_rows)
        except Exception as e:
            continue

    return None, "No valid Wave 2 opportunity found.", pd.DataFrame(candidate_rows)

# Streamlit UI
st.set_page_config(page_title="Wave 2 Finder", layout="centered")
st.title("Wave 2 Opportunity Finder")
st.markdown("Detects fib retracements, reversal candles, volume, and EMA21 confluence.")

result, error, candidates = detect_wave2_opportunity()

if error:
    st.error(error)
else:
    st.subheader("Wave 2 Setup Found")
    st.write(f"Wave 1 Low: **{result['wave1_low']}**")
    st.write(f"Wave 1 High: **{result['wave1_high']}**")
    st.write(f"Wave 2 Low: **{result['wave2_low']}**")
    st.write(f"Retracement: **{result['retrace_ratio']}**")
    st.write(f"Reversal Candle: **{result['reversal_candle']}**")
    st.write(f"Volume Surge: **{'✅' if result['volume_surge'] else '❌'}**")
    st.write(f"EMA Confluence: **{'✅' if result['ema_confluence'] else '❌'}**")
    st.write(f"Current Price: **{result['current_price']}**")

    st.subheader("Wave 3 Fib Target Projections")
    for level, target in result['fib_targets'].items():
        st.write(f"{level}: {target}")

if not candidates.empty:
    st.subheader("All Detected Wave 1 + 2 Candidates")
    st.dataframe(candidates)