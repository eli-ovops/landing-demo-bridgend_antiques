import sys,json,re,hashlib,time
from pathlib import Path
from decimal import Decimal
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from app import create_app
from app.db import get_db

def import_source(app):
 s=json.loads((ROOT/'data/source-index.json').read_text()); counts={}
 with app.app_context():
  db=get_db()
  with db:
   for c in s['categories']:db.execute('INSERT OR IGNORE INTO categories(id,name) VALUES(?,?)',(c['id'],c['name']))
   for p in s['products']:
    raw=(ROOT/'evidence/source'/f"{p['id']}.json").read_bytes();r=json.loads(raw);t=r['text']
    def field(name):
     m=re.search(r'\n'+name+r'\n(.*?)(?=\n(?:Date|Condition|Code|Price|Status|Seller)\n)',t,re.S);return m.group(1).strip() if m else ''
    status='sold' if field('Status').lower()=='sold' else 'for_sale' if p['listing_status']=='for_sale' else 'archived'
    m=re.search(r'£\s*([\d,]+(?:\.\d{2})?)',field('Price'));price=int(Decimal(m.group(1).replace(',',''))*100) if m else None
    title=next((h for h in r['h2'] if h not in ('Antiques Atlas','Purchase Item')),p['title']);counts[status]=counts.get(status,0)+1
    old=db.execute('SELECT edited FROM products WHERE id=?',(p['id'],)).fetchone()
    if not old or not old['edited']:
     db.execute('INSERT INTO products(id,title,description,price_pence,status,period,condition,source_code,source_url,source_status,source_hash,source_date,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET title=excluded.title,description=excluded.description,price_pence=excluded.price_pence,status=excluded.status,period=excluded.period,condition=excluded.condition,source_code=excluded.source_code,source_hash=excluded.source_hash,source_date=excluded.source_date',(p['id'],title,field('Description'),price,status,field('Date'),field('Condition'),field('Code'),p['url'],field('Status'),hashlib.sha256(raw).hexdigest(),s['date'],int(time.time())))
     note=field('Price')
     db.execute('UPDATE products SET pricing_note=? WHERE id=?',(note if 'Conversion rates as of' in note else '',p['id']))
     db.execute('DELETE FROM product_categories WHERE product_id=?',(p['id'],))
     for c in p['categories']:db.execute('INSERT OR IGNORE INTO product_categories VALUES(?,?)',(p['id'],c))
    db.execute("UPDATE products SET published_order=? WHERE id=? AND published_order=0",(int(p['id'].split('as619a')[1]),p['id']))
    urls=list(dict.fromkeys(l['url'] for l in r['links'] if l['url'].startswith('https://images.antiquesatlas.com/dealer-stock-images/bridgendantiques/')))
    for i,u in enumerate(urls):db.execute('INSERT OR IGNORE INTO images(product_id,source_url,alt,position) VALUES(?,?,?,?)',(p['id'],u,title,i))
   shop=dict(name='Bridgend Antiques',email='[REDACTED_EMAIL]',phone='02893341979',mobile='07966751699',address='50 Church Road, Ballynure, Ballyclare, Co Antrim, Northern Ireland BT39 9UF',hours='Antiques Atlas lists Monday–Saturday, 10:30am–5:30pm, or by appointment.',hours_note='Published opening times differ between directories. Please telephone to confirm your visit; Yell lists Sunday as closed.',payment_note='Gold and silver bought for cash. Please ask about payment arrangements for purchases.',overview='Antiques bought and sold in Ballynure. Browse furniture, clocks, silver, ceramics and collectables, or talk to Hector about an item you would like to sell.')
   db.execute('INSERT OR IGNORE INTO settings VALUES(?,?)',('shop',json.dumps(shop)))
  result=dict(products=sum(counts.values()),statuses=counts,categories=len(s['categories']),images=db.execute('SELECT count(*) FROM images').fetchone()[0],source_date=s['date']);return result
if __name__=='__main__':print(json.dumps(import_source(create_app()),indent=2))
