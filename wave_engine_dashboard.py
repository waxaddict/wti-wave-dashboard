import streamlit as st
import pandas as pd
import yfinance as yf

def test_fetch():
    df = yf.download("CL=F", period="30d", interval="1d", progress=False)
    df = df[['High', 'Low']].dropna().reset_index()
    
    try:
        val1 = float(df.at[5, 'High'])
        val2 = float(df.at[10, 'Low'])
        result = val1 + val2
        st.write("Success:", result)
    except Exception as e:
        st.write("ERROR:", str(e))

st.title("Quick Test: Data Access")
test_fetch()