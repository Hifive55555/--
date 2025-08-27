import jieba
import json
import math

def text_to_wordlist(text):
    wordss=jieba.cut(text)
    words=set(wordss)
    return words
def train(train_data_news,train_data_labels):
    all_words=[]
    positive={}
    nagetive={}
    wordlist=[]
    total_train_data=0
    positive_data=0
    nagetive_data=0
    for news,label in zip(train_data_news,train_data_labels):
        total_train_data+=1
        if label==1:
            positive_data+=1
        else:
            nagetive_data+=1
        words=text_to_wordlist(news)
        for word in words:
            if word not in all_words:
                all_words.append(word)
            if label==1:
                positive[word]=positive.get(word,0)+1
                nagetive[word]=nagetive.get(word,0)+0
            else:
                positive[word]=positive.get(word,0)+0
                nagetive[word]=nagetive.get(word,0)+1
    for word in all_words:
        if abs(0.5-positive[word]/(positive[word]+nagetive[word]))>=0.01:
            wordlist.append(word)
    return {
        'wordlist': wordlist,
        'positive': positive,
        'nagetive': nagetive,
        'total_data': total_train_data,
        'positive_data': positive_data,
        'nagetive_data': nagetive_data
    }
def check(news,train_data):
    wordlist=train_data['wordlist']
    positive=train_data['positive']
    nagetive=train_data['nagetive']
    total_data=train_data['total_data']
    positive_data=train_data['positive_data']
    nagetive_data=train_data['nagetive_data']
    if total_data==0:
        print("Due to data lackage, unpredictable!\n")
        return 0.5
    p_positive=positive_data/total_data
    p_nagetive=nagetive_data/total_data
    words=text_to_wordlist(news)
    p_pos=0
    p_nag=0
    for word in words:
        if word in wordlist:
            p=(positive[word]+1)/(positive_data+len(wordlist))
            p_pos=p_pos+math.log10(p)
            p=(nagetive[word]+1)/(nagetive_data+len(wordlist))
            p_nag=p_nag+math.log10(p)
    p_pos=p_pos+math.log10(p_positive)
    p_nag=p_nag+math.log10(p_nagetive)
    p_pos=math.pow(10,p_pos)
    p_nag=math.pow(10,p_nag)
    if p_pos+p_nag==0:
        print("Unknown calculating mistake!\n")
        return 0.5
    return p_pos/(p_pos+p_nag)

def save(data, filename):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
def load(filename):
    with open(filename, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data

if __name__=="__main__":
    train_news = [
        "buy now get free money",
        "win big prizes click here",
        "hello how are you today",
        "meeting tomorrow at 3pm",
        "special offer for you",
        "your package has arrived"
    ]
    train_labels = [1, 1, 0, 0, 1, 0]
    train_result=train(train_news,train_labels)
    test_news = [
        "click here to get free money",
        "can we meet tomorrow?",
        "special offer for your package"
    ]

    save(train_result,"news.weight.json")
    tr=load("news.weight.json")
    for news in test_news:
        print(check(news,tr))
    print("lishof")
