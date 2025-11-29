# services/notifier.py

import requests
import os
from dotenv import load_dotenv

load_dotenv()

class TelegramNotifier:
    def __init__(self):
        self.token = os.getenv("TELEGRAM_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")
        
        if not self.token or not self.chat_id:
            print("⚠️ UYARI: Telegram Token veya Chat ID eksik!")

    def send_message(self, message):
        """
        Telegram'a mesaj gönderir. HTML veya Markdown destekler.
        """
        if not self.token: return

        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "HTML", # Kalın yazı vb. için
            "disable_web_page_preview": True
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code != 200:
                print(f"Telegram Hatası: {response.text}")
        except Exception as e:
            print(f"Mesaj Gönderilemedi: {e}")

    def format_alert(self, coin_data):
        """
        Coin verisini şık bir mesaja çevirir.
        """
        symbol = coin_data['Symbol']
        price = coin_data['Price']
        dev = coin_data['Deviation (%)']
        
        # Emoji seçimi
        emoji = "🚀" if dev > 5 else "✅"
        
        msg = f"<b>{emoji} YENİ FIRSAT: {symbol}</b>\n\n"
        msg += f"💰 <b>Fiyat:</b> ${price}\n"
        msg += f"📈 <b>SMA 50 Üzerinde:</b> %{dev} yukarıda\n"
        msg += f"🔗 <a href='https://www.binance.com/en/futures/{symbol.replace('/','_')}'>Binance'de Aç</a>"
        
        return msg