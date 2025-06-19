# Import necessary libraries
import os
import xml.etree.ElementTree as ET
import aiohttp
import asyncio
from datetime import datetime
import pytz
import csv
from timeit import default_timer as timer

# Define how old an article can be to be included (in hours)
HOURS_PAST = 24

# Define headline dictionary to store news data
headlines = {'source': [], 'title': [], 'pubDate': [], 'content': []}

async def get_feed_data(session, feed, headers):
    '''
    Get relevant data from RSS feed in an async fashion
    
    Args:
        session: aiohttp session
        feed: URL of the RSS feed
        headers: HTTP headers for the request
    '''
    try:
        async with session.get(feed, headers=headers, timeout=60) as response:
            # Define the root for XML parsing
            text = await response.text()
            root = ET.fromstring(text)
            
            # Find all items in the feed
            items = root.findall('.//item')
            
            for item in items:
                # Extract title and pubDate
                title_elem = item.find('title')
                pubDate_elem = item.find('pubDate')
                
                if title_elem is None or pubDate_elem is None:
                    continue
                    
                title = title_elem.text
                pubDate = pubDate_elem.text
                
                # Extract content (try different possible tags)
                content = None
                for content_tag in ['description', 'content:encoded', 'content']:
                    content_elem = item.find(content_tag)
                    if content_elem is not None and content_elem.text:
                        content = content_elem.text
                        break
                
                if content is None:
                    content = "No content available"
                
                # Ensure no alien characters are being passed
                title = title.encode('UTF-8').decode('UTF-8')
                content = content.encode('UTF-8').decode('UTF-8')
                
                # Parse publication date and check if it's within our timeframe
                try:
                    # Handle different date formats
                    try:
                        published = datetime.strptime(pubDate.replace("GMT", "+0000"), '%a, %d %b %Y %H:%M:%S %z')
                    except ValueError:
                        # Try alternative format
                        published = datetime.strptime(pubDate, '%Y-%m-%dT%H:%M:%S%z')
                    
                    # Calculate time difference
                    time_between = datetime.now(pytz.utc) - published
                    
                    # Only include articles within the defined timeframe
                    if time_between.total_seconds() / (60 * 60) <= HOURS_PAST:
                        headlines['source'].append(feed)
                        headlines['pubDate'].append(pubDate)
                        headlines['title'].append(title)
                        headlines['content'].append(content)
                        print(f"Retrieved: {title}")
                except Exception as e:
                    print(f"Error parsing date {pubDate}: {e}")
    
    except Exception as e:
        print(f'Could not parse {feed}, error: {e}')

async def get_crypto_news(feed_file_path='../data/Crypto feeds.csv'):
    '''
    Fetches news from all crypto RSS feeds
    
    Args:
        feed_file_path: Path to the CSV file with RSS feed URLs
        
    Returns:
        List of dictionaries containing news data
    '''
    # Clear previous headlines
    for key in headlines:
        headlines[key] = []
    
    # Load the CSV file containing crypto feeds
    feeds = []
    try:
        with open(feed_file_path) as csv_file:
            csv_reader = csv.reader(csv_file)
            # Skip header row
            next(csv_reader, None)
            # Add each RSS URL to feeds list
            for row in csv_reader:
                feeds.append(row[0])
        print(f"Loaded {len(feeds)} RSS feeds")
    except FileNotFoundError:
        print(f"Feed file not found: {feed_file_path}")
        return []
    
    # Set headers for the request
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:87.0) Gecko/20100101 Firefox/87.0'
    }
    
    # Time the execution
    start = timer()
    
    async with aiohttp.ClientSession() as session:
        tasks = []
        for feed in feeds:
            task = asyncio.ensure_future(get_feed_data(session, feed, headers))
            tasks.append(task)
        
        # Wait for all tasks to complete
        await asyncio.gather(*tasks)
    
    end = timer()
    print(f"Time to parse feeds: {end - start:.2f} seconds")
    
    # Create a structured result
    result = []
    for i in range(len(headlines['title'])):
        news_item = {
            'source': headlines['source'][i],
            'title': headlines['title'][i],
            'pubDate': headlines['pubDate'][i],
            'content': headlines['content'][i] if i < len(headlines['content']) else None
        }
        result.append(news_item)
    
    return result

def get_crypto_news_sync(feed_file_path='../data/Crypto feeds.csv'):
    """
    Synchronous wrapper for get_crypto_news
    
    Args:
        feed_file_path: Path to the CSV file with RSS feed URLs
        
    Returns:
        List of dictionaries containing news data
    """
    return asyncio.run(get_crypto_news(feed_file_path))

def filter_news_by_keyword(news_list, keyword):
    """
    Filter news articles by keyword
    
    Args:
        news_list: List of news articles
        keyword: Keyword to filter by
        
    Returns:
        Filtered list of news articles
    """
    filtered_news = []
    
    for article in news_list:
        title = article['title'].lower()
        content = article['content'].lower() if article['content'] else ""
        
        if keyword.lower() in title or keyword.lower() in content:
            filtered_news.append(article)
    
    return filtered_news

if __name__ == '__main__':
    # Fetch the latest crypto news
    crypto_news = get_crypto_news_sync()
    print(f"\nRetrieved {len(crypto_news)} crypto news articles")
    
    # Display a sample of retrieved articles
    sample_size = min(3, len(crypto_news))
    for i, article in enumerate(crypto_news[:sample_size]):
        print(f"\n--- Article {i+1} ---")
        print(f"Source: {article['source']}")
        print(f"Title: {article['title']}")
        print(f"Date: {article['pubDate']}")
        
        # Truncate content for display
        content = article['content']
        if content:
            if len(content) > 150:
                content = content[:150] + "..."
        else:
            content = "No content available"
        
        print(f"Content: {content}")
    
    # Example: Filter news by specific cryptocurrencies
    bitcoin_news = filter_news_by_keyword(crypto_news, "bitcoin")
    print(f"\nFound {len(bitcoin_news)} articles about Bitcoin")
    
    ethereum_news = filter_news_by_keyword(crypto_news, "ethereum")
    print(f"Found {len(ethereum_news)} articles about Ethereum") 