from flask import Flask, render_template
import pandas as pd
import os

app = Flask(__name__)

# Đảm bảo rằng file signals.csv tồn tại
CSV_PATH = 'D:/pyth bot - II/demobot2/Data/signals.csv'

# Hàm để đọc dữ liệu từ signals.csv
def read_signals_csv():
    if os.path.exists(CSV_PATH):
        try:
            df = pd.read_csv(CSV_PATH)
            if df.empty:
                print("File CSV trống.")
                return None
            print(df.head())  # In ra vài dòng đầu tiên để kiểm tra dữ liệu
            return df
        except Exception as e:
            print(f"Lỗi khi đọc file CSV: {e}")
            return None
    else:
        print(f"File CSV không tồn tại tại {CSV_PATH}.")
        return None

@app.route('/')
def home():
    # Lấy dữ liệu từ signals.csv
    df = read_signals_csv()
    
    # Kiểm tra nếu có dữ liệu
    if df is not None and not df.empty:
        signals = df.to_dict(orient='records')  # Chuyển dữ liệu sang dạng dictionary để dễ dàng hiển thị
    else:
        signals = []

    # Render trang home và truyền dữ liệu signals vào template
    return render_template('index.html', signals=signals)

if __name__ == '__main__':
    app.run(debug=True)
