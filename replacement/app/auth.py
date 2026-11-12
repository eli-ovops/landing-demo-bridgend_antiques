import secrets,time,hashlib,sqlite3
from flask import Blueprint,request,render_template,session,redirect,url_for,flash,current_app,abort
from werkzeug.security import generate_password_hash,check_password_hash
from .db import get_db,audit
from .security import rate_limit,login_required
bp=Blueprint('auth',__name__)
@bp.route('/admin/setup',methods=['GET','POST'])
def setup():
    db=get_db()
    if db.execute('SELECT count(*) n FROM users').fetchone()['n']:return redirect(url_for('auth.login'))
    if not current_app.config['ALLOW_SETUP'] or request.remote_addr not in ('127.0.0.1','::1'):abort(403)
    if request.method=='POST':
        rate_limit('setup',5);user=request.form.get('username','').strip();pw=request.form.get('password','')
        if not 3<=len(user)<=64 or len(pw)<14 or len(pw)>256 or pw!=request.form.get('confirm'):
            flash('Use a username of 3–64 characters and matching passwords of at least 14 characters.','error')
        else:
            with db:
                db.execute('BEGIN IMMEDIATE')
                if db.execute('SELECT count(*) n FROM users').fetchone()['n']:abort(409)
                db.execute('INSERT INTO users(username,password_hash,created_at) VALUES(?,?,?)',(user,generate_password_hash(pw,method='scrypt'),int(time.time())));audit('account_created','initial_admin',user)
            flash('Your operator account is ready. Sign in.','success');return redirect(url_for('auth.login'))
    return render_template('login.html',setup=True)
@bp.route('/admin/login',methods=['GET','POST'])
def login():
    db=get_db()
    if not db.execute('SELECT count(*) n FROM users').fetchone()['n']:return redirect(url_for('auth.setup'))
    if request.method=='POST':
        rate_limit('login',8);name=request.form.get('username','')[:64];pw=request.form.get('password','')[:256];row=db.execute('SELECT * FROM users WHERE username=?',(name,)).fetchone()
        valid=check_password_hash(row['password_hash'] if row else current_app.config['DUMMY_HASH'],pw)
        if row and valid:
            token=secrets.token_urlsafe(48);session.clear();session['admin_token']=token
            with db:db.execute('INSERT INTO sessions VALUES(?,?,?)',(hashlib.sha256(token.encode()).hexdigest(),row['id'],int(time.time())+28800));audit('login','session',name)
            return redirect(url_for('admin.dashboard'))
        with db:audit('login_failed','session','anonymous')
        flash('The username or password was not recognised.','error')
    return render_template('login.html',setup=False)
@bp.post('/admin/logout')
@login_required
def logout():
    db=get_db()
    with db:db.execute('DELETE FROM sessions WHERE token_hash=?',(hashlib.sha256(session['admin_token'].encode()).hexdigest(),));audit('logout','session')
    session.clear();return redirect(url_for('auth.login'))
@bp.route('/admin/password',methods=['GET','POST'])
@login_required
def password():
    from flask import g
    if request.method=='POST':
        rate_limit('password',6);db=get_db();row=db.execute('SELECT * FROM users WHERE id=?',(g.user['id'],)).fetchone();pw=request.form.get('new_password','')
        if not check_password_hash(row['password_hash'],request.form.get('current_password','')) or not 14<=len(pw)<=256 or pw!=request.form.get('confirm'):
            flash('Check your current password and use matching new passwords of at least 14 characters.','error')
        else:
            with db:db.execute('UPDATE users SET password_hash=? WHERE id=?',(generate_password_hash(pw,method='scrypt'),g.user['id']));db.execute('DELETE FROM sessions WHERE user_id=?',(g.user['id'],));audit('password_changed','account',g.user['username'])
            session.clear();return redirect(url_for('auth.login'))
    return render_template('password.html')
