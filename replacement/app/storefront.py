import json,re,secrets,time,hashlib,sqlite3
from pathlib import Path
from urllib.parse import urlencode
from flask import Blueprint,render_template,request,redirect,url_for,abort,session,current_app,send_from_directory
from .db import get_db,setting
from .security import rate_limit
bp=Blueprint('store',__name__)
def product_images(pid):return get_db().execute("SELECT * FROM images WHERE product_id=? AND rights IN ('local_permission','owner_supplied') AND path<>'' ORDER BY position,id",(pid,)).fetchall()
def categories():return get_db().execute('SELECT * FROM categories WHERE archived=0 ORDER BY name').fetchall()
def price(p):return '£'+format(p['price_pence']/100,',.2f') if p['price_pence'] is not None and p['status']=='for_sale' else ('Sold' if p['status']=='sold' else 'Price on enquiry' if p['status']=='for_sale' else p['status'].replace('_',' ').title())
@bp.app_template_filter('money')
def money(p):return price(p)
@bp.app_template_filter('telephone')
def telephone(number):
    value=re.sub(r'[^0-9+]','',number)
    return '+44'+value[1:] if value.startswith('0') else value
@bp.app_template_filter('date')
def date(t):return time.strftime('%d %b %Y',time.gmtime(t))
@bp.get('/')
def home():
    db=get_db();latest=db.execute("SELECT * FROM products WHERE status='for_sale' AND title NOT LIKE '%Sword%' ORDER BY published_order DESC,id DESC LIMIT 4").fetchall()
    return render_template('home.html',latest=latest,images={p['id']:product_images(p['id']) for p in latest})
@bp.get('/catalogue')
def catalogue():
    db=get_db();q=request.args.get('q','').strip()[:120];cat=request.args.get('category','')[:40];status=request.args.get('status','for_sale');status=status if status in ('for_sale','archived') else 'for_sale';sort=request.args.get('sort','newest');orders={'newest':'p.published_order DESC,p.id DESC','price_low':'p.price_pence IS NULL,p.price_pence ASC','price_high':'p.price_pence IS NULL,p.price_pence DESC','title':'p.title COLLATE NOCASE'}
    try:page=max(1,min(10000,int(request.args.get('page','1'))))
    except ValueError:page=1
    where=["p.status='for_sale'" if status=='for_sale' else "p.status IN ('sold','archived','reserved')"];params=[]
    if q:where.append('(p.title LIKE ? ESCAPE \'\\\' OR p.description LIKE ? ESCAPE \'\\\' OR p.id LIKE ? ESCAPE \'\\\')');term='%'+q.replace('\\','\\\\').replace('%','\\%').replace('_','\\_')+'%';params.extend([term]*3)
    if cat:where.append('EXISTS(SELECT 1 FROM product_categories pc WHERE pc.product_id=p.id AND pc.category_id=?)');params.append(cat)
    clause=' AND '.join(where);total=db.execute('SELECT count(*) n FROM products p WHERE '+clause,params).fetchone()['n'];pages=max(1,(total+11)//12);page=min(page,pages)
    products=db.execute('SELECT p.* FROM products p WHERE '+clause+' ORDER BY '+orders.get(sort,orders['newest'])+' LIMIT 12 OFFSET ?',params+[(page-1)*12]).fetchall()
    def page_url(n):return '/catalogue?'+urlencode(dict(q=q,category=cat,status=status,sort=sort,page=n))
    counts={r['status']:r['n'] for r in db.execute('SELECT status,count(*) n FROM products GROUP BY status')}
    return render_template('catalogue.html',products=products,images={p['id']:product_images(p['id']) for p in products},categories=categories(),q=q,category=cat,status=status,sort=sort,total=total,page=page,pages=pages,page_url=page_url,counts=counts)
@bp.get('/product/<pid>')
def product(pid):
    p=get_db().execute("SELECT * FROM products WHERE id=? AND status<>'draft'",(pid,)).fetchone()
    if not p:abort(404)
    cats=get_db().execute('SELECT c.* FROM categories c JOIN product_categories pc ON pc.category_id=c.id WHERE pc.product_id=?',(pid,)).fetchall()
    siblings=get_db().execute("SELECT id,title FROM products WHERE status=? ORDER BY published_order DESC,id DESC",(p['status'],)).fetchall()
    index=next(i for i,x in enumerate(siblings) if x['id']==pid)
    return render_template('product.html',product=p,images=product_images(pid),categories=cats,previous=siblings[index-1] if index else None,next=siblings[index+1] if index+1<len(siblings) else None)
@bp.get('/services')
def services():return render_template('services.html')
@bp.get('/reviews')
def reviews():return render_template('reviews.html')
@bp.get('/contact')
def contact():
    pid=request.args.get('item','');p=get_db().execute("SELECT * FROM products WHERE id=? AND status<>'draft'",(pid,)).fetchone() if pid else None
    if pid and not p:abort(404)
    session['submission']=secrets.token_urlsafe(32)
    session['submission_keys']=(session.get('submission_keys',[])+[session['submission']])[-20:]
    topic={'Selling':'Selling an item','Valuation':'Valuation','Visit':'Visit'}.get(request.args.get('topic'),'Buying an item' if p else 'Other')
    return render_template('contact.html',product=p,values={'topic':topic},errors={},submission=session['submission'])
@bp.post('/enquire')
def enquire():
    rate_limit('enquiry',12);db=get_db();keys=['name','email','phone','location','message','topic','product_id'];values={k:request.form.get(k,'').strip() for k in keys};errors={};pid=values['product_id'];p=db.execute("SELECT * FROM products WHERE id=? AND status<>'draft'",(pid,)).fetchone() if pid else None
    if pid and not p:abort(400)
    if request.form.get('website'):abort(400)
    if not 2<=len(values['name'])<=120:errors['name']='Enter your name (2–120 characters).'
    if not re.fullmatch(r'[^\s@<>]+@[^\s@<>]+\.[^\s@<>]+',values['email']) or len(values['email'])>254:errors['email']='Enter a valid email address.'
    if len(values['phone'])>40:errors['phone']='Use at most 40 characters.'
    if len(values['location'])>120:errors['location']='Use at most 120 characters.'
    if not 10<=len(values['message'])<=5000:errors['message']='Tell us about your enquiry (10–5,000 characters).'
    if values['topic'] not in ('Buying an item','Selling an item','Valuation','Restoration','House clearance','Visit','Other'):errors['topic']='Choose an enquiry topic.'
    key=request.form.get('submission','')
    if not key or key not in session.get('submission_keys',[]):abort(400)
    digest=hashlib.sha256(json.dumps(values,sort_keys=True).encode()).hexdigest();existing=db.execute('SELECT id,payload_hash FROM inquiries WHERE submission_key=?',(key,)).fetchone()
    if existing:
        if existing['payload_hash']!=digest:abort(409)
        session['receipt']=existing['id']
        return redirect(url_for('store.receipt',reference=existing['id']))
    if errors:return render_template('contact.html',product=p,values=values,errors=errors,submission=key),422
    reference='BA-'+secrets.token_hex(6).upper();now=int(time.time())
    try:
        with db:
            db.execute('INSERT INTO inquiries(id,submission_key,payload_hash,name,email,phone,location,message,product_id,topic,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',(reference,key,digest,values['name'],values['email'],values['phone'],values['location'],values['message'],pid or None,values['topic'],now,now))
            db.execute('UPDATE inquiries SET product_snapshot=? WHERE id=?',(json.dumps({k:p[k] for k in ['id','title','price_pence','currency','status','source_code']} if p else {}),reference))
            db.execute('INSERT INTO outbox(inquiry_id,created_at) VALUES(?,?)',(reference,now))
    except sqlite3.IntegrityError:
        row=db.execute('SELECT id,payload_hash FROM inquiries WHERE submission_key=?',(key,)).fetchone()
        if row and row['payload_hash']==digest:return redirect(url_for('store.receipt',reference=row['id']))
        abort(409)
    session['receipt']=reference
    return redirect(url_for('store.receipt',reference=reference))
@bp.get('/receipt/<reference>')
def receipt(reference):
    if not re.fullmatch(r'BA-[A-F0-9]{12}',reference) or session.get('receipt')!=reference or not get_db().execute('SELECT 1 FROM inquiries WHERE id=?',(reference,)).fetchone():abort(404)
    return render_template('receipt.html',reference=reference)
@bp.get('/new-enquiry')
def new_enquiry():
    session.pop('submission',None);return redirect(url_for('store.contact'))
@bp.get('/media/<name>')
def media(name):
    if not re.fullmatch(r'[a-f0-9]{64}\.(jpg|png|webp)',name):abort(404)
    if not get_db().execute("SELECT 1 FROM images WHERE path=? AND rights IN ('local_permission','owner_supplied') AND EXISTS (SELECT 1 FROM products p WHERE p.id=images.product_id AND p.status<>'draft')",(name,)).fetchone():abort(404)
    return send_from_directory(current_app.config['MEDIA_DIR'],name,max_age=86400)
@bp.get('/privacy')
def privacy():return render_template('policy.html',kind='privacy')
@bp.get('/terms')
def terms():return render_template('policy.html',kind='terms')
@bp.get('/api/health')
def health():get_db().execute('SELECT 1');return {'status':'ok'}
@bp.get('/browse.php')
@bp.get('/bridgendantiques/browse.php')
def legacy_browse():
    if request.args.get('code'):return redirect('/product/'+request.args['code'],code=301)
    try: page=max(1,int(request.args.get('page','0'))+1)
    except ValueError:page=1
    return redirect('/catalogue?'+urlencode({'q':request.args.get('s',''),'page':page,'category':request.args.get('maincatid',''),'status':'archived' if request.args.get('status')=='S' else 'for_sale'}),code=301)
@bp.get('/contact.php')
@bp.get('/bridgendantiques/contact.php')
def legacy_contact():return redirect('/contact',code=301)
@bp.get('/bridgendantiques/')
def legacy_home():return redirect('/',code=301)
