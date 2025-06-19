import pandas as pd
import google.generativeai as genai
import os
from dotenv import load_dotenv
from tqdm import tqdm
import time

# --- PROMPT ENGINEERING SECTION ---
# Bạn có thể chỉnh sửa prompt dưới đây để cải thiện hiệu suất của mô hình.
# Chỗ `{{content}}` sẽ được thay thế bằng nội dung tin tức thực tế.
PROMPT_TEMPLATE = """
You're an expert in sentiment analysis, you will be provided a news that is about a cryto coin.
Analyze the sentiment of the following news content and classify it as either 'positive', 'negative', or 'neutral'.
Return only one classification word.

News:
"{{content}}"

Sentiment:
"""

def get_sentiment(content: str, model, prompt_template: str) -> str:
    """
    Gọi Gemini API để lấy cảm xúc của một đoạn văn bản.

    Args:
        content: Nội dung văn bản cần phân tích.
        model: Đối tượng mô hình generatvie.
        prompt_template: Mẫu prompt để sử dụng.

    Returns:
        Nhãn cảm xúc ('positive', 'negative', 'neutral') hoặc 'error'.
    """
    if not content or pd.isna(content):
        return "neutral"
        
    prompt = prompt_template.replace("{{content}}", str(content))
    
    try:
        # Tăng thời gian chờ cho yêu cầu
        response = model.generate_content(prompt, request_options={'timeout': 100})
        label = response.text.strip().lower()
        if label in ['positive', 'negative', 'neutral']:
            return label
        else:
            # Ghi lại các phản hồi không mong muốn để gỡ lỗi
            print(f"Unexpected label: '{label}' for content: '{content[:50]}...'")
            return 'error'
    except Exception as e:
        print(f"Đã xảy ra lỗi: {e}")
        return "error"

def main():
    """
    Hàm chính để chạy script phân tích cảm xúc.
    """
    # 1. Tải các biến môi trường
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Lỗi: Không tìm thấy GEMINI_API_KEY. Vui lòng tạo file .env và thêm API key của bạn.")
        return

    genai.configure(api_key=api_key)
    
    # Sử dụng mô hình 'gemini-1.5-flash', một lựa chọn hiệu quả và nhanh chóng.
    # Bạn có thể thay đổi nó thành bất kỳ mô hình nào có sẵn.
    model = genai.GenerativeModel('gemma-3n-e4b-it')

    # 2. Tải dữ liệu
    # Script nằm trong llm_analysis, dữ liệu nằm trong crawl_binance
    input_csv_path = '../crawl_binance/binance_news.csv'
    output_csv_path = 'analysis.csv'
    
    try:
        df = pd.read_csv(input_csv_path, header=None, names=['coin_name', 'content'])
    except FileNotFoundError:
        print(f"Lỗi: Không tìm thấy file đầu vào tại {input_csv_path}")
        return

    # 3. Phân tích cảm xúc và lưu trữ kết quả
    results = []
    print("Bắt đầu phân tích cảm xúc...")
    
    # Sử dụng tqdm để có thanh tiến trình
    for index, row in tqdm(df.iterrows(), total=df.shape[0], desc="Đang xử lý"):
        coin_name = row['coin_name']
        content = row['content']
        
        sentiment = get_sentiment(content, model, PROMPT_TEMPLATE)
        results.append({'coin_name': coin_name, 'label': sentiment})
        # Tạm dừng giữa các lần gọi API để tránh vượt quá giới hạn
        time.sleep(2.5) 

    # 4. Lưu kết quả
    output_df = pd.DataFrame(results)
    output_df.to_csv(output_csv_path, index=False, encoding='utf-8-sig')
    print(f"\nPhân tích hoàn tất. Kết quả được lưu vào {output_csv_path}")

if __name__ == "__main__":
    main()