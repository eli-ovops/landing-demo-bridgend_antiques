import sys,tempfile,unittest,re,secrets,io,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from app import create_app
from app.db import get_db
from tools.import_source import import_source
from tools.backup import backup,restore
from PIL import Image
class AppTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.tmp=tempfile.TemporaryDirectory(prefix='bridgend-tests-');cls.data=Path(cls.tmp.name)/'runtime';cls.app=create_app(dict(TESTING=True,DATA_DIR=str(cls.data),DATABASE=str(cls.data/'shop.sqlite3'),MEDIA_DIR=str(cls.data/'media')));cls.report=import_source(cls.app);cls.password=secrets.token_urlsafe(24)
  c=cls.app.test_client();cls.post(c,'/admin/setup',dict(username='testoperator',password=cls.password,confirm=cls.password),'/admin/setup')
 @staticmethod
 def post(c,path,data,page='/contact'):
  html=c.get(page).get_data(as_text=True)
  revision=re.search(r'name="revision" value="(\d+)"',html)
  if revision:data=dict(data,revision=revision.group(1))
  with c.session_transaction() as s:token=s['csrf']
  return c.post(path,data=dict(data,csrf_token=token))
 def login(self,c):return self.post(c,'/admin/login',dict(username='testoperator',password=self.password),'/admin/login')
 def test_01_inventory_and_routes(self):
  self.assertEqual(self.report['statuses'],{'for_sale':65,'sold':217});c=self.app.test_client()
  for url in ['/','/catalogue','/catalogue?status=archived&page=19','/catalogue?q=zzzznoresult','/catalogue?category=1372','/product/as619a1227','/services','/reviews','/contact','/privacy','/terms']:
   r=c.get(url);self.assertEqual(r.status_code,200,url);self.assertIn('Content-Security-Policy',r.headers)
  self.assertEqual(c.get('/browse.php?code=as619a1227').location,'/product/as619a1227');self.assertEqual(c.get('/product/missing').status_code,404)
 def test_02_inquiry_persistence_and_duplicate(self):
  c=self.app.test_client();c.get('/contact?item=as619a1227')
  with c.session_transaction() as s:token=s['csrf'];submission=s['submission']
  data=dict(csrf_token=token,submission=submission,product_id='as619a1227',name='Synthetic Test',email='[REDACTED_EMAIL]',phone='',location='',topic='Buying an item',message='Synthetic enquiry for verification only.')
  r=c.post('/enquire',data=data);self.assertEqual(r.status_code,302);self.assertEqual(c.get(r.location).status_code,200);self.assertEqual(c.post('/enquire',data=data).location,r.location)
  with self.app.app_context():
   db=get_db();row=db.execute('SELECT * FROM inquiries WHERE submission_key=?',(submission,)).fetchone();self.assertEqual(row['message'],data['message']);self.assertEqual(db.execute('SELECT count(*) FROM inquiries WHERE submission_key=?',(submission,)).fetchone()[0],1);self.assertEqual(db.execute('SELECT state FROM outbox WHERE inquiry_id=?',(row['id'],)).fetchone()[0],'local_only')
  self.assertEqual(self.app.test_client().get(r.location).status_code,404);data['message']='Different repeat payload';self.assertEqual(c.post('/enquire',data=data).status_code,409)
  c.get('/contact?item=as619a1227')
  with c.session_transaction() as s:data['submission']=s['submission']
  self.assertEqual(c.post('/enquire',data=data).status_code,302)
 def test_03_access_csrf_revocation(self):
  c=self.app.test_client();self.assertEqual(c.get('/admin/export').status_code,302);self.assertEqual(c.post('/admin/login',data={}).status_code,403);self.assertEqual(self.login(c).status_code,302)
  for url in ['/admin','/admin/products','/admin/products/as619a1227','/admin/products/new','/admin/inquiries','/admin/settings','/admin/export','/admin/audit','/admin/password']:self.assertEqual(c.get(url).status_code,200,url)
  cookie=c.get_cookie('session');self.post(c,'/admin/logout',{},'/admin');c.set_cookie('session',cookie.value);self.assertEqual(c.get('/admin/export').status_code,302)
 def test_04_edit_import_upload(self):
  c=self.app.test_client();self.login(c);data=dict(title='Synthetic <script>alert(1)</script>',description='Test description',price='12.34',status='draft',period='',condition='',source_code='',categories=['1372'])
  r=self.post(c,'/admin/products/new',data,'/admin/products/new');self.assertEqual(r.status_code,302);pid=r.location.rsplit('/',1)[1]
  self.assertEqual(c.get('/product/'+pid).status_code,404);data['status']='for_sale';self.post(c,r.location,data,r.location);page=c.get('/product/'+pid);self.assertIn(b'&lt;script&gt;',page.data);self.assertNotIn(b'<script>alert',page.data)
  b=io.BytesIO();Image.new('RGB',(20,20),'red').save(b,format='PNG');b.seek(0);self.post(c,'/admin/products/'+pid+'/image',dict(image=(b,'test.png'),rights='confirmed',alt='Synthetic QA fixture'),r.location)
  with self.app.app_context():self.assertEqual(get_db().execute('SELECT count(*) FROM images WHERE product_id=? AND rights=?',(pid,'owner_supplied')).fetchone()[0],1)
  source=dict(data,title='Operator changed title');self.post(c,'/admin/products/as619a1227',source,'/admin/products/as619a1227');import_source(self.app)
  with self.app.app_context():self.assertEqual(get_db().execute('SELECT title FROM products WHERE id=?',('as619a1227',)).fetchone()[0],source['title'])
 def test_05_backup_restore(self):
  parent=Path(self.tmp.name);backup(self.data,parent/'backup');restore(parent/'backup',parent/'restored')
  import sqlite3
  with sqlite3.connect(parent/'restored/shop.sqlite3') as d:self.assertGreaterEqual(d.execute('SELECT count(*) FROM products').fetchone()[0],282);self.assertEqual(d.execute('SELECT count(*) FROM sessions').fetchone()[0],0)
  with self.assertRaises(ValueError):restore(parent/'backup',parent/'restored')

 def test_06_regressions(self):
  c=self.app.test_client();self.login(c)
  data=dict(title='Newest fixture',description='Synthetic item',price='8',status='for_sale',period='',condition='',source_code='QA')
  r=self.post(c,'/admin/products/new',data,'/admin/products/new');pid=r.location.rsplit('/',1)[1]
  self.assertIn(b'Newest fixture',c.get('/').data)
  with self.app.app_context():revision=get_db().execute('SELECT revision FROM products WHERE id=?',(pid,)).fetchone()[0]
  with c.session_transaction() as sess:csrf=sess['csrf']
  payload=dict(data,csrf_token=csrf,revision=revision,title='First writer')
  self.assertEqual(c.post(r.location,data=payload).status_code,302);payload['title']='Stale writer';self.assertEqual(c.post(r.location,data=payload).status_code,409)
  with self.app.app_context():self.assertEqual(get_db().execute('SELECT title FROM products WHERE id=?',(pid,)).fetchone()[0],'First writer')
  b=io.BytesIO();Image.new('RGB',(10,10),'blue').save(b,format='PNG');b.seek(0);self.post(c,r.location+'/image',dict(image=(b,'fixture.png'),rights='confirmed'),r.location)
  with self.app.app_context():im=dict(get_db().execute('SELECT * FROM images WHERE product_id=?',(pid,)).fetchone())
  response=c.get('/media/'+im['path']);self.assertEqual(response.status_code,200);response.close()
  self.post(c,r.location,dict(data,status='draft'),r.location);self.assertEqual(c.get('/media/'+im['path']).status_code,404)
  preview=c.get('/admin/media/'+im['path']);self.assertEqual(preview.status_code,200);preview.close()
  self.assertEqual(self.app.test_client().get('/admin/media/'+im['path']).status_code,302)
  self.assertIn(b'<option selected>Selling an item',c.get('/contact?topic=Selling').data)
  self.assertEqual(c.post('/admin/logout',data={'csrf_token':csrf},headers={'Origin':'https://hostile.invalid'}).status_code,403)
  self.post(c,'/admin/categories',{'name':'New QA category'},'/admin/categories');self.assertIn(b'New QA category',c.get('/admin/categories').data)
 def test_07_recovery_content(self):
  import sqlite3,time
  parent=Path(self.tmp.name);start=time.monotonic();backup(self.data,parent/'full-backup');restore(parent/'full-backup',parent/'full-restored')
  with sqlite3.connect(self.data/'shop.sqlite3') as source,sqlite3.connect(parent/'full-restored/shop.sqlite3') as target:
   for table in ['products','categories','product_categories','images','inquiries','outbox','settings','users']:
    self.assertEqual(source.execute('SELECT * FROM '+table).fetchall(),target.execute('SELECT * FROM '+table).fetchall(),table)
  from tools.backup import manifest
  self.assertEqual(manifest(self.data/'media'),manifest(parent/'full-restored/media'))
  d=parent/'full-restored';restored=create_app(dict(TESTING=True,DATA_DIR=str(d),DATABASE=str(d/'shop.sqlite3'),MEDIA_DIR=str(d/'media')));c=restored.test_client();self.assertEqual(self.login(c).status_code,302);self.assertEqual(c.get('/admin/inquiries').status_code,200)
  (parent/'full-backup/media/corrupt.txt').write_text('corrupt backup test')
  with self.assertRaises(ValueError):restore(parent/'full-backup',parent/'bad-restore')
  self.assertLess(time.monotonic()-start,30)

if __name__=='__main__':unittest.main(verbosity=2)
