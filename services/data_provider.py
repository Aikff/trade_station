# services/data_provider.py

import ccxt
import pandas as pd
import pandas_ta as ta
import gc # Garbage Collector (Çöp Toplayıcı)

class BinanceService:
    def __init__(self):
        self.exchange = ccxt.binance({
            'enableRateLimit': True,
            'options': {'defaultType': 'future'} 
        })

    def get_active_symbols(self):
        """Aktif USDT Vadeli çiftlerini getirir"""
        try:
            self.exchange.load_markets()
            symbols = []
            for s in self.exchange.symbols:
                market = self.exchange.markets[s]
                if market['quote'] == 'USDT' and market['linear'] and market['active']:
                    symbols.append(s)
            return symbols
        except Exception as e:
            print(f"Sembol listesi hatası: {e}")
            return []

    def fetch_data(self, symbol, timeframe='1d', limit=100):
        """
        RAM DOSTU VERİ ÇEKME
        Limit düşürüldü ve veri tipleri küçültüldü.
        """
        try:
            # Limit optimize edildi
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            if not ohlcv:
                return None
            
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            # --- MEMORY OPTIMIZATION ---
            # Sayıları float32'ye çevirerek RAM kullanımını yarıya indiriyoruz
            cols = ['open', 'high', 'low', 'close', 'volume']
            df[cols] = df[cols].astype('float32')
            
            return df
        except Exception as e:
            print(f"Veri hatası ({symbol}): {e}")
            return None

    def calculate_indicators(self, df):
        if df is None or df.empty: return None
        try:
            df.ta.sma(length=50, append=True)
            return df
        except Exception:
            return df

    def scanner_logic(self):
        """
        Garbage Collection ile optimize edilmiş tarama
        """
        symbols = self.get_active_symbols()
        results = []
        
        # Test/Production için tüm sembolleri dönüyoruz
        # RAM şişmesin diye her adımda temizlik yapacağız
        print(f"🕵️ Tarama Başlıyor (Toplam {len(symbols)} coin)...")

        for i, sym in enumerate(symbols):
            try:
                # Sadece 80 mum çekiyoruz (SMA 50 için yeterli ve hafif)
                df = self.fetch_data(sym, timeframe='1d', limit=80)
                
                if df is not None and len(df) > 50:
                    df = self.calculate_indicators(df)
                    
                    last_row = df.iloc[-1]
                    last_sma = last_row['SMA_50']
                    last_close = last_row['close']
                    
                    if not pd.isna(last_sma):
                        if last_close > last_sma:
                            deviation = ((last_close - last_sma) / last_sma) * 100
                            results.append({
                                'Symbol': sym,
                                'Price': float(last_close),
                                'SMA_50': float(last_sma),
                                'Deviation (%)': round(float(deviation), 2)
                            })
            except Exception as e:
                continue
            
            # --- KRİTİK NOKTA ---
            # Her 15 coinde bir RAM'i temizle
            if i % 15 == 0:
                gc.collect()

        # Son temizlik
        gc.collect()
        
        df_results = pd.DataFrame(results)
        if not df_results.empty:
            df_results = df_results.sort_values(by='Deviation (%)', ascending=False)
            
        return df_results
