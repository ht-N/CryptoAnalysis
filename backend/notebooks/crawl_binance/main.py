from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import time
import re

name = "Default"
profile_path = fr"C:/Users/hello/AppData/Local/Microsoft/Edge/User Data"

webdriver_path = fr"msedgedriver.exe"
service = Service(webdriver_path)
options = webdriver.EdgeOptions()
options.add_argument(f'--user-data-dir={profile_path}')
options.add_argument(f'--profile-directory={name}')
# options.add_argument("headless")

driver = webdriver.Edge(service=service, options=options)

df = pd.read_csv(fr'news.csv')

# Truy cập cột 'link' trong DataFrame
try:
    with open('progress.txt', 'r') as f:
        processed_count = int(f.read().strip())
    print(f"Resuming from position {processed_count}")
except FileNotFoundError:
    processed_count = 0
    print("Starting new crawl from beginning")

urls = df['link'].tolist()
total = len(urls)
all_news_data = []

SAVE_INTERVAL = 1
urls_processed_since_last_save = 0

urls_to_process = urls[processed_count:]

for url in urls_to_process:
    print(f"Processing {processed_count + 1}/{total}: {url}")
    
    try:
        match = re.search(r'hashtag/([^/?]+)', url)
        coin_name = match.group(1).upper() if match else "N/A"
        
        driver.get(url)
        time.sleep(3) 

        # Scroll down to load all posts
        print("Scrolling to load all content...")
        last_height = driver.execute_script("return document.body.scrollHeight")
        for _ in range(10): 
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                print("Reached end of page.")
                break
            last_height = new_height

        print("Waiting for content to be present...")
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'card__description') and contains(@class, 'rich-text')]"))
        )
        
        content_elements = driver.find_elements(By.XPATH, "//div[contains(@class, 'card__description') and contains(@class, 'rich-text')]")
        print(f"Found {len(content_elements)} articles for {coin_name}.")

        for element in content_elements:
            content_text = element.text.replace('\n', ' ').strip()
            # Simple cleaning: remove multiple spaces
            content_text = re.sub(r'\s+', ' ', content_text)
            
            if content_text:
                news_item = {'coin_name': coin_name, 'content': content_text}
                all_news_data.append(news_item)
        
        processed_count += 1
        urls_processed_since_last_save += 1
        print(f"Successfully extracted data from URL. Total articles so far: {len(all_news_data)}")
        
        with open('progress.txt', 'w') as f:
            f.write(str(processed_count))
        
        if urls_processed_since_last_save >= SAVE_INTERVAL:
            print(f"Saving checkpoint data to CSV... ({len(all_news_data)} articles total)")
            temp_df = pd.DataFrame(all_news_data)
            temp_df.to_csv(fr'binance_news.csv', index=False, encoding='utf-8-sig')
            urls_processed_since_last_save = 0
        
    except Exception as e:
        print(f"Error processing URL {url}: {str(e)}")
        processed_count += 1
        with open('progress.txt', 'w') as f:
            f.write(str(processed_count))
        continue

driver.quit()

if all_news_data:
    print(f"Saving final data to CSV... ({len(all_news_data)} articles total)")
    final_df = pd.DataFrame(all_news_data)
    final_df.to_csv(fr'binance_news.csv', index=False, encoding='utf-8-sig')
    
# Reset progress for next run if desired, or comment out to continue later
with open('progress.txt', 'w') as f:
    f.write('0')
print(f"Processing finished. Total news articles saved: {len(all_news_data)}")