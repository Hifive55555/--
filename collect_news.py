import feedparser
from newspaper import Article
import pandas as pd
import os
from classifier import load, check
from typing import Callable

train_result = load('news.weight.json')

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
                article = Article(entry.link, language='zh')  # 中文优先
                article.download()
                article.parse()
                if not article.text:
                    continue
                content = article.text.strip().replace('\n', ' ')
                check_value = check(content, train_result)

                rows.append({
                    '时间': article.publish_date.strftime('%Y-%m-%d %H:%M') if article.publish_date else '',
                    '标题': article.title or entry.title,
                    '内容': content,
                    '值': f'{check_value:.4f}',
                })

                total_processed += 1
                if progress_callback:
                    progress_callback(total_processed, max_articles)
                    
                print(f"处理文章: {article.title} - 值: {check_value}")
            except Exception as e:
                print(f"跳过 {entry.link}: {e}")
    return rows

def main():
    df_new = pd.DataFrame(fetch_news())
    # print(df_new[['标题', '值']].head())  # 打印前几行数据查看值是否正确
    
    # df_new['值'] = df_new['值'].astype(float)
    if os.path.exists(OUTPUT):
        df_old = pd.read_excel(OUTPUT) if OUTPUT.endswith('xlsx') else pd.read_csv(OUTPUT)
        df_all = pd.concat([df_old, df_new]).drop_duplicates(subset=['标题'])
    else:
        df_all = df_new
    if OUTPUT.endswith('xlsx'):
        df_all.to_excel(OUTPUT, index=False)
    else:
        df_all.to_csv(OUTPUT, index=False, encoding='utf-8-sig')
    print(f"已保存 {len(df_all)} 条新闻 → {OUTPUT}")

if __name__ == '__main__':
    main()