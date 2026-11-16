"""Disposable scheduling deployment and backup recovery acceptance."""
import json,secrets,subprocess,tempfile,time,urllib.request,urllib.error
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
name='meet-test-'+secrets.token_hex(5);volume=name+'-data';restored=name+'-restore';key=secrets.token_urlsafe(32);image='meet-vale-acceptance:local'
def docker(*args):return subprocess.check_output(['docker',*args],text=True).strip()
def call(base,path,token=key,data=None,method=None):
 raw=json.dumps(data).encode() if data is not None else None
 headers={'Authorization':'Bearer '+token}
 if raw:headers['Content-Type']='application/json'
 with urllib.request.urlopen(urllib.request.Request(base+path,data=raw,headers=headers,method=method),timeout=10) as r:return json.load(r)
def denied(base,path,token):
 try:call(base,path,token);raise AssertionError('Revoked access worked')
 except urllib.error.HTTPError as e:assert e.code==401

def ready(container):
 base='http://127.0.0.1:'+docker('port',container,'8102/tcp').rsplit(':',1)[1]
 for _ in range(100):
  try:
   with urllib.request.urlopen(base,timeout=1) as r:
    if r.status==200:return base
  except (OSError,urllib.error.URLError):time.sleep(.1)
 raise RuntimeError('Service failed to start')
def start(container,vol):
 docker('run','-d','--name',container,'--read-only','--tmpfs','/tmp:size=32m','--cap-drop=ALL','--security-opt=no-new-privileges:true','-e','MEET_OWNER_KEY='+key,'-v',vol+':/data','-p','127.0.0.1::8102',image)
 return ready(container)
try:
 base=start(name,volume);assert docker('exec',name,'id','-u')=='10001'
 from datetime import datetime,timezone,timedelta
 begin=datetime.now(timezone.utc).replace(second=0,microsecond=0)+timedelta(days=7)
 body={'title':'Recovery meeting','zone':'UTC','slots':[{'start':begin.isoformat(),'end':(begin+timedelta(hours=1)).isoformat()}]}
 finalized=call(base,'/api/polls',data=body);active=call(base,'/api/polls',data=body)
 finalpath='/api/shared/'+finalized['id'];activepath='/api/shared/'+active['id']
 guest=call(base,finalpath+'/participants',finalized['token'],{'name':'Ada','votes':['yes']})
 editable=call(base,activepath+'/participants',active['token'],{'name':'Lin','votes':['maybe']})
 call(base,'/api/polls/'+finalized['id']+'/finalize',data={'index':0})
 def calendar(base):
  with urllib.request.urlopen(urllib.request.Request(base+finalpath+'/calendar.ics',headers={'Authorization':'Bearer '+finalized['token']})) as r:return r.read()
 original=calendar(base)
 def check(base):
  assert call(base,finalpath,finalized['token'])['final']==0
  assert call(base,finalpath,finalized['token'])['counts'][0]['yes']==1
  assert calendar(base)==original
  denied(base,finalpath,'wrong')
  try:call(base,finalpath+'/participants/'+guest['id'],guest['token'],{'votes':['no']},'PUT');raise AssertionError('Final vote changed')
  except urllib.error.HTTPError as e:assert e.code==400
 docker('restart','-t','1',name);base=ready(name);check(base)
 docker('stop','-t','1',name)
 with tempfile.TemporaryDirectory() as tmp:
  source=Path(tmp)/'source.sqlite3';backup=Path(tmp)/'backup.sqlite3';docker('cp',name+':/data/meet.sqlite3',str(source))
  subprocess.run(['python3',str(ROOT/'scripts/backup.py'),str(source),str(backup)],check=True);assert backup.stat().st_mode & 0o777==0o600
  assert subprocess.run(['python3',str(ROOT/'scripts/backup.py'),str(source),str(backup)],capture_output=True).returncode!=0
  docker('volume','create',restored)
  docker('run','--rm','--user','0','-v',restored+':/data','-v',str(backup)+':/backup:ro',image,'python','-c',"import shutil,os;shutil.copyfile('/backup','/data/meet.sqlite3');os.chown('/data/meet.sqlite3',10001,10001);os.chmod('/data/meet.sqlite3',0o600);os.chown('/data',10001,10001)")
  base=start(name+'-restored',restored);check(base)
  call(base,activepath+'/participants/'+editable['id'],editable['token'],{'votes':['yes']},'PUT')
  assert call(base,activepath,active['token'])['counts'][0]['yes']==1
  call(base,'/api/polls/'+active['id']+'/finalize',data={'index':0})
  assert call(base,activepath,active['token'])['final']==0
  assert call(base,'/api/polls',data=body)['id']
 print('PASS: non-root/read-only service; votes, finalization, credentials and exact ICS survive restart/clean-volume restore; fresh updates/finalization/polls work')

finally:
 for container in (name,name+'-restored'):subprocess.run(['docker','rm','-f',container],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 for vol in (volume,restored):subprocess.run(['docker','volume','rm',vol],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
