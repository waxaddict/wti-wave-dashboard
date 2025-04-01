import streamlit as st
import pandas as pd
import yfinance as yf

def detect_waves(symbol="CL=F", interval="1d", period="90d", min_separation=3):
    df = yf.download(tickers=symbol, period=period, interval=interval, progress=False)
    df = df[['High', 'Low', 'Close']].dropna().reset_index()

    if len(df) < 20:
        return None, "Not enough data for wave detection."

    df['local_min'] = (df['Low'] < df['Low'].shift(1)) & (df['Low'] < df['Low'].shift(-1))
    df['local_max'] = (df['High'] > df['High'].shift(1)) & (df['High'] > df['High'].shift(-1))

    local_lows = df[df['local_min']].reset_index()
    local_highs = df[df['local_max']].reset_index()

    st.write("DEBUG: Data shape =", df.shape)
    st.write("DEBUG: Local lows =", len(local_lows))
    st.write("DEBUG: Local highs =", len(local_highs))

    if len(local_lows) < 2 or len(local_highs) < 1:
        return None, "Not enough swing points found."

    for i in range(len(local_lows) - 1):
        try:
            wave1_low_idx = int(local_lows.loc[i, 'index'])

            wave1_high_candidates = local_highs[local_highs['index'] > wave1_low_idx + min_separation]
            if wave1_high_candidates.empty:
                continue

            wave1_high_idx = int(wave1_high_candidates.iloc[0]['index'])

            wave1_high_price = float(df.iloc[wave1_high_idx]['High'])
            wave1_low_price = float(df.iloc[wave1_low_idx]['Low'])

            wave2_candidates = local_lows[local_lows['index'] > wave1_high_idx + min_separation]
            if wave2_candidates.empty:
                continue

            wave2_idx = int(wave2_candidates.iloc[0]['index'])
            wave2_price = float(df.iloc[wave2_idx]['Low'])

            current_price = float(df['Close'].iloc[-1])
            wave3_confirmed = current_price > wave1_high_price

            st.write("DEBUG: W1 Low idx/price:", wave1_low_idx, wave1_low_price)
            st.write("DEBUG: W1 High idx/price:", wave1_high_idx, wave1_high_price)
            st.write("DEBUG: W2 Low idx/price:", wave2_idx, wave2_price)
            st.write("DEBUG: Current price:", current_price)

            if wave3_confirmed:
                fib_1618 = wave1_low_price + (wave1_high_price - wave1_low_price) * 1.618
                fib_200 = wave1_low_price + (wave1_high_price - wave1_low_price) * 2.0
                fib_2618 = wave1_low_price + (wave1_high_price - wave1_low_price) * 2.618

                return {
                    "wave1_low": round(wave1_low_price, 2),
                    "wave1_high": round(wave1_high_price, 2),
                    "wave2_low": round(wave2_price, 2),
                    "current_price": round(current_price, 2),
                    "wave3_confirmed": True,
                    "fib_targets": {
                        "1.618": round(fib_1618, 2),
                        "2.0": round(fib_200, 2),
                        "2.618": round(fib_2618, 2)
                    }
                }, None
        except Exception as e:
            st.write("DEBUG ERROR in loop:", str(e))
            continue

    return None, "No valid wave 1–3 structure found."

# -----------------------
# Streamlit UI
# -----------------------
st.set_page_config(page_title="Wave Engine v2 – Clean Debug", layout="centered")
st.title("Wave Engine v2 – Scalar Fix Applied")
st.markdown("Wave 1–2–3 detection with debug outputs and scalar-safe indexing.")

timeframe = st.selectbox("Timeframe", ["1d", "4h", "2h"])
results, error = detect_waves(interval=timeframe)

st.write("DEBUG: Final Results =", results)
st.write("DEBUG: Error =", error)

if error:
    st.error(error)
else:
    st.subheader(f"{timeframe.upper()} Wave Structure")
    st.write(f"Wave 1 Low: **{results['wave1_low']}**")
    st.write(f"Wave 1 High: **{results['wave1_high']}**")
    st.write(f"Wave 2 Low: **{results['wave2_low']}**")
    st.write(f"Current Price: **{results['current_price']}**")
    st.write(f"Wave 3 Confirmed: {'✅ Yes' if results['wave3_confirmed'] else '❌ No'}")

    st.subheader("Wave 3/5 Fib Targets")
    for level, price in results['fib_targets'].items():
        st.write(f"{level}: {price}")