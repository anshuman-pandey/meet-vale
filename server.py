"""Authenticated local HTTP preview. No public deployment configured."""
import hmac,os,sqlite3,time
from flask import Flask,g,request,jsonify,abort,Response
from werkzeug.exceptions import HTTPException
from polls import Polls,Invalid

def create_app(path,owner_key,clock=time.time):
    if not isinstance(owner_key,str) or not owner_key.isascii() or len(owner_key)<32:raise ValueError('Set MEET_OWNER_KEY to at least 32 random ASCII characters.')
    app=Flask(__name__,static_folder=None);app.config['MAX_CONTENT_LENGTH']=65536
    def db():
        if 'db' not in g:g.db=Polls(path,clock)
        return g.db
    def token():
        auth=request.headers.get('Authorization','');return auth[7:] if auth.startswith('Bearer ') else ''
    def owner():
        if not hmac.compare_digest(token().encode(),owner_key.encode()):abort(401,description='Owner access denied.')
    def shared(pid):
        try:return db().view(pid,token())
        except Invalid:abort(401,description='Poll access denied.')
    def body():
        value=request.get_json()
        if not isinstance(value,dict):raise Invalid('Expected a JSON object.')
        return value
    @app.teardown_appcontext
    def close(error):
        store=g.pop('db',None)
        if store:store.close()
    @app.after_request
    def headers(r):
        r.headers.update({'Cache-Control':'no-store','X-Content-Type-Options':'nosniff','Referrer-Policy':'no-referrer','Content-Security-Policy':"default-src 'none'; frame-ancestors 'none'; base-uri 'none'"});return r
    @app.errorhandler(Invalid)
    def invalid(e):return jsonify(error=str(e)),400
    @app.errorhandler(HTTPException)
    def http_error(e):return jsonify(error=e.description),e.code
    @app.errorhandler(sqlite3.OperationalError)
    def storage(e):return jsonify(error='Storage unavailable. Please retry.'),503
    @app.get('/api/polls')
    def listing():
        owner();return jsonify([dict(r) for r in db().db.execute('SELECT id,title,zone,final FROM polls ORDER BY rowid DESC')])
    @app.post('/api/polls')
    def create():
        owner();b=body();return jsonify(db().create(b.get('title'),b.get('zone'),b.get('slots'))),201
    @app.get('/api/polls/<pid>')
    def report(pid):owner();return jsonify(db().report(pid))
    @app.post('/api/polls/<pid>/finalize')
    def finalize(pid):
        owner();b=body();db().finalize(pid,b.get('index'));return jsonify(ok=True)
    @app.get('/api/shared/<pid>')
    def view(pid):return jsonify(shared(pid))
    @app.post('/api/shared/<pid>/participants')
    def join(pid):
        shared(pid);b=body();return jsonify(db().join(pid,token(),b.get('name'),b.get('votes'))),201
    @app.put('/api/shared/<pid>/participants/<gid>')
    def vote(pid,gid):
        b=body();db().vote(pid,gid,token(),b.get('votes'));return jsonify(ok=True)
    @app.get('/api/shared/<pid>/calendar.ics')
    def calendar(pid):
        shared(pid);return Response(db().calendar(pid,token()),mimetype='text/calendar',headers={'Content-Disposition':'attachment; filename="meeting.ics"'})
    return app
if __name__=='__main__':
    os.umask(0o077)
    create_app(os.environ.get('MEET_DATABASE','meet.sqlite3'),os.environ.get('MEET_OWNER_KEY','')).run(host='127.0.0.1',port=8102)
