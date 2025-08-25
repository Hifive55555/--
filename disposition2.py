import math
def put(data):
    type_1=data['type_1']
    type_2=data['type_2']
    type_3=data['type_3']
    dir=data['dir']
    round_2_type_2=int((type_1+type_2)*0.5+0.9999)
    round_2_type_2=min(type_2,round_2_type_2)
    round_1_type=[]
    round_1_pos=[]
    round_2_type=[]
    round_2_pos=[]
    round_3_type=[]
    round_3_pos=[]
    if type_1+type_2-round_2_type_2==0:
        print("Error 1 !")
        return 
    turn=2*math.pi/(type_1+type_2-round_2_type_2)
    now_turn=dir
    if type_1%2==0:
        now_turn+=turn/2
    for i in range(type_1+type_2-round_2_type_2):
        if i>=type_1:
            round_1_type.append(2)
        else:
            round_1_type.append(1)
        round_1_pos.append(now_turn)
        now_turn+=turn
    round_3_type_3=int((type_3+round_2_type_2)*0.5+0.9999)
    round_3_type_3=min(round_3_type_3,type_3)
    if type_3+round_2_type_2-round_3_type_3==0:
        print("Error 2 !")
        return
    turn=2*math.pi/(type_3+round_2_type_2-round_3_type_3)
    now_turn=dir
    if round_2_type_2%2==0:
        now_turn+=turn/2
    for i in range(type_3+round_2_type_2-round_3_type_3):
        if i>=round_2_type_2:
            round_2_type.append(3)
        else:
            round_2_type.append(2)
        round_2_pos.append(now_turn)
        now_turn+=turn
    now_turn=dir
    if round_3_type_3==0:
        print("Error 3 !")
        return
    turn=2*math.pi/round_3_type_3
    if round_3_type_3%2==0:
        now_turn+=turn/2
    for i in range(round_3_type_3):
        round_3_type.append(3)
        round_3_pos.append(now_turn)
        now_turn+=turn
    return{
        'r1t': round_1_type,
        'r1p': round_1_pos,
        'r2t': round_2_type,
        'r2p': round_2_pos,
        'r3t': round_3_type,
        'r3p': round_3_pos
    }
def change_to_pos(dir,r):
    return{
        'x': math.cos(dir)*r,
        'y': math.sin(dir)*r
    }
def calculate(data):
    data = put(data)
    r1t=data['r1t']
    r1p=data['r1p']
    r2t=data['r2t']
    r2p=data['r2p']
    r3t=data['r3t']
    r3p=data['r3p']
    
    fino_tp=[]
    
    l=len(r1t)
    for i in range(l):
        fino_tp.append([str(r1t[i]),math.cos(r1p[i])*24,math.sin(r1p[i])*24])
    l=len(r2t)
    for i in range(l):
        fino_tp.append([str(r2t[i]),math.cos(r2p[i])*15,math.sin(r2p[i])*15])
    l=len(r3t)
    for i in range(l):
        fino_tp.append([str(r3t[i]),math.cos(r3p[i])*24,math.sin(r3p[i])*24])
    return fino_tp

print(calculate({'type_1':6,'type_2':6,'type_3':6,'dir':0}))