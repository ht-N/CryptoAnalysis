from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import time
import re
import os


def run_news_scraping_flow(
    urls_to_process: list
) -> pd.DataFrame:
    """
    The main tool function for scraping news content using Selenium with headless Chrome.
    This function is designed to be run inside a Docker container.

    Args:
        urls_to_process (list): A list of URLs to scrape.

    Returns:
        pd.DataFrame: A dataframe containing the scraped data ('coin_name', 'content').
    """
    
    print(f"--- Running News Scraping Tool for {len(urls_to_process)} URLs (Docker/Chrome) ---")

    options = Options()
    # These options are crucial for running Chrome in a Docker container or locally without a GUI
    options.add_argument("--headless")
    options.add_argument("--no-sandbox") # Bypasses OS security model, a must for Docker
    options.add_argument("--disable-dev-shm-usage") # Overcomes limited resource problems
    options.add_argument("--disable-gpu") # Disables GPU hardware acceleration.
    options.add_argument("--disable-software-rasterizer") # An additional flag to disable GPU features.
    options.add_argument("--window-size=1920,1080") # Set a standard window size to avoid rendering issues
    options.add_argument("--log-level=3") # Suppress logs
    
    # In a Docker environment, chromedriver is expected to be in the PATH.
    # We don't need to specify the service path.
    driver = webdriver.Chrome(options=options)
    
    all_news_data = []
    
    try:
        for i, url in enumerate(urls_to_process):
            print(f"Processing URL {i+1}/{len(urls_to_process)}: {url}")
            
            try:
                match = re.search(r'hashtag/([^/?]+)', url)
                coin_name = match.group(1).upper() if match else "N/A"
                
                driver.get(url)
                time.sleep(3) 

                # Scroll down to load all posts
                last_height = driver.execute_script("return document.body.scrollHeight")
                for _ in range(10): 
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(2)
                    new_height = driver.execute_script("return document.body.scrollHeight")
                    if new_height == last_height:
                        break
                    last_height = new_height

                WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'card__description') and contains(@class, 'rich-text')]"))
                )
                
                content_elements = driver.find_elements(By.XPATH, "//div[contains(@class, 'card__description') and contains(@class, 'rich-text')]")
                
                for element in content_elements:
                    content_text = element.text.replace('\n', ' ').strip()
                    content_text = re.sub(r'\s+', ' ', content_text)
                    
                    if content_text:
                        news_item = {'coin_name': coin_name, 'content': content_text}
                        all_news_data.append(news_item)
                
                print(f"✓ Found {len(content_elements)} articles for {coin_name}.")

            except Exception as e:
                print(f"✗ Error processing URL {url}: {e}")
                continue
    
    finally:
        driver.quit()
        print("--- News Scraping Tool Finished ---")

    return pd.DataFrame(all_news_data)


def main():
    """Main function to run the script from the command line, including state management."""
    
    news_csv_path = '../data/news.csv'
    output_csv_path = '../data/binance_news.csv'
    progress_file = 'progress.txt'

    # 1. Load all URLs
    try:
        df_urls = pd.read_csv(news_csv_path)
        all_urls = df_urls['link'].tolist()
    except FileNotFoundError:
        print(f"Error: Input file not found at {news_csv_path}")
        return

    # 2. Manage state to find which URLs to process
    try:
        with open(progress_file, 'r') as f:
            processed_count = int(f.read().strip())
    except FileNotFoundError:
        processed_count = 0
    
    urls_to_process = all_urls[processed_count:]

    if not urls_to_process:
        print("No new URLs to process. Everything is up to date.")
        return

    print(f"Found {len(all_urls)} total URLs. Resuming from position {processed_count}.")
    
    # 3. Run the scraping workflow
    scraped_df = run_news_scraping_flow(urls_to_process)

    # 4. Save results
    if not scraped_df.empty:
        # Append to existing file or create a new one
        if os.path.exists(output_csv_path):
            scraped_df.to_csv(output_csv_path, mode='a', header=False, index=False, encoding='utf-8-sig')
            print(f"Appended {len(scraped_df)} new articles to {output_csv_path}")
        else:
            scraped_df.to_csv(output_csv_path, index=False, encoding='utf-8-sig')
            print(f"Created new file and saved {len(scraped_df)} articles to {output_csv_path}")

        # 5. Update progress file
        new_processed_count = processed_count + len(urls_to_process)
        with open(progress_file, 'w') as f:
            f.write(str(new_processed_count))
        print(f"Progress updated to {new_processed_count}.")

    else:
        print("Scraping finished, but no new data was collected.")


if __name__ == "__main__":
    main()