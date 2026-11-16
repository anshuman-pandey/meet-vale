import tempfile,unittest
from pathlib import Path
from server import create_app
class HTTP(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.key='owner-key-for-http-tests-1234567890';self.app=create_app(str(Path(self.tmp.name)/'meet.db'),self.key,lambda:1794787200);self.c=self.app.test_client();self.owner={'Authorization':'Bearer '+self.key}
  self.body={'title':'Team <sync>','zone':'Europe/London','slots':[{'start':'2026-11-20T10:00:00+00:00','end':'2026-11-20T11:00:00+00:00'}]}
  r=self.c.post('/api/polls',json=self.body,headers=self.owner);self.assertEqual(r.status_code,201);self.poll=r.json;self.pid=r.json['id'];self.invite={'Authorization':'Bearer '+r.json['token']};self.url='/api/shared/'+self.pid
 def tearDown(self):self.tmp.cleanup()
 def join(self):
  r=self.c.post(self.url+'/participants',json={'name':'Ada','votes':['yes']},headers=self.invite);self.assertEqual(r.status_code,201);return r.json
 def test_owner_separation(self):
  for h in [{},self.invite,{'Authorization':'Bearer wrong'}]:
   self.assertEqual(self.c.get('/api/polls',headers=h).status_code,401)
   self.assertEqual(self.c.post('/api/polls',headers=h,json=self.body).status_code,401)
   self.assertEqual(self.c.post('/api/polls/'+self.pid+'/finalize',headers=h,json={'index':0}).status_code,401)
  self.assertEqual(self.c.get(self.url,headers=self.owner).status_code,401)
  self.assertEqual(self.c.get(self.url+'?token='+self.poll['token']).status_code,401)
 def test_full_flow(self):
  guest=self.join();path=self.url+'/participants/'+guest['id'];edit={'Authorization':'Bearer '+guest['token']}
  self.assertEqual(self.c.put(path,headers=edit,json={'votes':['maybe']}).status_code,200)
  self.assertEqual(self.c.get(self.url,headers=self.invite).json['counts'][0]['maybe'],1)
  self.assertEqual(self.c.post('/api/polls/'+self.pid+'/finalize',headers=self.owner,json={'index':0}).status_code,200)
  self.assertEqual(self.c.put(path,headers=edit,json={'votes':['no']}).status_code,400)
  r=self.c.get(self.url+'/calendar.ics',headers=self.invite);self.assertEqual(r.status_code,200);self.assertIn(b'DTSTART:20261120T100000Z',r.data);self.assertIn('attachment',r.headers['Content-Disposition']);self.assertEqual(r.headers['Cache-Control'],'no-store')
 def test_no_secret_leak(self):
  guest=self.join()
  for path,h in [('/api/polls',self.owner),('/api/polls/'+self.pid,self.owner),(self.url,self.invite)]:
   r=self.c.get(path,headers=h);self.assertEqual(r.status_code,200)
   for secret in [self.poll['token'],guest['token'],'Ada']:self.assertNotIn(secret,r.get_data(as_text=True))
 def test_guest_scope(self):
  guest=self.join();path=self.url+'/participants/'+guest['id']
  for h in [{},self.invite,self.owner]:self.assertEqual(self.c.put(path,headers=h,json={'votes':['no']}).status_code,400)
  other=self.c.post('/api/polls',headers=self.owner,json=self.body).json
  self.assertEqual(self.c.put('/api/shared/'+other['id']+'/participants/'+guest['id'],headers={'Authorization':'Bearer '+guest['token']},json={'votes':['no']}).status_code,400)
 def test_malformed_and_size(self):
  for value in [[],None,{'title':'X','zone':'UTC','slots':True}]:self.assertEqual(self.c.post('/api/polls',headers=self.owner,json=value).status_code in (400,415),True)
  self.assertEqual(self.c.post('/api/polls',headers=self.owner,data='{',content_type='application/json').status_code,400)
  self.assertEqual(self.c.post('/api/polls',headers=self.owner,data='x'*65537,content_type='application/json').status_code,413)
 def test_calendar_requires_final_and_invite(self):
  self.assertEqual(self.c.get(self.url+'/calendar.ics',headers=self.invite).status_code,400)
  self.assertEqual(self.c.get(self.url+'/calendar.ics').status_code,401)
 def test_final_index_validation(self):
  for value in [True,-1,1,None]:self.assertEqual(self.c.post('/api/polls/'+self.pid+'/finalize',headers=self.owner,json={'index':value}).status_code,400)
 def test_configuration(self):
  with self.assertRaises(ValueError):create_app(':memory:','short')
