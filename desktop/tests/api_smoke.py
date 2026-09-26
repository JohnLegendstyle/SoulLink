"""Run only against an explicitly selected test server; creates one test room."""
import json
import sys
from urllib.request import Request,urlopen
from urllib.error import HTTPError

base=sys.argv[1].rstrip('/')
def call(path,method='GET',data=None,token=None):
    headers={'Content-Type':'application/json'}
    if token: headers['Authorization']='Bearer '+token
    request=Request(base+path,method=method,headers=headers,data=json.dumps(data).encode() if data is not None else None)
    with urlopen(request,timeout=10) as r: return json.load(r)
assert call('/health')['ok']
room=call('/api/room','POST',{})
try: call('/api/room?id='+room['id'])
except HTTPError as e: assert e.code==401
else: raise AssertionError('Room accepted an unauthenticated read')
def pokemon(uid):return {'uid':uid,'species':25,'nickname':'Test','level':5,'hp':20,'maxHp':20}
for role,uid in [('John','test-optimus'),('Eddie','test-bee')]:
    result=call('/api/sync','POST',{'roomId':room['id'],'sessionId':'test','sequence':0,'party':[pokemon(uid)],'owned':[pokemon(uid)],'fainted':[]},room[role])
dead=pokemon('test-optimus');dead['hp']=0
call('/api/sync','POST',{'roomId':room['id'],'sessionId':'test','sequence':1,'party':[dead],'owned':[dead],'fainted':['test-optimus']},room['John'])
result=call('/api/sync','POST',{'roomId':room['id'],'heartbeat':True},room['Eddie'])
assert result['blocked']==['test-bee'] and result['partnerOnline']
call('/api/room','PATCH',{'id':room['id'],'pair':0,'name':'Test-Paar'},room['readToken'])
state=call('/api/room?id='+room['id'],token=room['readToken'])['state']
assert state['names']['0']=='Test-Paar' and state['John']['dead']==['test-optimus']
print('PASS: health, authentication, both players, KO propagation, pair naming, persisted state')
