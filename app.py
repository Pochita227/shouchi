from flask import Flask, render_template
import pandas as pd

app = Flask(__name__)

# Đọc dữ liệu từ file CSV
def read_signals():
    # Đọc file CSV (mặc dù là file Excel thì ta giả định file này có thể mở được như CSV)
    file_path = 'D:/pyth bot - II/demobot2/Data/signals.csv'  # Đảm bảo đường dẫn đúng
    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        print(f"Lỗi khi đọc file CSV: {e}")
        return []

    # Chuyển đổi timestamp từ định dạng mm:ss.s đến thời gian hợp lệ
    try:
        df['timestamp'] = pd.to_datetime(df['timestamp'], format='%M:%S.%f', errors='coerce')
    except Exception as e:
        print(f"Lỗi khi chuyển đổi timestamp: {e}")
    
    return df.to_dict(orient='records')  # Chuyển dữ liệu thành danh sách dict

@app.route('/')
def index():
    signals = read_signals()
    return render_template('index.html', signals=signals)

if __name__ == '__main__':
    app.run(debug=True)
