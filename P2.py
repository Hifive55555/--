import math
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
                positive[i][feature]=positive[i].get(feature,0)+1
                nagetive[i][feature]=nagetive[i].get(feature,0)
            else:
                positive[i][feature]=positive[i].get(feature,0)
                nagetive[i][feature]=nagetive[i].get(feature,0)+1
    Dic=[set(),set(),set()]
    for i in range(3):
        for feature in dic[i]:
            if abs(positive[i].get(feature,0)-nagetive[i].get(feature,0))/(positive[i].get(feature,0)+nagetive[i].get(feature,0))>=0.001:
                Dic[i].add(feature)
    dic=Dic
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
    p_nagetive=0
    for i in range(3):
        if target[i] in dic[i]:
            cnt=nagetive[i].get(target[i],0)
            p=(cnt+1)/(nagetive_cnt+len(dic[i]))
            p_nagetive+=math.log10(p)
    p_positive=0
    for i in range(3):
        if target[i] in dic[i]:
            cnt=positive[i].get(target[i],0)
            p=(cnt+1)/(positive_cnt+len(dic[i]))
            p_positive+=math.log10(p)
    P_positive=positive_cnt/total
    P_nagetive=nagetive_cnt/total
    p_nagetive=pow(10,p_nagetive)
    p_positive=pow(10,p_positive)
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