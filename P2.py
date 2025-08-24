def train(samples,labels):
    positive_cnt=0
    nagetive_cnt=0
    positive=[{},{},{}]
    nagetive=[{},{},{}]
    dic=[set(),set(),set()]
    for sample,label in zip(samples,labels):
        if label==1:
            positive_cnt+=1
        else:
            nagetive_cnt+=1
        for i in range(3):
            feature=sample[i]
            dic[i].add(feature)
            if label==1:
                if feature in positive[i]:
                    positive[i][feature]+=1
                else:
                    positive[i][feature]=1
            else:
                if feature in nagetive[i]:
                    nagetive[i][feature]+=1
                else:
                    nagetive[i][feature]=1
    return {
        'positive_cnt': positive_cnt,
        'nagetive_cnt': nagetive_cnt,
        'dic': dic,
        'positive': positive,
        'nagetive': nagetive
    }
def check(target,modul):
    positive_cnt=modul['positive_cnt']
    nagetive_cnt=modul['nagetive_cnt']
    dic=modul['dic']
    positive=modul['positive']
    nagetive=modul['nagetive']
    total=positive_cnt+nagetive_cnt
    p_nagetive=1.0
    for i in range(3):
        cnt=nagetive[i].get(target[i],0)
        p=(cnt+1)/(nagetive_cnt+len(dic[i]))
        p_nagetive*=p
    
    p_positive=1.0
    for i in range(3):
        cnt=positive[i].get(target[i],0)
        p=(cnt+1)/(positive_cnt+len(dic[i]))
        p_positive*=p

    P_positive=positive_cnt/total
    P_nagetive=nagetive_cnt/total
    P=P_positive*p_positive+P_nagetive*p_nagetive
    #print(p_nagetive/P)
    #return 1-(p_nagetive/P)
    

    return 1-P_nagetive*p_nagetive/P
if __name__=="__main__":
    train_samples=[
        ["15:00","A class","port 000"],
        ["15:05","B class","port 002"],
        ["15:10","A class","port 001"],
        ["15:15","B class","port 001"],
        ["15:46","A class","port 000"],
        ["15:30","A class","port 002"],
        ["15:13","C class","port 000"],
        ["15:17","A class","port 001"],
        ["15:19","B class","port 001"],
        ["15:46","A class","port 002"],
        ["15:05","B class","port 002"],
        ["15:10","A class","port 001"],
        ["15:15","B class","port 001"],
        ["15:46","A class","port 000"],
        ["15:30","A class","port 002"],
        ["15:13","C class","port 000"],
        ["15:17","A class","port 001"],
        ["15:19","B class","port 001"],
        ["15:46","A class","port 002"]
    ]
    train_labels=[1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]

    model=train(train_samples,train_labels)
    
    test=[
        ["15:20","A class","port 002"],
        ["15:15","C class","port 000"],
        ["15:13","B class","port 001"],
    ]

    for sample in test:
        print(check(sample,model))