import sqlite3, json, time
from pathlib import Path
from flask import current_app, g
SCHEMA='''
CREATE TABLE IF NOT EXISTS products(id TEXT PRIMARY KEY,title TEXT NOT NULL,description TEXT NOT NULL DEFAULT '',price_pence INTEGER,currency TEXT NOT NULL DEFAULT 'GBP',status TEXT NOT NULL,period TEXT DEFAULT '',condition TEXT DEFAULT '',source_code TEXT DEFAULT '',source_url TEXT DEFAULT '',source_status TEXT DEFAULT '',source_hash TEXT DEFAULT '',source_date TEXT DEFAULT '',edited INTEGER NOT NULL DEFAULT 0,updated_at INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS categories(id TEXT PRIMARY KEY,name TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS product_categories(product_id TEXT REFERENCES products(id),category_id TEXT REFERENCES categories(id),PRIMARY KEY(product_id,category_id));
CREATE TABLE IF NOT EXISTS images(id INTEGER PRIMARY KEY,product_id TEXT REFERENCES products(id),path TEXT NOT NULL DEFAULT '',source_url TEXT NOT NULL DEFAULT '',sha256 TEXT DEFAULT '',alt TEXT DEFAULT '',position INTEGER NOT NULL DEFAULT 0,rights TEXT NOT NULL DEFAULT 'pending',UNIQUE(product_id,source_url));
CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY,username TEXT UNIQUE NOT NULL,password_hash TEXT NOT NULL,created_at INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS sessions(token_hash TEXT PRIMARY KEY,user_id INTEGER REFERENCES users(id),expires INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS inquiries(id TEXT PRIMARY KEY,submission_key TEXT UNIQUE NOT NULL,payload_hash TEXT NOT NULL,name TEXT NOT NULL,email TEXT NOT NULL,phone TEXT NOT NULL DEFAULT '',location TEXT NOT NULL DEFAULT '',message TEXT NOT NULL,product_id TEXT REFERENCES products(id),topic TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'new',created_at INTEGER NOT NULL,updated_at INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY,actor TEXT NOT NULL,action TEXT NOT NULL,resource TEXT NOT NULL,created_at INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS limits(key TEXT NOT NULL,bucket INTEGER NOT NULL,hits INTEGER NOT NULL,PRIMARY KEY(key,bucket));
CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY,value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS outbox(id INTEGER PRIMARY KEY,inquiry_id TEXT UNIQUE REFERENCES inquiries(id),state TEXT NOT NULL DEFAULT 'local_only',created_at INTEGER NOT NULL);

'''
def connect(path):
    db=sqlite3.connect(path,timeout=15);db.row_factory=sqlite3.Row;db.execute('PRAGMA foreign_keys=ON');db.execute('PRAGMA journal_mode=WAL');return db
def get_db():
    if 'db' not in g:g.db=connect(current_app.config['DATABASE'])
    return g.db
def init_db(path):
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    with connect(path) as db:
        version=db.execute('PRAGMA user_version').fetchone()[0]
        if version>4:raise RuntimeError('Database schema is newer than this application')
        db.executescript(SCHEMA)
        if version<2:
            columns={r['name'] for r in db.execute('PRAGMA table_info(products)')}
            if 'revision' not in columns:db.execute('ALTER TABLE products ADD COLUMN revision INTEGER NOT NULL DEFAULT 0')
            columns={r['name'] for r in db.execute('PRAGMA table_info(inquiries)')}
            if 'product_snapshot' not in columns:db.execute("ALTER TABLE inquiries ADD COLUMN product_snapshot TEXT NOT NULL DEFAULT '{}'")
            db.execute('PRAGMA user_version=2')
        if version<3:
            columns={r['name'] for r in db.execute('PRAGMA table_info(products)')}
            if 'published_order' not in columns:db.execute('ALTER TABLE products ADD COLUMN published_order INTEGER NOT NULL DEFAULT 0')
            db.execute("UPDATE products SET published_order=CAST(substr(id,7) AS INTEGER) WHERE published_order=0 AND id LIKE 'as619a%'")
            columns={r['name'] for r in db.execute('PRAGMA table_info(categories)')}
            if 'archived' not in columns:db.execute('ALTER TABLE categories ADD COLUMN archived INTEGER NOT NULL DEFAULT 0')
            db.execute('PRAGMA user_version=3')
        if version<4:
            columns={r['name'] for r in db.execute('PRAGMA table_info(products)')}
            if 'pricing_note' not in columns:db.execute("ALTER TABLE products ADD COLUMN pricing_note TEXT NOT NULL DEFAULT ''")
            db.execute('PRAGMA user_version=4')
def close_db(_=None):
    db=g.pop('db',None)
    if db:db.close()
def audit(action,resource,actor='operator'):
    get_db().execute('INSERT INTO audit(actor,action,resource,created_at) VALUES(?,?,?,?)',(actor,action,resource,int(time.time())))
def setting(key,default=None):
    row=get_db().execute('SELECT value FROM settings WHERE key=?',(key,)).fetchone()
    return json.loads(row['value']) if row else default
