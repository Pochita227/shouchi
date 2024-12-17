from flask import Flask, render_template, jsonify
import pandas as pd
import os

app = Flask(__name__)

# Đường dẫn tới file CSV nơi lưu tín hiệu
csv_path = 'D:/Data/signals.csv'

# Hàm đọc dữ liệu từ CSV
def read_csv():
    try:
        # Kiểm tra nếu tệp CSV tồn tại
        if os.path.exists(csv_path):
            # Đọc dữ liệu từ file CSV
            df = pd.read_csv(csv_path)
            return df.to_dict(orient='records')  # Chuyển DataFrame thành list của dictionary
        else:
            return []  # Trả về danh sách rỗng nếu không có file
    except Exception as e:
        print(f"Lỗi khi đọc CSV: {e}")
        return []

# Route trang chính (giao diện web)
@app.route('/')
def index():
    # Lấy dữ liệu tín hiệu từ file CSV
    data = read_csv()
    return render_template('index.html', signals=data)

# Route API để lấy tín hiệu (dữ liệu dạng JSON)
@app.route('/api/signals')
def api_signals():
    # Trả về dữ liệu tín hiệu dưới dạng JSON
    data = read_csv()
    return jsonify(data)

# Chạy ứng dụng Flask
if __name__ == '__main__':
    app.run(debug=True)
