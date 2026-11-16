"""Scheduling domain; owner methods require authentication at the service boundary."""
import hashlib,hmac,json,secrets,sqlite3,time,unicodedata
from datetime import datetime,timezone
from zoneinfo import ZoneInfo,ZoneInfoNotFoundError
class Invalid(ValueError):pass

def text(value,limit):
    if not isinstance(value,str) or not value.strip() or len(value)>limit or any(unicodedata.category(c).startswith('C') for c in value):raise Invalid('Use nonempty text without control characters.')
    return value.strip()
def digest(token):
    if not isinstance(token,str):raise Invalid('Access denied.')
    return hashlib.sha256(token.encode()).hexdigest()
def instant(value,zone):
    try:
        dt=datetime.fromisoformat(value)
        if dt.tzinfo is None or dt.second or dt.microsecond:raise ValueError()
        local=dt.astimezone(ZoneInfo(zone))
        if local.replace(tzinfo=None)!=dt.replace(tzinfo=None) or local.utcoffset()!=dt.utcoffset():raise ValueError()
        return int(dt.timestamp())
    except (ValueError,TypeError,ZoneInfoNotFoundError,OverflowError):raise Invalid('Use a valid local minute with an explicit UTC offset matching the selected timezone.')
def fold(line):
    chunks=[];part=''
    for c in line:
        if len((part+c).encode())>75:chunks.append(part);part=' '
        part+=c
    return '\r\n'.join(chunks+[part])
def escape(value):return value.replace('\\','\\\\').replace(';','\\;').replace(',','\\,')
class Polls:
    def __init__(self,path,clock=time.time):
        self.clock=clock;self.db=sqlite3.connect(path);self.db.row_factory=sqlite3.Row
        self.db.execute('PRAGMA foreign_keys=ON')
        self.db.executescript('''CREATE TABLE IF NOT EXISTS polls(id TEXT PRIMARY KEY,title TEXT NOT NULL,zone TEXT NOT NULL,slots TEXT NOT NULL,invite TEXT NOT NULL,final INTEGER,created INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS guests(id TEXT PRIMARY KEY,poll TEXT NOT NULL REFERENCES polls(id),name TEXT NOT NULL,secret TEXT NOT NULL,votes TEXT NOT NULL);''')
    def close(self):self.db.close()
    def create(self,title,zone,slots):
        title=text(title,200)
        if not isinstance(slots,list) or not 1<=len(slots)<=20:raise Invalid('Choose 1 to 20 slots.')
        normalized=[]
        for slot in slots:
            if not isinstance(slot,dict):raise Invalid('Invalid slot.')
            start=instant(slot.get('start'),zone);end=instant(slot.get('end'),zone)
            if not self.clock()<start<=self.clock()+366*86400 or not 300<=end-start<=43200:raise Invalid('Slots must start within 366 days and last 5 minutes to 12 hours.')
            normalized.append([start,end])
        if len({tuple(s) for s in normalized})!=len(normalized):raise Invalid('Duplicate slot.')
        token=secrets.token_urlsafe(32);pid=secrets.token_urlsafe(16)
        with self.db:
            self.db.execute('BEGIN IMMEDIATE')
            if self.db.execute('SELECT count(*) FROM polls').fetchone()[0]>=200:raise Invalid('Poll limit reached.')
            self.db.execute('INSERT INTO polls VALUES(?,?,?,?,?,NULL,?)',(pid,title,zone,json.dumps(normalized),digest(token),int(self.clock())))
        return {'id':pid,'token':token}
    def _poll(self,pid,token=None):
        row=self.db.execute('SELECT * FROM polls WHERE id=?',(pid,)).fetchone()
        if not row or (token is not None and not hmac.compare_digest(row['invite'],digest(token))):raise Invalid('Poll unavailable.')
        return row
    def view(self,pid,token):
        digest(token);r=self._poll(pid,token)
        slots=json.loads(r['slots']);counts=[{'yes':0,'maybe':0,'no':0} for _ in slots]
        for row in self.db.execute('SELECT votes FROM guests WHERE poll=?',(pid,)):
            for i,v in enumerate(json.loads(row['votes'])):counts[i][v]+=1
        return {'id':pid,'title':r['title'],'zone':r['zone'],'slots':slots,'counts':counts,'final':r['final']}
    def _votes(self,votes,n):
        if not isinstance(votes,list) or len(votes)!=n or any(type(v) is not str or v not in ('yes','maybe','no') for v in votes):raise Invalid('Answer every slot with yes, maybe or no.')
        return json.dumps(votes)
    def join(self,pid,invite,name,votes):
        name=text(name,80);digest(invite)
        with self.db:
            self.db.execute('BEGIN IMMEDIATE');r=self._poll(pid,invite)
            if r['final'] is not None:raise Invalid('Poll is finalized.')
            encoded=self._votes(votes,len(json.loads(r['slots'])))
            if self.db.execute('SELECT count(*) FROM guests WHERE poll=?',(pid,)).fetchone()[0]>=100:raise Invalid('Participant limit reached.')
            gid=secrets.token_urlsafe(16);token=secrets.token_urlsafe(32)
            self.db.execute('INSERT INTO guests VALUES(?,?,?,?,?)',(gid,pid,name,digest(token),encoded))
        return {'id':gid,'token':token}
    def vote(self,pid,gid,token,votes):
        with self.db:
            self.db.execute('BEGIN IMMEDIATE');r=self._poll(pid)
            guest=self.db.execute('SELECT * FROM guests WHERE id=? AND poll=?',(gid,pid)).fetchone()
            if not guest or not hmac.compare_digest(guest['secret'],digest(token)):raise Invalid('Participant access denied.')
            if r['final'] is not None:raise Invalid('Poll is finalized.')
            self.db.execute('UPDATE guests SET votes=? WHERE id=?',(self._votes(votes,len(json.loads(r['slots']))),gid))
    def finalize(self,pid,index):
        with self.db:
            self.db.execute('BEGIN IMMEDIATE');r=self._poll(pid)
            if r['final'] is not None:raise Invalid('Poll is already finalized.')
            if type(index) is not int or not 0<=index<len(json.loads(r['slots'])):raise Invalid('Choose an existing slot.')
            if json.loads(r['slots'])[index][0]<=self.clock():raise Invalid('Choose a future slot.')
            self.db.execute('UPDATE polls SET final=? WHERE id=?',(index,pid))
    def calendar(self,pid,token):
        view=self.view(pid,token)
        if view['final'] is None:raise Invalid('Finalize the poll before calendar export.')
        start,end=view['slots'][view['final']];stamp=lambda t:datetime.fromtimestamp(t,timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        created=self._poll(pid)['created']
        lines=['BEGIN:VCALENDAR','VERSION:2.0','PRODID:-//Meet Vale//Local Preview//EN','CALSCALE:GREGORIAN','BEGIN:VEVENT','UID:'+pid+'@meet-vale.local','DTSTAMP:'+stamp(created),'DTSTART:'+stamp(start),'DTEND:'+stamp(end),'SUMMARY:'+escape(view['title']),'END:VEVENT','END:VCALENDAR']
        return ('\r\n'.join(fold(line) for line in lines)+'\r\n').encode()
