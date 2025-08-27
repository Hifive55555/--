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

# 动态更新模型钩子
def update_models():
    global models
    models = load_all_models()

# 配置：RSS 源可任意增删
RSS_URLS = [
    'https://rss.aishort.top/?type=cneb',
]

OUTPUT = 'news.xlsx'   # 也可改成 .csv

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
        df_old = pd.read_excel(OUTPUT)
        existing_titles.update(df_old['标题'].tolist())
    
    for rss in RSS_URLS:
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
                    continue
                    
                article = Article(entry.link, language='zh')
                article.download()
                article.parse()
                if not article.text:
                    continue
                    
                content = article.text.strip().replace('\n', ' ')
                title = article.title or entry.title
                
                # Skip if title already exists (double check)
                if title in existing_titles:
                    continue
                
                existing_titles.add(title)
                
                row_data = {
                    '时间': article.publish_date.strftime('%Y-%m-%d %H:%M') if article.publish_date else '',
                    '标题': title,
                    '内容': content,
                }
                
                for model_name, model in models.items():
                    check_value = check(content, model)
                    row_data[model_name] = float(f'{check_value:.4f}')

                rows.append(row_data)
                new_articles_count += 1
                total_processed += 1
                
                # Call callbacks with true progress
                if progress_callback:
                    progress_callback(new_articles_count, max_articles)
                if news_callback:
                    news_callback(row_data)
                    
            except Exception as e:
                print(f"跳过 {entry.link}: {e}")

    df_new = pd.DataFrame(rows)
    
    # Update current_news_df and save to Excel
    if os.path.exists(OUTPUT):
        df_old = pd.read_excel(OUTPUT)
        current_news_df = pd.concat([df_old, df_new])
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