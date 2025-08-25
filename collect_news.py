import feedparser
from newspaper import Article
import pandas as pd
import os
from classifier import load, check
from typing import Callable

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

def fetch_news(progress_callback: Callable[[int, int], None] = None, max_articles: int = 50):
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
                
                # 创建基础数据字典
                row_data = {
                    '时间': article.publish_date.strftime('%Y-%m-%d %H:%M') if article.publish_date else '',
                    '标题': article.title or entry.title,
                    '内容': content,
                }
                
                # 对每个模型计算值
                for model_name, model in models.items():
                    check_value = check(content, model)
                    row_data[model_name] = f'{check_value:.4f}'
                    print(f"处理文章: {article.title} - {model_name}: {check_value}")

                rows.append(row_data)

                total_processed += 1
                if progress_callback:
                    progress_callback(total_processed, max_articles)
                    
            except Exception as e:
                print(f"跳过 {entry.link}: {e}")
    return rows

def main():
    if not models:
        print("错误：未找到任何模型！")
        return
        
    df_new = pd.DataFrame(fetch_news())
    
    if os.path.exists(OUTPUT):
        df_old = pd.read_excel(OUTPUT) if OUTPUT.endswith('xlsx') else pd.read_csv(OUTPUT)
        df_all = pd.concat([df_old, df_new]).drop_duplicates(subset=['标题'])
    else:
        df_all = df_new

    # 将所有模型的值转换为float类型
    for model_name in models.keys():
        if model_name in df_all.columns:
            df_all[model_name] = df_all[model_name].astype(float)
    
    if OUTPUT.endswith('xlsx'):
        df_all.to_excel(OUTPUT, index=False)
    else:
        df_all.to_csv(OUTPUT, index=False, encoding='utf-8-sig')
    print(f"已保存 {len(df_all)} 条新闻 → {OUTPUT}")

if __name__ == '__main__':
    main()