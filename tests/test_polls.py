import tempfile,unittest
from pathlib import Path
from polls import Polls,Invalid,instant
class Scheduling(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.now=1794787200;self.path=str(Path(self.tmp.name)/'poll.sqlite3');self.p=Polls(self.path,lambda:self.now)
  self.slots=[{'start':'2026-11-20T10:00:00+00:00','end':'2026-11-20T11:00:00+00:00'}];self.poll=self.p.create('Team, review; Q4','Europe/London',self.slots)
 def tearDown(self):self.p.close();self.tmp.cleanup()
 def view(self):return self.p.view(self.poll['id'],self.poll['token'])
 def test_vote_update_counts(self):
  g=self.p.join(self.poll['id'],self.poll['token'],'Ada',['yes']);self.assertEqual(self.view()['counts'],[{'yes':1,'maybe':0,'no':0}]);self.p.vote(self.poll['id'],g['id'],g['token'],['maybe']);self.assertEqual(self.view()['counts'][0]['yes'],0);self.assertEqual(self.view()['counts'][0]['maybe'],1)
 def test_credentials(self):
  for token in [None,'',False,'wrong']:
   with self.assertRaises(Invalid):self.p.view(self.poll['id'],token)
   with self.assertRaises(Invalid):self.p.join(self.poll['id'],token,'Ada',['yes'])
 def test_guest_scope(self):
  g=self.p.join(self.poll['id'],self.poll['token'],'Ada',['yes']);other=self.p.create('Other','Europe/London',self.slots)
  with self.assertRaises(Invalid):self.p.vote(other['id'],g['id'],g['token'],['no'])
  with self.assertRaises(Invalid):self.p.vote(self.poll['id'],g['id'],'bad',['no'])
 def test_atomic_validation(self):
  for votes in [[],['bad'],[True],['yes','no']]:
   with self.assertRaises(Invalid):self.p.join(self.poll['id'],self.poll['token'],'Ada',votes)
  self.assertEqual(self.view()['counts'][0]['yes'],0)
 def test_finalize_freezes(self):
  g=self.p.join(self.poll['id'],self.poll['token'],'Ada',['yes']);self.p.finalize(self.poll['id'],0)
  with self.assertRaises(Invalid):self.p.vote(self.poll['id'],g['id'],g['token'],['no'])
  with self.assertRaises(Invalid):self.p.join(self.poll['id'],self.poll['token'],'Bob',['yes'])
  with self.assertRaises(Invalid):self.p.finalize(self.poll['id'],0)
 def test_calendar(self):
  with self.assertRaises(Invalid):self.p.calendar(self.poll['id'],self.poll['token'])
  self.p.finalize(self.poll['id'],0);data=self.p.calendar(self.poll['id'],self.poll['token']);self.assertIn(b'DTSTART:20261120T100000Z\r\n',data);self.assertIn(b'SUMMARY:Team\\, review\\; Q4',data);self.assertEqual(data,self.p.calendar(self.poll['id'],self.poll['token']))
 def test_dst(self):
  with self.assertRaises(Invalid):instant('2027-03-14T02:30:00-05:00','America/New_York')
  a=instant('2026-11-01T01:30:00-04:00','America/New_York');b=instant('2026-11-01T01:30:00-05:00','America/New_York');self.assertEqual(b-a,3600)
  with self.assertRaises(Invalid):instant('2026-11-01T01:30:00','America/New_York')
 def test_bad_slots(self):
  for slots in [[],self.slots*2,[{'start':'bad','end':'bad'}]]:
   with self.assertRaises(Invalid):self.p.create('X','UTC',slots)
  with self.assertRaises(Invalid):self.p.create('X','No/Zone',self.slots)
 def test_calendar_utf8_folding(self):
  poll=self.p.create('会議'*60,'Europe/London',self.slots);self.p.finalize(poll['id'],0);data=self.p.calendar(poll['id'],poll['token']);self.assertTrue(all(len(line)<=75 for line in data.split(b'\r\n')));self.assertIn(('SUMMARY:'+'会議'*60).encode(),data.replace(b'\r\n ',b''))
 def test_persistence_and_secrets(self):
  self.p.join(self.poll['id'],self.poll['token'],'Ada',['yes']);self.p.finalize(self.poll['id'],0);self.p.close();self.p=Polls(self.path,lambda:self.now);self.assertEqual(self.view()['final'],0);self.assertEqual(self.view()['counts'][0]['yes'],1);self.assertNotIn(self.poll['token'],self.p.db.execute('SELECT invite FROM polls').fetchone()[0])
 def test_past_final_rejected(self):
  self.now=instant('2026-11-20T10:00:00+00:00','Europe/London')
  with self.assertRaises(Invalid):self.p.finalize(self.poll['id'],0)
 def test_control_injection(self):
  with self.assertRaises(Invalid):self.p.create('Title\r\nATTENDEE:evil','UTC',self.slots)
if __name__=='__main__':unittest.main()
