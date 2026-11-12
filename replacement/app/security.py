import hashlib,hmac,secrets,time
from functools import wraps
from flask import request,session,abort,redirect,url_for,g,current_app
from .db import get_db,audit

def csrf_token():
    if 'csrf' not in session:session['csrf']=secrets.token_urlsafe(32)
    return session['csrf']
def require_csrf():
    if request.method in ('POST','PUT','PATCH','DELETE'):
        if request.headers.get('Origin') and request.headers['Origin']!=request.host_url.rstrip('/'):abort(403)
        if request.headers.get('Sec-Fetch-Site')=='cross-site':abort(403)
        token=request.form.get('csrf_token','')
        if not token or not hmac.compare_digest(token,session.get('csrf','')):abort(403)
def rate_limit(scope,maximum,seconds=600):
    key=hmac.new(current_app.secret_key,(scope+':'+(request.remote_addr or '')).encode(),hashlib.sha256).hexdigest();bucket=int(time.time())//seconds;db=get_db()
    with db:
        db.execute('INSERT INTO limits(key,bucket,hits) VALUES(?,?,1) ON CONFLICT(key,bucket) DO UPDATE SET hits=hits+1',(key,bucket))
        hits=db.execute('SELECT hits FROM limits WHERE key=? AND bucket=?',(key,bucket)).fetchone()['hits']
    if hits>maximum:abort(429)
def load_user():
    g.user=None;token=session.get('admin_token')
    if token:
        g.user=get_db().execute('SELECT u.id,u.username FROM sessions s JOIN users u ON u.id=s.user_id WHERE s.token_hash=? AND s.expires>?',(hashlib.sha256(token.encode()).hexdigest(),int(time.time()))).fetchone()
def login_required(fn):
    @wraps(fn)
    def wrapped(*a,**kw):
        if not g.user:return redirect(url_for('auth.login'))
        return fn(*a,**kw)
    return wrapped
