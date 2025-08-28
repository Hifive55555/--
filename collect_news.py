import feedparser
from newspaper import Article
import pandas as pd
import os
from classifier import load, check
from typing import Callable, List, Dict, Optional
import logging
import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime
import re

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="news_fetcher.log"
)

# Global variable to store the latest news DataFrame
current_news_df: Optional[pd.DataFrame] = None

# 获取所有模型
def load_all_models(base_folder='train_set'):
    models = {}
    try:
        subfolders = [f.path for f in os.scandir(base_folder) if f.is_dir()]
        for folder in subfolders:
            weight_file = os.path.join(folder, 'weight.json')
            if os.path.exists(weight_file):
                folder_name = os.path.basename(folder)
                models[folder_name] = load(weight_file)
                print(f"已加载模型: {folder_name}")
    except FileNotFoundError:
        print(f"警告: 未找到训练集文件夹 {base_folder}")
    return models

# 加载所有模型
models = load_all_models()

# 动态更新模型钩子
def update_models():
    global models
    models = load_all_models()

# 配置：RSS 源可任意增删
RSS_URLS = [
    'https://rss.aishort.top/?type=cneb',
]

OUTPUT = 'news.xlsx'   # 也可改成 .csv

def extract_date_from_rss(entry):
    """从RSS条目提取日期"""
    # 尝试多种可能的日期字段
    date_fields = ['published', 'updated', 'created', 'pubDate']
    for field in date_fields:
        if hasattr(entry, field):
            try:
                return datetime(*entry[field][:6])
            except (TypeError, ValueError):
                continue
    
    # 如果RSS中没有日期，返回当前时间
    return datetime.now()

def parse_date_from_text(text):
    """从文本中提取日期"""
    if not text:
        return None
    
    # 常见的中文日期格式
    patterns = [
        r'(\d{4})[年/-](\d{1,2})[月/-](\d{1,2})[日\s]*(\d{1,2}):(\d{2})',
        r'(\d{4})[年/-](\d{1,2})[月/-](\d{1,2})日?',
        r'(\d{1,2})[月/-](\d{1,2})日',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            try:
                groups = match.groups()
                if len(groups) >= 3:
                    year, month, day = int(groups[0]), int(groups[1]), int(groups[2])
                    if year < 1000:  # 如果年不完整
                        year += 2000
                    hour, minute = 0, 0
                    if len(groups) >= 5:
                        hour, minute = int(groups[3]), int(groups[4])
                    return datetime(year, month, day, hour, minute)
            except ValueError:
                continue
    
    return None

def extract_content_with_bs(html_content, url):
    """使用BeautifulSoup作为备用内容提取方法"""
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 移除不需要的元素
        for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'advertisement']):
            element.decompose()
        
        # 尝试找到发布日期
        date_selectors = [
            '.publish-time', '.article-time', '.date', '.pubtime',
            'time[datetime]', 'span[class*="date"]', 'span[class*="time"]',
            'meta[property="article:published_time"]', 'meta[name="publishdate"]'
        ]
        
        publish_date = None
        for selector in date_selectors:
            element = soup.select_one(selector)
            if element:
                if selector.startswith('meta'):
                    date_str = element.get('content', '')
                else:
                    date_str = element.get_text().strip()
                
                publish_date = parse_date_from_text(date_str)
                if publish_date:
                    break
        
        # 获取正文内容
        content_selectors = [
            'article', '.article-content', '.content', '.post-content',
            '.entry-content', 'main', '#content', '.news-content', '.text'
        ]
        
        content = None
        for selector in content_selectors:
            element = soup.select_one(selector)
            if element:
                text = element.get_text()
                lines = (line.strip() for line in text.splitlines())
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                content = ' '.join(chunk for chunk in chunks if chunk)
                if len(content) > 100:  # 确保内容足够长
                    break
        
        if not content:
            # 如果特定选择器没找到，使用全文
            text = soup.get_text()
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            content = ' '.join(chunk for chunk in chunks if chunk)
        
        # 尝试提取标题
        title_selectors = [
            'h1', '.title', '.article-title', '.post-title', '.entry-title',
            'meta[property="og:title"]', 'title'
        ]
        
        title = None
        for selector in title_selectors:
            element = soup.select_one(selector)
            if element:
                if selector.startswith('meta'):
                    title = element.get('content', '')
                else:
                    title = element.get_text().strip()
                if title:
                    break
        
        return {
            'title': title,
            'content': content,
            'publish_date': publish_date
        }
    except Exception as e:
        logging.error(f"BeautifulSoup解析失败: {e}")
        return None

def extract_metadata_fallback(entry):
    """当newspaper失败时的备用提取方法"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(entry.link, timeout=10, headers=headers)
        response.raise_for_status()
        response.encoding = response.apparent_encoding
        
        result = extract_content_with_bs(response.text, entry.link)
        if result:
            # 使用RSS的标题作为备选
            result['title'] = result['title'] or entry.title
            # 如果找不到日期，使用RSS中的日期
            if not result['publish_date']:
                result['publish_date'] = extract_date_from_rss(entry)
            return result
            
    except Exception as e:
        logging.error(f"备用提取方法失败: {e}")
    
    return None

def fetch_news(
    progress_callback: Callable[[int, int], None] = None, 
    news_callback: Callable[[Dict], None] = None,
    max_articles: int = 50
) -> pd.DataFrame:
    global current_news_df
    rows = []
    total_processed = 0
    existing_titles = set()
    
    # Load existing titles
    if os.path.exists(OUTPUT):
        try:
            df_old = pd.read_excel(OUTPUT)
            existing_titles.update(df_old['标题'].tolist())
        except Exception as e:
            logging.error(f"读取现有新闻文件失败: {e}")
    
    for rss in RSS_URLS:
        try:
            feed = feedparser.parse(rss)
            entries = feed.entries
            new_articles_count = 0
            
            for entry in entries:
                if new_articles_count >= max_articles:
                    break
                    
                try:
                    # Skip if title already exists
                    title = entry.title
                    if title in existing_titles:
                        logging.info(f"Skipping duplicate article: {title}")
                        continue
                        
                    # 使用newspaper库解析文章
                    article = Article(entry.link, language='zh', fetch_images=False)
                    article.download()
                    article.parse()
                    
                    # 提取信息
                    if not article.text or len(article.text.strip()) < 50:
                        logging.warning(f"newspaper提取内容不足，使用备用方法: {entry.link}")
                        fallback_result = extract_metadata_fallback(entry)
                        if not fallback_result:
                            continue
                        
                        title = fallback_result['title']
                        content = fallback_result['content']
                        publish_date = fallback_result['publish_date']
                    else:
                        title = article.title or entry.title
                        content = article.text.strip().replace('\n', ' ')
                        publish_date = article.publish_date
                    
                    # 如果还是提取不到日期，使用RSS中的日期
                    if not publish_date:
                        publish_date = extract_date_from_rss(entry)
                    
                    # Skip if title already exists (double check)
                    if title in existing_titles:
                        logging.info(f"Skipping duplicate article: {title}")
                        continue
                    
                    existing_titles.add(title)
                    
                    row_data = {
                        '时间': publish_date.strftime('%Y-%m-%d %H:%M') if publish_date else datetime.now().strftime('%Y-%m-%d %H:%M'),
                        '标题': title,
                        '内容': content,
                    }
                    
                    # 对每个模型进行分类
                    for model_name, model in models.items():
                        try:
                            check_value = check(content, model)
                            row_data[model_name] = float(f'{check_value:.4f}')
                        except Exception as e:
                            logging.error(f"Fail to classify with model {model_name}: {e}")
                            row_data[model_name] = 0.0

                    rows.append(row_data)
                    new_articles_count += 1
                    total_processed += 1
                    
                    # Call callbacks with true progress
                    if progress_callback:
                        progress_callback(new_articles_count, max_articles)
                    if news_callback:
                        news_callback(row_data)
                        
                    # 避免请求过于频繁
                    time.sleep(0.5)
                        
                except Exception as e:
                    logging.exception(f"Fail to process article {entry.link}: {e}")
                    # 即使失败也添加延迟
                    time.sleep(0.5)
        
        except Exception as e:
            logging.exception(f"Fail to parse RSS feed {rss}: {e}")

    # 如果没有获取到新文章，直接返回
    if not rows:
        logging.warning("No new articles fetched.")
        return pd.DataFrame()
    
    df_new = pd.DataFrame(rows)
    
    # Update current_news_df and save to Excel
    try:
        if os.path.exists(OUTPUT):
            df_old = pd.read_excel(OUTPUT)
            current_news_df = pd.concat([df_old, df_new])
        else:
            current_news_df = df_new

        # Convert all model columns to float
        for model_name in models.keys():
            if model_name in current_news_df.columns:
                current_news_df[model_name] = current_news_df[model_name].astype(float)
        
        # 去重并保存
        current_news_df = current_news_df.drop_duplicates(subset=['标题'], keep='last')
        current_news_df.to_excel(OUTPUT, index=False)
        
    except Exception as e:
        logging.exception(f"Fail to save news data: {e}")
    
    return current_news_df

def get_current_news() -> Optional[pd.DataFrame]:
    """Get the current news DataFrame"""
    global current_news_df
    if current_news_df is None and os.path.exists(OUTPUT):
        try:
            current_news_df = pd.read_excel(OUTPUT)
        except Exception as e:
            logging.error(f"Failed to load current news from file: {e}")
            return None
    return current_news_df

if __name__ == "__main__":
    df = fetch_news(max_articles=50)
    logging.debug(f"Fetched news data:\n{df}")
    print(df)