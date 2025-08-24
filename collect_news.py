import feedparser
from newspaper import Article
import pandas as pd
import os
from classifier import train, check

train_news = [
        "攻击黄岩岛",
        "黄岩岛在24海里处遭受袭击，新闻2024年",
        "网红打卡地",
        "这一点也不好玩，美妆博主",
        "岛屿遭受攻击，联合国发表说明",
        "坚决捍卫我国领土完整",
        "2025年10月，王源死了，入狱罚金1000万"
    ]
train_labels = [1, 1, 0, 0, 1, 1, 0]
train_result = train(train_news, train_labels)

# 1) 配置：RSS 源可任意增删
RSS_URLS = [
    'https://rss.aishort.top/?type=cneb',
]

OUTPUT = 'news.xlsx'   # 也可改成 .csv
MAX_ARTICLES = 50     # 每次最多抓多少条

def fetch_news():
    rows = []
    for rss in RSS_URLS:
        feed = feedparser.parse(rss)
        for entry in feed.entries[:MAX_ARTICLES]:
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