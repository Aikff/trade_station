#!/bin/bash

# 1. Arka planda Bot'u başlat (& işareti arka plana atar)
python bot.py &

# 2. Ön planda Streamlit sitesini başlat
streamlit run main.py --server.port $PORT --server.address 0.0.0.0