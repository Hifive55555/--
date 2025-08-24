import math
def gcd(a,b):
    while b:
        a,b=b,a%b
    return a
def test():
    return{
        'self_ship_list': {'1':3,'2':2,'3':10,'4':0},
        'self_r': {'1':2,'2':3,'3':4,'4':1},
        'ship_dic': ['1','2','3','4']
    }
def PUT(info):
    self_ship=info['self_ship_list']
    self_r=info['self_r']
    ship_dic=info['ship_dic']
    total_len=0
    c=1
    left_ship=0
    ship_count={}
    for ship in ship_dic:
        total_len+=self_r[ship]*self_ship[ship]*2
        if self_ship[ship]!=0:
            c*=self_ship[ship]/gcd(c,self_ship[ship])
        left_ship+=self_ship[ship]
        ship_count[ship]=ship_count.get(ship,0)
    try_put_max_range_typ=[]
    try_put_max_range_ang=[]
    last_angle=0
    last_r=0
    jsh=0
    round_typ=[[],[],[]]
    round_pos=[[],[],[]]
    cnt=left_ship
    while left_ship>0:
        for ship in ship_dic:
            if ship_count[ship]>=c and self_ship[ship]>0:
                self_ship[ship]-=1
                left_ship-=1
                try_put_max_range_typ.append(ship)
                round_typ[jsh%3].append(ship)
                if last_angle!=0 and last_r!=0:
                    last_r+=self_r[ship]
                last_angle+=360*last_r/total_len
                try_put_max_range_ang.append(last_angle)
                round_pos[jsh%3].append(last_angle)
                last_r=self_r[ship]
                ship_count[ship]-=c
                jsh+=1
            ship_count[ship]+=self_ship[ship]
    return{
        #'round_pos': round_pos,
        #'round_typ': round_typ
        'round_pos': try_put_max_range_ang,
        'round_typ': try_put_max_range_typ,
        'cnt': cnt
    }
def put_into_cell(info):
    round_pos=info['round_pos']
    round_typ=info['round_typ']
    ranges=[6,12,24]
    fino=[]
    l=info['cnt']
    for i in range(l):
        fino.append([round_typ[i],ranges[i%3]*math.cos(round_pos[i]/360*2*math.pi),ranges[i%3]*math.sin(round_pos[i]/360*2*math.pi)])
    return fino
def calculate(data: dict):
    return put_into_cell(PUT(data))

if __name__=="__main__":
    print(calculate(test()))

