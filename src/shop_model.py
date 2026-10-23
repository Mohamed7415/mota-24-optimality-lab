"""Pure rules of the six pinned original shop routines; integer resource domain.
A resource-changing transaction strictly decreases rank(potential, cash).
Identity actions (failure/exit/navigation) are abstracted away.
"""
import copy
FIELDS=['Now_hp','Now_gong','Now_fang','Now_life','Now_yellow','Now_blue','Now_red','Now_money','Now_mp']
COSTS={1:[25,25,25],2:[100,100,100],3:[10,50,100],4:[1,1,1],5:[100,30,30],6:[270,95,95]}

def potential(s):return s['Now_money']+10*s['Now_yellow']+50*s['Now_blue']+100*s['Now_red']+s['Now_mp']
def rank(s):
    p=potential(s);return p*(p+1)//2+s['Now_money']

def transact(s,shop,choice):
    if shop not in COSTS or choice not in [1,2,3,4]:raise ValueError('Shop or choice')
    if any(not isinstance(s[k],int) or s[k]<0 for k in FIELDS):raise ValueError('Nonnegative integer resources required')
    r=copy.deepcopy(s)
    if choice==4:return r
    cost=COSTS[shop][choice-1]
    source='Now_money' if shop<=3 else ['Now_yellow','Now_blue','Now_red'][choice-1] if shop==4 else 'Now_mp'
    if r[source]<cost:return r
    r[source]-=cost
    if shop in [1,2]:
        key=['Now_hp','Now_gong','Now_fang'][choice-1]
        r[key]+={1:[800,4,4],2:[4000,20,20]}[shop][choice-1]
    elif shop==3:r[['Now_yellow','Now_blue','Now_red'][choice-1]]+=1
    elif shop==4:r['Now_money']+=[7,35,70][choice-1]
    elif choice==1:
        for key,delta in zip(['Now_life','Now_hp','Now_gong','Now_fang'],[1,1000,7,7] if shop==5 else [3,3000,20,20]):r[key]+=delta
    else:r[['Now_gong','Now_fang'][choice-2]]+=5 if shop==5 else 17
    if rank(r)>=rank(s):raise AssertionError('Shop rank must strictly decrease')
    return r
