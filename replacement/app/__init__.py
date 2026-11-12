import os,secrets
from pathlib import Path
from flask import Flask,render_template,request
from werkzeug.security import generate_password_hash
from .db import init_db,close_db,setting
from .security import require_csrf,load_user,csrf_token
ROOT=Path(__file__).resolve().parents[1]
def create_app(test_config=None):
    app=Flask(__name__,template_folder=str(ROOT/'templates'),static_folder=str(ROOT/'static'))
    data=Path(os.environ.get('BRIDGEND_DATA',ROOT/'data/runtime')).resolve()
    app.config.update(DATABASE=str(data/'shop.sqlite3'),DATA_DIR=str(data),MEDIA_DIR=str(data/'media'),MAX_CONTENT_LENGTH=8*1024*1024,SESSION_COOKIE_HTTPONLY=True,SESSION_COOKIE_SAMESITE='Strict',SESSION_COOKIE_SECURE=os.environ.get('BRIDGEND_ENV')=='production',TRUSTED_HOSTS=['127.0.0.1','localhost']+([os.environ['BRIDGEND_HOST']] if os.environ.get('BRIDGEND_HOST') else []),ALLOW_SETUP=os.environ.get('BRIDGEND_ENV')!='production',DUMMY_HASH=generate_password_hash(secrets.token_urlsafe(32),method='scrypt'))
    if test_config:app.config.update(test_config)
    data=Path(app.config['DATA_DIR']);data.mkdir(parents=True,exist_ok=True);os.chmod(data,0o700)
    secret_path=data/'session.key'
    if not secret_path.exists():
        fd=os.open(secret_path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
        with os.fdopen(fd,'wb') as f:f.write(secrets.token_bytes(48))
    app.secret_key=secret_path.read_bytes();Path(app.config['MEDIA_DIR']).mkdir(parents=True,exist_ok=True)
    init_db(app.config['DATABASE']);os.chmod(app.config['DATABASE'],0o600)
    app.teardown_appcontext(close_db);app.before_request(require_csrf);app.before_request(load_user)
    from . import storefront,auth,admin
    app.register_blueprint(storefront.bp);app.register_blueprint(auth.bp);app.register_blueprint(admin.bp)
    @app.context_processor
    def context():return dict(csrf_token=csrf_token,shop=setting('shop',{}),is_admin=request.path.startswith('/admin'))
    @app.after_request
    def headers(response):
        response.headers['X-Content-Type-Options']='nosniff';response.headers['Referrer-Policy']='strict-origin-when-cross-origin';response.headers['X-Frame-Options']='DENY';response.headers['Content-Security-Policy']="default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; form-action 'self'; frame-ancestors 'none'; base-uri 'self'; object-src 'none'"
        response.headers['Permissions-Policy']='camera=(), microphone=(), geolocation=()'
        if request.path.startswith('/admin') or request.method=='POST' or request.path.startswith('/receipt'):response.headers['Cache-Control']='no-store'
        if app.config['SESSION_COOKIE_SECURE']:response.headers['Strict-Transport-Security']='max-age=31536000'
        return response
    for code in (400,403,404,409,413,429,500):
        def handle(error):return render_template('error.html',code=error.code),error.code
        app.register_error_handler(code,handle)
    return app
