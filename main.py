# main.py

import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from services.data_provider import BinanceService
from services.indicator_engine import IndicatorEngine
import pandas as pd

# --- 1. CONFIG & CSS ---
st.set_page_config(layout="wide", page_title="Crypto Flow", page_icon="🌊")

st.markdown("""
<style>
    .stApp { background-color: #131722; }
    [data-testid="stSidebar"] { background-color: #0e1118; border-right: 1px solid #2a2e39; }
    div[data-testid="stExpander"] { background-color: #1e222d; border: none; border-radius: 12px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3); }
    div.stButton > button { background-color: #2962ff; color: white; border-radius: 8px; border: none; padding: 10px 24px; font-weight: 600; }
    div.stButton > button:hover { background-color: #1e4bd1; }
    h1, h2, h3 { color: #d1d4dc !important; font-family: 'Helvetica Neue', sans-serif; }
    p, label { color: #b2b5be !important; }
</style>
""", unsafe_allow_html=True)

# --- 2. STATE ---
if 'selected_symbol' not in st.session_state:
    st.session_state.selected_symbol = 'BTC/USDT'
if 'scan_results' not in st.session_state:
    st.session_state.scan_results = None

service = BinanceService()

# --- 3. GRAFİK MOTORU ---
def create_pro_chart(df, symbol, timeframe, show_sma, show_rsi):
    rows = 2 if show_rsi else 1
    row_heights = [0.75, 0.25] if show_rsi else [1.0]
    
    fig = make_subplots(rows=rows, cols=1, shared_xaxes=True, vertical_spacing=0.02, row_heights=row_heights)

    fig.add_trace(go.Candlestick(
        x=df['timestamp'], open=df['open'], high=df['high'], low=df['low'], close=df['close'],
        name='Fiyat', increasing_line_color='#089981', decreasing_line_color='#f23645'
    ), row=1, col=1)

    if show_sma:
        fig.add_trace(go.Scatter(
            x=df['timestamp'], y=df['SMA_50'], line=dict(color='#ff9800', width=2), name='SMA 50'
        ), row=1, col=1)

    if show_rsi:
        fig.add_trace(go.Scatter(x=df['timestamp'], y=df['RSI_14'], line=dict(color='#a485ff', width=2), name='RSI'), row=2, col=1)
        fig.add_hrect(y0=30, y1=70, row=2, col=1, fillcolor="rgba(255,255,255,0.05)", layer="below", line_width=0)

    fig.update_layout(
        height=700, template="plotly_dark", margin=dict(l=0, r=50, t=30, b=0),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(19, 23, 34, 1)',
        hovermode='x unified', dragmode='pan', showlegend=False
    )
    fig.update_xaxes(showspikes=True, spikemode='across', spikesnap='cursor', showline=False, showgrid=True, gridcolor='rgba(255,255,255,0.05)', rangeslider_visible=False)
    fig.update_yaxes(showspikes=True, spikemode='across', spikesnap='cursor', showgrid=True, gridcolor='rgba(255,255,255,0.05)', side='right')

    return fig

# --- 4. DATA FETCHING (OPTIMIZED) ---
@st.cache_data(ttl=300)
def get_cached_data(symbol, tf):
    # LİMİT DÜŞÜRÜLDÜ: 500 -> 200 (RAM Tasarrufu)
    return service.fetch_data(symbol, tf, limit=200)

def set_symbol(symbol):
    st.session_state.selected_symbol = symbol

# --- 5. ARAYÜZ ---
with st.sidebar:
    st.markdown("### ⚡ Crypto Flow")
    with st.expander("📡 Market Scanner", expanded=True):
        if st.button("Taramayı Başlat", use_container_width=True):
            with st.spinner(".."):
                st.session_state.scan_results = service.scanner_logic()
        
        if st.session_state.scan_results is not None:
            if not st.session_state.scan_results.empty:
                st.markdown(f"<div style='text-align:center; color:#089981; margin-bottom:10px;'>{len(st.session_state.scan_results)} Fırsat Bulundu</div>", unsafe_allow_html=True)
                for idx, row in st.session_state.scan_results.iterrows():
                    sym = row['Symbol']
                    dev = row['Deviation (%)']
                    col_a, col_b = st.columns([3, 1])
                    col_a.markdown(f"**{sym}**")
                    col_a.caption(f"Sapma: %{dev}")
                    if col_b.button("➜", key=sym):
                        set_symbol(sym)
                        st.rerun()
                    st.markdown("---")
            else:
                st.warning("Fırsat yok.")

    st.markdown("### ⚙️ Ayarlar")
    timeframe = st.select_slider("", options=['15m', '1h', '4h', '1d'], value='1d')
    c1, c2 = st.columns(2)
    show_sma = c1.checkbox("SMA 50", True)
    show_rsi = c2.checkbox("RSI", False)

current_coin = st.session_state.selected_symbol
col_h1, col_h2 = st.columns([3, 1])
with col_h1: st.markdown(f"<h1 style='margin-bottom:0px;'>{current_coin}</h1>", unsafe_allow_html=True)
with col_h2: st.markdown(f"<h3 style='text-align:right; color:#2962ff;'>{timeframe}</h3>", unsafe_allow_html=True)

with st.spinner('Grafik yükleniyor...'):
    df = get_cached_data(current_coin, timeframe)
    if df is not None:
        IndicatorEngine.apply_strategy(df)
        fig = create_pro_chart(df, current_coin, timeframe, show_sma, show_rsi)
        st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True, 'displayModeBar': False, 'showAxisDragHandles': True})
        
        last_price = df['close'].iloc[-1]
        last_sma = df['SMA_50'].iloc[-1]
        st.markdown("<br>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        c1.metric("Fiyat", f"${last_price:.4f}")
        c2.metric("SMA 50", f"${last_sma:.4f}", delta_color="normal")
        delta = ((last_price - last_sma) / last_sma) * 100
        c3.metric("SMA Uzaklık", f"%{delta:.2f}", delta=f"{delta:.2f}%")
    else:
        st.error("Veri alınamadı.")
