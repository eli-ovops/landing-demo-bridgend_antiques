import io,json,re,secrets,time,hashlib,warnings
from decimal import Decimal,InvalidOperation
from pathlib import Path
from flask import Blueprint,render_template,request,redirect,url_for,flash,abort,current_app,g,Response,send_from_directory
from PIL import Image
from .db import get_db,audit,setting
from .security import login_required
bp=Blueprint('admin',__name__,url_prefix='/admin')
@bp.get('')
@bp.get('/')
@login_required
def dashboard():
    db=get_db();counts={r['status']:r['n'] for r in db.execute('SELECT status,count(*) n FROM products GROUP BY status')};inq=db.execute('SELECT count(*) n FROM inquiries').fetchone()['n'];new=db.execute("SELECT count(*) n FROM inquiries WHERE status='new'").fetchone()['n'];pending=db.execute("SELECT count(*) n FROM images WHERE rights='pending'").fetchone()['n']
    return render_template('admin.html',mode='dashboard',counts=counts,inquiry_count=inq,new_count=new,pending=pending)
@bp.get('/products')
@login_required
def products():
    q=request.args.get('q','')[:120];db=get_db();params=('%'+q+'%','%'+q+'%');total=db.execute('SELECT count(*) FROM products WHERE title LIKE ? OR id LIKE ?',params).fetchone()[0];pages=max(1,(total+49)//50);page=min(pages,max(1,request.args.get('page',1,type=int)));rows=db.execute('SELECT * FROM products WHERE title LIKE ? OR id LIKE ? ORDER BY updated_at DESC,id LIMIT 50 OFFSET ?',params+((page-1)*50,)).fetchall();return render_template('admin.html',mode='products',products=rows,q=q,page=page,pages=pages)
@bp.route('/products/new',methods=['GET','POST'])
@bp.route('/products/<pid>',methods=['GET','POST'])
@login_required
def edit_product(pid=None):
    db=get_db();p=db.execute('SELECT * FROM products WHERE id=?',(pid,)).fetchone() if pid else None
    if pid and not p:abort(404)
    cats=db.execute('SELECT * FROM categories ORDER BY name').fetchall();chosen=[r['category_id'] for r in db.execute('SELECT category_id FROM product_categories WHERE product_id=?',(pid,))] if pid else []
    if request.method=='POST':
        values={k:request.form.get(k,'').strip() for k in ['title','description','price','status','period','condition','source_code']};selected=request.form.getlist('categories');errors=[]
        if not 3<=len(values['title'])<=200:errors.append('Use a title of 3–200 characters.')
        if len(values['description'])>6000 or len(values['period'])>200 or len(values['condition'])>500 or len(values['source_code'])>120:errors.append('One of the text fields is too long.')
        if values['status'] not in ('for_sale','reserved','sold','archived','draft'):errors.append('Choose a valid status.')
        if not set(selected).issubset({r['id'] for r in cats}):errors.append('Choose existing categories.')
        try:
            amount=Decimal(values['price']) if values['price'] else None
            if amount is not None and (not amount.is_finite() or amount<0 or amount>10000000 or amount.as_tuple().exponent< -2):raise InvalidOperation()
            pence=int(amount*100) if amount is not None else None
        except InvalidOperation:errors.append('Use a non-negative GBP price with at most two decimal places.');pence=None
        if errors:
            for e in errors:flash(e,'error')
            p={**(dict(p) if p else {}),**values,'price_pence':pence};chosen=selected
        else:
            pid=pid or 'BA'+secrets.token_hex(6).upper()
            with db:
                db.execute('BEGIN IMMEDIATE')
                if p:
                    current=db.execute('SELECT revision FROM products WHERE id=?',(pid,)).fetchone()['revision']
                    if request.form.get('revision',type=int)!=current:return render_template('conflict.html',values=values,pid=pid),409
                db.execute('INSERT INTO products(id,title,description,price_pence,status,period,condition,source_code,edited,updated_at) VALUES(?,?,?,?,?,?,?,?,1,?) ON CONFLICT(id) DO UPDATE SET title=excluded.title,description=excluded.description,price_pence=excluded.price_pence,status=excluded.status,period=excluded.period,condition=excluded.condition,source_code=excluded.source_code,edited=1,updated_at=excluded.updated_at,revision=products.revision+1,pricing_note=""',(pid,values['title'],values['description'],pence,values['status'],values['period'],values['condition'],values['source_code'],int(time.time())))
                if values['status']=='for_sale' and (not p or p['status']!='for_sale'):db.execute('UPDATE products SET published_order=? WHERE id=?',(time.time_ns(),pid))
                db.execute('DELETE FROM product_categories WHERE product_id=?',(pid,));db.executemany('INSERT INTO product_categories VALUES(?,?)',[(pid,c) for c in dict.fromkeys(selected)]);audit('product_saved',pid,g.user['username'])
            flash('Product saved. Importing source data again will preserve this edit.','success');return redirect(url_for('admin.edit_product',pid=pid))
    imgs=db.execute('SELECT * FROM images WHERE product_id=? ORDER BY position,id',(pid,)).fetchall() if pid else []
    return render_template('admin.html',mode='edit_product',product=p,categories=cats,selected=chosen,images=imgs,pid=pid)
@bp.post('/products/<pid>/image')
@login_required
def upload_image(pid):
    db=get_db()
    if not db.execute('SELECT 1 FROM products WHERE id=?',(pid,)).fetchone():abort(404)
    f=request.files.get('image')
    if not f or request.form.get('rights')!='confirmed':flash('Choose an image and confirm that you have permission to use it.','error');return redirect(url_for('admin.edit_product',pid=pid))
    data=f.read(8*1024*1024+1)
    if len(data)>8*1024*1024:abort(413)
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error',Image.DecompressionBombWarning)
            im=Image.open(io.BytesIO(data));fmt=im.format
            if fmt not in ('JPEG','PNG','WEBP') or im.width*im.height>20000000:raise ValueError()
            im.verify()
    except Exception:flash('Use a valid JPEG, PNG or WebP up to 8 MB and 20 megapixels.','error');return redirect(url_for('admin.edit_product',pid=pid))
    digest=hashlib.sha256(data).hexdigest();name=digest+{'JPEG':'.jpg','PNG':'.png','WEBP':'.webp'}[fmt];path=Path(current_app.config['MEDIA_DIR'])/name
    if not path.exists():path.write_bytes(data)
    with db:
        count=db.execute('SELECT count(*) n FROM images WHERE product_id=?',(pid,)).fetchone()['n'];db.execute('INSERT INTO images(product_id,path,source_url,sha256,alt,position,rights) VALUES(?,?,?,?,?,?,?) ON CONFLICT(product_id,source_url) DO NOTHING',(pid,name,'operator-upload:'+digest,digest,request.form.get('alt','').strip()[:250],count,'owner_supplied'));db.execute('UPDATE products SET edited=1,updated_at=? WHERE id=?',(int(time.time()),pid));audit('image_added',pid,g.user['username'])
    flash('Image added.','success');return redirect(url_for('admin.edit_product',pid=pid))
@bp.post('/images/<int:iid>/position')
@login_required
def image_position(iid):
    db=get_db();im=db.execute('SELECT * FROM images WHERE id=?',(iid,)).fetchone()
    if not im:abort(404)
    try:pos=max(0,min(100,int(request.form.get('position','0'))))
    except ValueError:abort(400)
    with db:db.execute('UPDATE images SET position=?,alt=? WHERE id=?',(pos,request.form.get('alt',im['alt'])[:250],iid));audit('image_reordered',str(iid),g.user['username'])
    return redirect(url_for('admin.edit_product',pid=im['product_id']))
@bp.get('/inquiries')
@login_required
def inquiries():
    db=get_db();total=db.execute('SELECT count(*) FROM inquiries').fetchone()[0];pages=max(1,(total+49)//50);page=min(pages,max(1,request.args.get('page',1,type=int)));rows=db.execute('SELECT * FROM inquiries ORDER BY created_at DESC,id LIMIT 50 OFFSET ?',((page-1)*50,)).fetchall();return render_template('admin.html',mode='inquiries',inquiries=rows,page=page,pages=pages)
@bp.route('/inquiries/<iid>',methods=['GET','POST'])
@login_required
def inquiry(iid):
    db=get_db();row=db.execute('SELECT * FROM inquiries WHERE id=?',(iid,)).fetchone()
    if not row:abort(404)
    if request.method=='POST':
        status=request.form.get('status')
        if status not in ('new','read','responded','closed'):abort(400)
        with db:db.execute('UPDATE inquiries SET status=?,updated_at=? WHERE id=?',(status,int(time.time()),iid));audit('inquiry_status',iid,g.user['username'])
        return redirect(url_for('admin.inquiry',iid=iid))
    return render_template('admin.html',mode='inquiry',inquiry=row,snapshot=json.loads(row['product_snapshot']))
@bp.route('/settings',methods=['GET','POST'])
@login_required
def settings():
    keys=['name','email','phone','mobile','address','hours','hours_note','payment_note','overview'];db=get_db()
    if request.method=='POST':
        data={k:request.form.get(k,'').strip() for k in keys}
        if any(not v or len(v)>2000 for v in data.values()) or not re.fullmatch(r'[^\s@<>]+@[^\s@<>]+\.[^\s@<>]+',data['email']):flash('Complete every field with valid contact details.','error')
        else:
            with db:db.execute('INSERT INTO settings VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value',('shop',json.dumps(data)));audit('settings_saved','shop',g.user['username'])
            flash('Shop details saved.','success');return redirect(url_for('admin.settings'))
    return render_template('admin.html',mode='settings',settings=setting('shop',{}),keys=keys)
@bp.get('/export')
@login_required
def export():
    db=get_db();tables=['products','categories','product_categories','images','inquiries','settings'];data={t:[dict(r) for r in db.execute('SELECT * FROM '+t)] for t in tables}
    with db:audit('data_export','content',g.user['username'])
    return Response(json.dumps(dict(schema_version=1,exported_at=int(time.time()),data=data),indent=2),mimetype='application/json',headers={'Content-Disposition':'attachment; filename=bridgend-content-export.json'})
@bp.get('/audit')
@login_required
def audit_log():return render_template('admin.html',mode='audit',events=get_db().execute('SELECT * FROM audit ORDER BY id DESC LIMIT 200').fetchall())

@bp.route('/categories',methods=['GET','POST'])
@login_required
def categories_admin():
    db=get_db()
    if request.method=='POST':
        name=request.form.get('name','').strip();cid=request.form.get('id','').strip()
        if not 2<=len(name)<=100:abort(400)
        if cid and not db.execute('SELECT 1 FROM categories WHERE id=?',(cid,)).fetchone():abort(404)
        cid=cid or 'C'+secrets.token_hex(6)
        with db:db.execute('INSERT INTO categories(id,name,archived) VALUES(?,?,?) ON CONFLICT(id) DO UPDATE SET name=excluded.name,archived=excluded.archived',(cid,name,1 if request.form.get('archived')=='1' else 0));audit('category_saved',cid,g.user['username'])
        return redirect(url_for('admin.categories_admin'))
    return render_template('categories.html',categories=db.execute('SELECT * FROM categories ORDER BY name').fetchall())

@bp.post('/images/<int:iid>/visibility')
@login_required
def image_visibility(iid):
    db=get_db();im=db.execute('SELECT * FROM images WHERE id=?',(iid,)).fetchone()
    if not im:abort(404)
    if im['rights'] not in ('owner_supplied','withdrawn_owner'):abort(400)
    state='withdrawn_owner' if im['rights']=='owner_supplied' else 'owner_supplied'
    with db:db.execute('UPDATE images SET rights=? WHERE id=?',(state,iid));audit('image_visibility_changed',str(iid),g.user['username'])
    return redirect(url_for('admin.edit_product',pid=im['product_id']))

@bp.get('/media/<name>')
@login_required
def media_preview(name):
    if not re.fullmatch(r'[a-f0-9]{64}\.(jpg|png|webp)',name):abort(404)
    if not get_db().execute('SELECT 1 FROM images WHERE path=?',(name,)).fetchone():abort(404)
    return send_from_directory(current_app.config['MEDIA_DIR'],name)
