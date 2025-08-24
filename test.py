import feedparser
from newspaper import Article

url = 'https://rss.aishort.top/?type=cneb'
feed = feedparser.parse(url)
print('RSS 条目数:', len(feed.entries))

for entry in feed.entries[:3]:
    try:
        a = Article(entry.link, language='zh', memoize_articles=False)
        a.download()
        a.parse()
        print('标题:', a.title)
        print('时间:', a.publish_date)
        print('正文前 50 字:', a.text[:50])
        print('-'*30)
    except Exception as e:
        print('出错:', e)