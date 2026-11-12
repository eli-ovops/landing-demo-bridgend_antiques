import sys,json,hashlib,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from app import create_app
from app.db import get_db
app=create_app();source=json.loads((ROOT/'data/source-index.json').read_text())
with app.app_context():
 db=get_db();products=[dict(r) for r in db.execute('SELECT * FROM products')];ids={p['id'] for p in products};source_ids={p['id'] for p in source['products']};missing={field:[p['id'] for p in products if not p[field]] for field in ['title','description','source_code','source_url','source_hash']};forms={}
 for p in source['products']:
  raw=json.loads((ROOT/'evidence/source'/f"{p['id']}.json").read_text())
  for form in raw['forms']:
   signature=','.join(x['name'] for x in form['inputs']);forms[signature]=forms.get(signature,0)+1
 report=dict(source_date=source['date'],source_ids=len(source_ids),local_ids=len(ids),missing_ids=sorted(source_ids-ids),extra_ids=sorted(ids-source_ids),statuses={r['status']:r['n'] for r in db.execute('SELECT status,count(*) n FROM products GROUP BY status')},missing_fields=missing,categories=db.execute('SELECT count(*) FROM categories').fetchone()[0],images_total=db.execute('SELECT count(*) FROM images').fetchone()[0],images_usable=db.execute("SELECT count(*) FROM images WHERE path<>'' AND rights IN ('local_permission','owner_supplied')").fetchone()[0],source_form_signatures=forms)
client=app.test_client();failures=[]
for pid in sorted(ids):
 response=client.get('/product/'+pid)
 if response.status_code!=200:failures.append(dict(id=pid,status=response.status_code))
report['product_route_failures']=failures
(ROOT/'evidence/coverage.json').write_text(json.dumps(report,indent=2))
manifest={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for folder in ['app','templates','static','tools','tests','docs'] for p in (ROOT/folder).rglob('*') if p.is_file() and '__pycache__' not in str(p)}
(ROOT/'evidence/implementation-manifest.json').write_text(json.dumps(manifest,indent=2));print(json.dumps(report,indent=2))
