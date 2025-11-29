# services/data_provider.py

import ccxt
import pandas as pd
import pandas_ta as ta
import streamlit as st

class BinanceService:
    def __init__(self):
        self.exchange = ccxt.binance({
            'enableRateLimit': True,
            'options': {'defaultType': 'future'} 
        })

    def get_active_symbols(self):
        try:
            # Piyasaları yükle
            self.exchange.load_markets()
            symbols = []
            for s in self.exchange.symbols:
                market = self.exchange.markets[s]
                # Sadece USDT, Vadeli ve Aktif olanlar
                if market['quote'] == 'USDT' and market['linear'] and market['active']:
                    symbols.append(s)
            
            print(f"✅ Toplam {len(symbols)} aktif parite bulundu.")
            return symbols
        except Exception as e:
            print(f"❌ Sembol listesi çekilemedi: {e}")
            return []

    def fetch_data(self, symbol, timeframe='1d', limit=200):
        # Limit artırıldı: 60 yerine 200. SMA 50 için bol veri lazım.
        try:
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            if not ohlcv:
                return None
            
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            return df
        except Exception as e:
            print(f"❌ Veri hatası ({symbol}): {e}")
            return None

    def calculate_indicators(self, df):
        if df is None or df.empty: return None
        # SMA 50 Hesapla
        try:
            df.ta.sma(length=50, append=True)
            return df
        except Exception as e:
            print(f"İndikatör hatası: {e}")
            return df

    def scanner_logic(self):
        """
        Detaylı Loglama ile Tarama
        """
        symbols = self.get_active_symbols()
        results = []
        
        # Test için sayıyı 50'ye çıkaralım ve Log basalım
        scan_limit = 50 
        print(f"🕵️ İlk {scan_limit} coin taranıyor...")

        for sym in symbols[:scan_limit]: 
            df = self.fetch_data(sym, timeframe='1d')
            
            if df is not None and len(df) > 50:
                df = self.calculate_indicators(df)
                
                # Son satırı al
                last_row = df.iloc[-1]
                last_price = last_row['close']
                last_sma = last_row['SMA_50']
                
                # Debug Baskısı (Terminale bak)
                # Hangi coinde ne bulduğunu görmek için:
                # print(f"{sym} -> Fiyat: {last_price} | SMA: {last_sma}")

                if pd.isna(last_sma):
                    continue

                if last_price > last_sma:
                    deviation = ((last_price - last_sma) / last_sma) * 100
                    print(f"🎯 BULUNDU: {sym} (Sapma: %{deviation:.2f})") # Bulunca terminale yaz
                    results.append({
                        'Symbol': sym,
                        'Price': last_price,
                        'SMA_50': last_sma,
                        'Deviation (%)': round(deviation, 2)
                    })
        
        df_results = pd.DataFrame(results)
        if not df_results.empty:
            df_results = df_results.sort_values(by='Deviation (%)', ascending=False)
            
        return df_results