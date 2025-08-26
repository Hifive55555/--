import feedparser
from newspaper import Article
import pandas as pd
import os
from classifier import load, check
from typing import Callable, List, Dict, Optional

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

# 配置：RSS 源可任意增删
RSS_URLS = [
    'https://rss.aishort.top/?type=cneb',
]

OUTPUT = 'news.xlsx'   # 也可改成 .csv

def fetch_news(
    progress_callback: Callable[[int, int], None] = None, 
    news_callback: Callable[[Dict], None] = None,  # Add news callback
    max_articles: int = 50
) -> pd.DataFrame:
    global current_news_df
    rows = []
    total_processed = 0
    
    for rss in RSS_URLS:
        feed = feedparser.parse(rss)
        entries = feed.entries[:max_articles]
        
        for entry in entries:
            try:
                article = Article(entry.link, language='zh')
                article.download()
                article.parse()
                if not article.text:
                    continue
                content = article.text.strip().replace('\n', ' ')
                
                row_data = {
                    '时间': article.publish_date.strftime('%Y-%m-%d %H:%M') if article.publish_date else '',
                    '标题': article.title or entry.title,
                    '内容': content,
                }
                
                for model_name, model in models.items():
                    check_value = check(content, model)
                    row_data[model_name] = float(f'{check_value:.4f}')

                rows.append(row_data)
                total_processed += 1
                
                # Call callbacks
                if progress_callback:
                    progress_callback(total_processed, max_articles)
                if news_callback:
                    news_callback(row_data)  # Send new news immediately
                    
            except Exception as e:
                print(f"跳过 {entry.link}: {e}")

    df_new = pd.DataFrame(rows)
    
    # Update current_news_df and save to Excel
    if os.path.exists(OUTPUT):
        df_old = pd.read_excel(OUTPUT)
        current_news_df = pd.concat([df_old, df_new]).drop_duplicates(subset=['标题'])
    else:
        current_news_df = df_new

    # Convert all model columns to float
    for model_name in models.keys():
        if model_name in current_news_df.columns:
            current_news_df[model_name] = current_news_df[model_name].astype(float)
    
    # Save to Excel
    current_news_df.to_excel(OUTPUT, index=False)
    
    return current_news_df

def get_current_news() -> Optional[pd.DataFrame]:
    """Get the current news DataFrame"""
    global current_news_df
    if current_news_df is None and os.path.exists(OUTPUT):
        current_news_df = pd.read_excel(OUTPUT)
    return current_news_df