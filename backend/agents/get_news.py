from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import time
import re
import os
import tempfile
import shutil
import threading
import platform
import uuid
import random

# Global lock to prevent multiple Chrome instances from conflicting
chrome_lock = threading.Lock()

def is_docker_environment():
    """Check if running inside Docker container"""
    try:
        with open('/proc/1/cgroup', 'rt') as f:
            return 'docker' in f.read()
    except:
        return False

def is_windows():
    """Check if running on Windows"""
    return platform.system() == 'Windows'

def kill_existing_chrome_processes():
    """Kill any existing Chrome processes to avoid conflicts"""
    try:
        if is_windows():
            import subprocess
            subprocess.run(['taskkill', '/f', '/im', 'chrome.exe'], 
                         capture_output=True, check=False)
            subprocess.run(['taskkill', '/f', '/im', 'chromedriver.exe'], 
                         capture_output=True, check=False)
        else:
            import psutil
            for proc in psutil.process_iter(['pid', 'name']):
                if 'chrome' in proc.info['name'].lower():
                    proc.kill()
        time.sleep(2)  # Wait for processes to be fully killed
    except Exception as e:
        print(f"Warning: Could not kill existing Chrome processes: {e}")

def get_chrome_driver_service():
    """Get Chrome driver service for different environments"""
    if is_docker_environment():
        # In Docker, use the pre-installed chromedriver
        return ChromeService(executable_path="/usr/local/bin/chromedriver")
    else:
        # Local environment: use webdriver-manager to auto-download
        return ChromeService(ChromeDriverManager().install())

def get_chrome_options():
    """Get Chrome options for different environments"""
    options = Options()
    
    # Common options for all environments
    options.add_argument("--headless=new")  # Use new headless mode
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-software-rasterizer")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--log-level=3")
    
    # Memory and performance optimizations
    options.add_argument("--memory-pressure-off")
    options.add_argument("--disable-background-timer-throttling")
    options.add_argument("--disable-backgrounding-occluded-windows")
    options.add_argument("--disable-renderer-backgrounding")
    
    # Security and stability options
    options.add_argument("--disable-features=TranslateUI,BlinkGenPropertyTrees")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-plugins")
    options.add_argument("--disable-default-apps")
    options.add_argument("--no-first-run")
    options.add_argument("--no-default-browser-check")
    options.add_argument("--disable-web-security")
    options.add_argument("--allow-running-insecure-content")
    options.add_argument("--disable-blink-features=AutomationControlled")
    
    # CRITICAL: Create unique user data directory with UUID to prevent conflicts
    unique_id = str(uuid.uuid4())
    timestamp = str(int(time.time()))
    
    if is_docker_environment():
        # Docker-specific options with unique directories
        user_data_dir = f"/tmp/chrome_user_data_{unique_id}_{timestamp}"
        options.add_argument(f"--user-data-dir={user_data_dir}")
        
        # Use unique remote debugging port to avoid conflicts
        debug_port = random.randint(9222, 9999)
        options.add_argument(f"--remote-debugging-port={debug_port}")
        
        # Additional Docker-specific options
        options.add_argument("--disable-background-networking")
        options.add_argument("--disable-sync")
        options.add_argument("--disable-setuid-sandbox")
        options.add_argument("--disable-features=VizDisplayCompositor")
        options.add_argument("--disable-logging")
        options.add_argument("--silent")
        options.add_argument("--disable-crash-reporter")
        options.add_argument("--disable-in-process-stack-traces")
        options.add_argument("--disable-logging")
        options.add_argument("--disable-dev-tools")
        options.add_argument("--no-zygote")
        options.add_argument("--single-process")
        
    elif is_windows():
        # Windows-specific options
        user_data_dir = f"C:\\temp\\chrome_user_data_{unique_id}_{timestamp}"
        options.add_argument(f"--user-data-dir={user_data_dir}")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
    else:
        # Unix-like systems (Linux/Mac)
        user_data_dir = f"/tmp/chrome_user_data_{unique_id}_{timestamp}"
        options.add_argument(f"--user-data-dir={user_data_dir}")
    
    return options

def run_news_scraping_flow(
    urls_to_process: list
) -> pd.DataFrame:
    """
    The main tool function for scraping news content using Selenium with headless Chrome.
    This function works on both local (Windows/Mac/Linux) and Docker environments.

    Args:
        urls_to_process (list): A list of URLs to scrape.

    Returns:
        pd.DataFrame: A dataframe containing the scraped data ('coin_name', 'content').
    """
    
    print(f"--- Running News Scraping Tool for {len(urls_to_process)} URLs ---")
    print(f"Environment: {'Docker' if is_docker_environment() else 'Local'} ({'Windows' if is_windows() else 'Unix-like'})")

    # Use global lock to prevent concurrent Chrome instances
    with chrome_lock:
        # Kill any existing Chrome processes first
        kill_existing_chrome_processes()
        
        # Create temporary directory for this session
        temp_dir = tempfile.mkdtemp(prefix="chrome_session_")
        
        user_data_dir = None
        try:
            # Get environment-specific Chrome options and service
            options = get_chrome_options()
            service = get_chrome_driver_service()
            
            # Extract user data dir for cleanup later
            for arg in options.arguments:
                if arg.startswith('--user-data-dir='):
                    user_data_dir = arg.split('=')[1]
                    break
            
            # Set temp directory for downloads and cache
            options.add_argument(f"--disk-cache-dir={temp_dir}/cache")
            options.add_argument(f"--crash-dumps-dir={temp_dir}/crashes")
            
            print(f"Initializing Chrome driver with user-data-dir: {user_data_dir}")
            # Create webdriver instance
            driver = webdriver.Chrome(service=service, options=options)
            
            # Set timeouts
            driver.set_page_load_timeout(30)
            driver.implicitly_wait(10)
            
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
                try:
                    driver.quit()
                except:
                    pass
                    
                # Clean up processes
                kill_existing_chrome_processes()
                print("--- News Scraping Tool Finished ---")

        finally:
            # Clean up temporary directory and user data directory
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
                if user_data_dir and os.path.exists(user_data_dir):
                    shutil.rmtree(user_data_dir, ignore_errors=True)
                    print(f"Cleaned up user data directory: {user_data_dir}")
            except Exception as e:
                print(f"Warning: Could not clean up directories: {e}")

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