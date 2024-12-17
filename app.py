from flask import Flask, render_template
import pandas as pd
import os

app = Flask(__name__)

@app.route('/')
def index():
    # Đọc dữ liệu từ file CSV
    file_path = "D:/pyth bot - II/demobot2/Data/signals.csv"
    
    # Kiểm tra nếu file CSV tồn tại
    if os.path.exists(file_path):
        try:
            # Đọc file CSV vào DataFrame
            df = pd.read_csv(file_path)

            # Kiểm tra nếu DataFrame có dữ liệu
            if not df.empty:
                # Chuyển DataFrame thành danh sách các dictionary
                signals = df.to_dict(orient='records')
            else:
                signals = []
        except Exception as e:
            print(f"Lỗi khi đọc file CSV: {e}")
            signals = []
    else:
        signals = []

    # Truyền dữ liệu signals vào template
    return render_template('index.html', signals=signals)

if __name__ == "__main__":
    app.run(debug=True)
