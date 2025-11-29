# bot.py

import time
import json
import os
from datetime import datetime
from services.data_provider import BinanceService
from services.notifier import TelegramNotifier

# Ayarlar
CHECK_INTERVAL = 3600  # 1 Saat (Saniye cinsinden)
HISTORY_FILE = "sent_alerts.json"

def load_history():
    """Daha önce sinyal atılan coinleri ve zamanlarını yükler."""
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_history(history):
    """Sinyal geçmişini kaydeder."""
    with open(HISTORY_FILE, 'w') as f:
        json.dump(history, f)

def clean_old_history(history):
    """24 saatten eski kayıtları temizler (Tekrar sinyal verebilmek için)"""
    now = time.time()
    # Sadece son 24 saatteki (86400 saniye) kayıtları tut
    new_history = {k: v for k, v in history.items() if now - v < 86400}
    return new_history

def main():
    print("🤖 Crypto Bot Başlatılıyor...")
    
    service = BinanceService()
    notifier = TelegramNotifier()
    
    # Başlangıç mesajı
    notifier.send_message("🤖 <b>Sistem Online!</b> Taramalar başladı.")

    while True:
        try:
            print(f"⏰ Tarama Başlıyor: {datetime.now().strftime('%H:%M:%S')}")
            
            # 1. Geçmişi Yükle ve Temizle
            history = load_history()
            history = clean_old_history(history)
            
            # 2. Piyasayı Tara
            results = service.scanner_logic()
            
            if not results.empty:
                count = 0
                for index, row in results.iterrows():
                    symbol = row['Symbol']
                    
                    # Eğer bu coine son 24 saatte sinyal atmadıysak
                    if symbol not in history:
                        # Mesaj Hazırla ve Gönder
                        msg = notifier.format_alert(row)
                        notifier.send_message(msg)
                        
                        # Geçmişe kaydet (Şu anki zaman damgasıyla)
                        history[symbol] = time.time()
                        count += 1
                        time.sleep(1) # Telegram spam yapmamak için bekle
                
                if count > 0:
                    print(f"✅ {count} yeni bildirim gönderildi.")
                    save_history(history)
                else:
                    print("ℹ️ Yeni fırsat yok (Eskiler zaten gönderildi).")
            
            else:
                print("📉 Kriterlere uygun coin yok.")

        except Exception as e:
            print(f"❌ Beklenmedik Hata: {e}")
            notifier.send_message(f"⚠️ <b>Sistem Hatası:</b> {str(e)}")

        # Bekle
        print(f"💤 {CHECK_INTERVAL/60} dakika bekleniyor...")
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()