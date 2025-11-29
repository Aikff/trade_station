# services/indicator_engine.py

import pandas_ta as ta

class IndicatorEngine:
    """
    Bu sınıf, tıpkı TradingView Pine Script gibi çalışır.
    Verilen DataFrame üzerine istenen indikatörleri işler.
    """
    
    @staticmethod
    def add_sma(df, length=50):
        # SMA ekler ve sütun adını döndürür
        df.ta.sma(length=length, append=True)
        return f"SMA_{length}"

    @staticmethod
    def add_rsi(df, length=14):
        df.ta.rsi(length=length, append=True)
        return f"RSI_{length}"

    @staticmethod
    def add_bollinger(df, length=20, std=2):
        df.ta.bbands(length=length, std=std, append=True)
        # Bollinger Bands birden çok sütun döndürür (Lower, Mid, Upper)
        return [f"BBL_{length}_{std}.0", f"BBM_{length}_{std}.0", f"BBU_{length}_{std}.0"]

    @staticmethod
    def apply_strategy(df):
        """
        Kullanıcının 'Pine Editor'de yazdığı strateji burasıdır.
        Otomatik olarak tüm indikatörleri uygular.
        """
        IndicatorEngine.add_sma(df, 50)
        IndicatorEngine.add_sma(df, 200) # Golden Cross için
        IndicatorEngine.add_rsi(df, 14)
        return df