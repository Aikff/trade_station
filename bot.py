# bot.py

import time
import json
import os
from datetime import datetime
from services.data_provider import BinanceService
from services.notifier import TelegramNotifier

# OPTİMİZASYON: 4 Saatte bir çalış (14400 saniye)
# Günlük mumlara baktığımız için her dakika çalışmasına gerek yok.
CHECK_INTERVAL = 14400 
HISTORY_FILE = "sent_alerts.json"

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_history(history):
    with open(HISTORY_FILE, 'w') as f:
        json.dump(history, f)

def clean_old_history(history):
    now = time.time()
    # 24 saatten eski kayıtları sil
    new_history = {k: v for k, v in history.items() if now - v < 86400}
    return new_history

def main():
    print("🤖 Crypto Bot Başlatılıyor (Low Memory Mode)...")
    
    service = BinanceService()
    notifier = TelegramNotifier()
    
    notifier.send_message("🤖 <b>Sistem Online!</b> (Optimizasyonlu Mod)")

    while True:
        try:
            print(f"⏰ Tarama Başlıyor: {datetime.now().strftime('%H:%M:%S')}")
            
            history = load_history()
            history = clean_old_history(history)
            
            # Data Provider içindeki yeni Garbage Collector'lı taramayı kullanır
            results = service.scanner_logic()
            
            if not results.empty:
                count = 0
                for index, row in results.iterrows():
                    symbol = row['Symbol']
                    
                    if symbol not in history:
                        msg = notifier.format_alert(row)
                        notifier.send_message(msg)
                        history[symbol] = time.time()
                        count += 1
                        time.sleep(1) 
                
                if count > 0:
                    print(f"✅ {count} bildirim gönderildi.")
                    save_history(history)
                else:
                    print("ℹ️ Yeni sinyal yok.")
            else:
                print("📉 Kriterlere uygun coin yok.")

        except Exception as e:
            print(f"❌ Hata: {e}")

        print(f"💤 {CHECK_INTERVAL/60} dakika bekleme modu...")
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
