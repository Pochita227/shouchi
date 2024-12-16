import requests
import time
import hmac
import hashlib
import base64
import pandas as pd
import asyncio
from telegram import Bot
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from datetime import datetime
import os

# ====== 1. Thông tin API OKX ======
api_key = 'your_api_key'       # Thay bằng API key của bạn
secret_key = 'your_secret_key' # Thay bằng Secret key của bạn
passphrase = 'your_passphrase' # Thay bằng Passphrase của bạn

# ====== 2. Thông tin Telegram Bot ======
bot_token = '8121290045:AAE4b8-KspWb4hqfhKmxHr-nuZfZ4WeLvAE'  # Thay bằng token bot của bạn
chat_id = '1636962907'  # Thay bằng chat ID của bạn
bot = Bot(token=bot_token)

# URL endpoint cho Market Data SPOT
url_tickers = "https://www.okx.com/api/v5/market/tickers"
params_tickers = {"instType": "SPOT"}  # Lấy dữ liệu giao dịch SPOT

# URL endpoint cho Candlestick Data
url_candles = "https://www.okx.com/api/v5/market/candles"

# ====== 3. Tạo chữ ký và headers ======
def get_headers():
    timestamp = str(time.time())  # Timestamp hiện tại
    message = timestamp + 'GET' + '/api/v5/market/tickers' + ''
    signature = hmac.new(secret_key.encode('utf-8'), message.encode('utf-8'), hashlib.sha256).digest()
    signature_base64 = base64.b64encode(signature).decode()

    return {
        'OK-ACCESS-KEY': api_key,
        'OK-ACCESS-SIGN': signature_base64,
        'OK-ACCESS-TIMESTAMP': timestamp,
        'OK-ACCESS-PASSPHRASE': passphrase,
        'Content-Type': 'application/json'
    }

# ====== 4. Hàm lưu tín hiệu vào CSV ======
def save_signal_to_csv(inst_id, signal_type):
    signal_data = {
        'timestamp': [datetime.now()],
        'inst_id': [inst_id],
        'signal_type': [signal_type]  # Long hoặc Short
    }
    df = pd.DataFrame(signal_data)

    # Kiểm tra và tạo thư mục D:/Data nếu chưa có
    if not os.path.exists('D:/Data'):
        os.makedirs('D:/Data')

    # Lưu tín hiệu vào file CSV trên ổ D, ghi thêm vào cuối file mà không ghi đè
    try:
        df.to_csv('D:/Data/signals.csv', mode='a', header=not os.path.exists('D:/Data/signals.csv'), index=False)
        print(f"Tín hiệu {signal_type} cho cặp {inst_id} đã được lưu vào D:/Data/signals.csv.")
    except Exception as e:
        print(f"Lỗi khi lưu tín hiệu vào CSV: {e}")

# ====== 5. Hàm phân tích và kiểm tra cặp giao dịch ======
async def analyze_and_send_signal(sent_signals_count):
    headers = get_headers()

    # Tạo session và cấu hình retry với timeout và pool size
    session = requests.Session()
    retries = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
    session.mount('https://', HTTPAdapter(max_retries=retries))

    # Lấy danh sách tất cả các cặp giao dịch từ API
    try:
        response = session.get(url_tickers, headers=headers, params=params_tickers, timeout=10)
        data = response.json()
        if 'data' not in data:
            print("Dữ liệu API không hợp lệ hoặc không có dữ liệu.")
            return sent_signals_count
    except requests.exceptions.RequestException as e:
        print(f"Lỗi khi gọi API lấy cặp giao dịch: {e}")
        return sent_signals_count

    # Lặp qua tất cả các cặp giao dịch
    for item in data['data']:
        inst_id = item['instId']
        print(f"Đang phân tích cặp giao dịch: {inst_id}")

        # Phân tích các khung thời gian
        timeframes = ["15m", "1h", "4h"]  # Các khung thời gian cần phân tích
        signals_for_pair = 0  # Biến đếm số khung thời gian đồng thuận tín hiệu long

        for timeframe in timeframes:
            print(f"Đang phân tích khung thời gian {timeframe} cho {inst_id}")

            # Lấy dữ liệu nến (candlestick) cho từng cặp giao dịch
            params_candles = {
                "instId": inst_id,
                "bar": timeframe,  # Khung thời gian
                "limit": 100  # Lấy 100 dữ liệu gần nhất
            }

            try:
                response_candles = session.get(url_candles, headers=headers, params=params_candles, timeout=10)
                candle_data = response_candles.json()
            except requests.exceptions.RequestException as e:
                print(f"Lỗi khi gọi API lấy dữ liệu nến cho {inst_id} tại khung thời gian {timeframe}: {e}")
                continue

            if 'data' in candle_data and isinstance(candle_data['data'], list) and len(candle_data['data']) > 0:
                columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'high_24h', 'low_24h']
                df = pd.DataFrame(candle_data['data'], columns=columns)

                # Chuyển các cột giá thành kiểu số
                df['close'] = pd.to_numeric(df['close'])
                df['high'] = pd.to_numeric(df['high'])
                df['low'] = pd.to_numeric(df['low'])
                df['open'] = pd.to_numeric(df['open'])

                # Tính toán các chỉ báo
                df['EMA_12'] = df['close'].ewm(span=12, adjust=False).mean()  # EMA 12
                df['EMA_26'] = df['close'].ewm(span=26, adjust=False).mean()  # EMA 26
                df['SMA_50'] = df['close'].rolling(window=50).mean()  # SMA 50
                df['SMA_200'] = df['close'].rolling(window=200).mean()  # SMA 200
                df['RSI'] = 100 - (100 / (1 + (df['close'].diff().where(lambda x: x > 0, 0).rolling(window=14).sum() / df['close'].diff().where(lambda x: x < 0, 0).rolling(window=14).sum())))
                df['MACD'] = df['EMA_12'] - df['EMA_26']  # MACD
                df['Signal_Line'] = df['MACD'].ewm(span=9, adjust=False).mean()  # Signal Line for MACD

                # Tính toán chỉ báo Stochastic Oscillator (%K, %D)
                low_min = df['low'].rolling(window=14).min()
                high_max = df['high'].rolling(window=14).max()
                df['%K'] = (df['close'] - low_min) / (high_max - low_min) * 100  # %K
                df['%D'] = df['%K'].rolling(window=3).mean()  # %D (dòng tín hiệu)

                # Tiến hành phân tích tín hiệu
                signal_count = 0

                if df['EMA_12'].iloc[-1] > df['EMA_26'].iloc[-1]:
                    signal_count += 1  # EMA tín hiệu long
                if df['SMA_50'].iloc[-1] > df['SMA_200'].iloc[-1]:
                    signal_count += 1  # SMA tín hiệu long
                if df['RSI'].iloc[-1] < 30:
                    signal_count += 1  # RSI tín hiệu long (quá bán)
                if df['MACD'].iloc[-1] > df['Signal_Line'].iloc[-1]:
                    signal_count += 1  # MACD tín hiệu long
                if df['%K'].iloc[-1] > df['%D'].iloc[-1]:
                    signal_count += 1  # Stochastic tín hiệu long

                # Kiểm tra và tăng đếm tín hiệu đồng thuận
                if signal_count >= 3:
                    signals_for_pair += 1  # Tăng đếm tín hiệu đồng thuận

        # Gửi tín hiệu nếu ít nhất 2 khung thời gian đồng thuận hoặc khung 4h có tín hiệu đồng thuận
        if signals_for_pair >= 2 or ("4h" in timeframes and signal_count >= 3):
            if "4h" in timeframes and signal_count >= 3:
                message = f"Tín hiệu Long cho cặp giao dịch {inst_id}! Khung 4 giờ đồng thuận tín hiệu long."
            else:
                message = f"Tín hiệu Long cho cặp giao dịch {inst_id}! Đồng thuận ít nhất 2 khung thời gian."

            # Lưu tín hiệu vào CSV
            save_signal_to_csv(inst_id, 'Long')

            # Gửi thông báo
            await bot.send_message(chat_id=chat_id, text=message)
            print(message)  # In ra tín hiệu gửi đi
            sent_signals_count += 1  # Tăng số tín hiệu đã gửi

        # Nếu đã gửi đủ 15 tín hiệu, dừng bot
        if sent_signals_count >= 15:
            print("Đã gửi đủ 15 tín hiệu, dừng bot.")
            return sent_signals_count  # Dừng vòng lặp sau khi gửi đủ 15 tín hiệu

    return sent_signals_count

# ====== 6. Chạy liên tục mỗi 15 phút ======
async def main():
    sent_signals_count = 0  # Biến đếm số tín hiệu đã gửi
    while sent_signals_count < 15:
        sent_signals_count = await analyze_and_send_signal(sent_signals_count)
        await asyncio.sleep(900)  # Ngừng trong 15 phút

# Chạy bot
asyncio.run(main())
