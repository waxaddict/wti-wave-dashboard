
import streamlit as st
import pandas as pd
import yfinance as yf

# -----------------------
# Function: Detect Wave 1 and Compute Fib Zones
# -----------------------
def detect_wave_and_fibs(symbol="CL=F", interval="4h", period="60d", window=6):
    df = yf.download(tickers=symbol, period=period, interval=interval, progress=False)
    df = df[['High', 'Low', 'Close']].dropna().reset_index()

    if len(df) < window + 2:
        return None, "Not enough data to detect wave structure."

    df['change'] = df['Close'].diff()
    df['rolling_sum'] = df['change'].rolling(window).sum()
    impulse_idx = df['rolling_sum'].idxmax()

    if impulse_idx < window:
        return None, "Impulse leg detected too early in dataset."

    impulse_start_idx = impulse_idx - window + 1
    impulse_end_idx = impulse_idx

    wave1_low = float(df.loc[impulse_start_idx, 'Low'])
    wave1_high = float(df.loc[impulse_end_idx, 'High'])

    fib_382 = wave1_high - (wave1_high - wave1_low) * 0.382
    fib_618 = wave1_high - (wave1_high - wave1_low) * 0.618

    fib_1618 = wave1_low + (wave1_high - wave1_low) * 1.618
    fib_200 = wave1_low + (wave1_high - wave1_low) * 2.000
    fib_2618 = wave1_low + (wave1_high - wave1_low) * 2.618

    current_price = float(df['Close'].iloc[-1])

    return {
        "wave1_low": wave1_low,
        "wave1_high": wave1_high,
        "fib_retrace_zone": (round(fib_618, 2), round(fib_382, 2)),
        "fib_targets": {
            "1.618": round(fib_1618, 2),
            "2.0": round(fib_200, 2),
            "2.618": round(fib_2618, 2),
        },
        "current_price": round(current_price, 2),
        "in_entry_zone": fib_618 <= current_price <= fib_382
    }, None

# -----------------------
# Streamlit UI
# -----------------------
st.set_page_config(page_title="Wave Engine: Fib Zones", layout="centered")
st.title("Wave Engine")
st.markdown("Detect Wave 1, Ideal Entry Zone (Wave 2), and Projected Targets (Wave 3 / 5)")

timeframe = st.selectbox("Select Timeframe", ["2h", "4h", "1d"])
results, error = detect_wave_and_fibs(interval=timeframe)

if error:
    st.error(error)
else:
    st.subheader(f"{timeframe.upper()} Chart Analysis")
    st.write(f"Wave 1 Low: **{results['wave1_low']}**")
    st.write(f"Wave 1 High: **{results['wave1_high']}**")
    st.write(f"Current Price: **{results['current_price']}**")
    retrace_low, retrace_high = results['fib_retrace_zone']
    st.write(f"**Fib Retracement Zone (Entry - Wave 2):** {retrace_low} → {retrace_high}")
    st.write(f"In Entry Zone: {'✅ Yes' if results['in_entry_zone'] else '❌ No'}")

    st.subheader("Projected Fib Extensions (Wave 3/5 Targets)")
    for label, val in results['fib_targets'].items():
        st.write(f"{label}x: {val}")
