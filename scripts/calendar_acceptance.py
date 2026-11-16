"""Import actual Meet Vale exports into an isolated Khal calendar; never user calendars."""
import os,subprocess,sys,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from polls import Polls
khal=os.environ.get('KHAL','khal')
with tempfile.TemporaryDirectory(prefix='meet-calendar-') as tmp:
    root=Path(tmp);calendar=root/'calendar';calendar.mkdir()
    config=root/'config'
    config.write_text(f'''[calendars]
[[acceptance]]
path = {calendar}
type = calendar
[locale]
timeformat = %H:%M
dateformat = %Y-%m-%d
longdateformat = %Y-%m-%d
datetimeformat = %Y-%m-%d %H:%M
longdatetimeformat = %Y-%m-%d %H:%M
local_timezone = UTC
default_timezone = UTC
[sqlite]
path = {root / 'calendar.db'}
[default]
default_calendar = acceptance
''')
    env={**os.environ,'XDG_CONFIG_HOME':str(root/'config-home'),'XDG_DATA_HOME':str(root/'data-home'),'XDG_CACHE_HOME':str(root/'cache-home'),'TZ':'UTC'}
    def run(*args):return subprocess.check_output([khal,'-c',str(config),*args],env=env,text=True,stderr=subprocess.STDOUT)
    polls=Polls(str(root/'polls.db'),clock=lambda:1790812800)
    title='会議, review; path\\notes '+('長い議題'*25)
    exports=[]
    for offset in ['-04:00','-05:00']:
        poll=polls.create(title+offset,'America/New_York',[{'start':'2026-11-01T01:00:00'+offset,'end':'2026-11-01T01:30:00'+offset}])
        polls.finalize(poll['id'],0);path=root/(poll['id']+'.ics');path.write_bytes(polls.calendar(poll['id'],poll['token']));exports.append(path)
        run('import','--batch','-a','acceptance',str(path))
    # Re-import retains stable UID and updates the same event, rather than duplicating it.
    run('import','--batch','-a','acceptance',str(exports[0]))
    output=run('list','2026-11-01','2026-11-02','--format','{start} | {end} | {title}','--day-format','')
    assert title+'-04:00' in output,output
    assert title+'-05:00' in output,output
    assert '05:00' in output and '05:30' in output and '06:00' in output and '06:30' in output,output
    assert output.count(title)==2,output
    assert len(list(calendar.glob('*.ics')))==2
    polls.close()
    print(run('--version').strip())
    print('PASS: actual Khal import preserves Unicode, escaped text, repeated-hour distinct UTC times and stable UID on re-import; isolated calendar removed')
