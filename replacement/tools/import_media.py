"""Import unchanged source photos ONLY after explicit local-use permission."""
import argparse,concurrent.futures,hashlib,io,json,sys,time,urllib.request
from pathlib import Path
from urllib.parse import urlparse
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from app import create_app
from app.db import get_db

def fetch(row,dest):
 url=row['source_url'];u=urlparse(url)
 if u.scheme!='https' or u.hostname!='images.antiquesatlas.com' or not u.path.startswith('/dealer-stock-images/bridgendantiques/'):raise ValueError('Unexpected source URL')
 req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
 with urllib.request.urlopen(req,timeout=40) as response:
  if urlparse(response.url).hostname!='images.antiquesatlas.com':raise ValueError('Unexpected redirect')
  data=response.read(8*1024*1024+1)
 if len(data)>8*1024*1024:raise ValueError('Image exceeds 8 MB')
 im=Image.open(io.BytesIO(data));fmt=im.format;im.verify()
 if fmt not in ('JPEG','PNG','WEBP'):raise ValueError('Unsupported image format')
 digest=hashlib.sha256(data).hexdigest();name=digest+{'JPEG':'.jpg','PNG':'.png','WEBP':'.webp'}[fmt];path=dest/name
 if not path.exists():path.write_bytes(data)
 elif hashlib.sha256(path.read_bytes()).hexdigest()!=digest:raise ValueError('Existing content-addressed file mismatch')
 return dict(id=row['id'],source_url=url,path=name,sha256=digest,bytes=len(data),unchanged=True)

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--local-use-confirmed',action='store_true');parser.add_argument('--permission-reference',required=True);args=parser.parse_args()
 if not args.local_use_confirmed:parser.error('Explicit local-use permission is required; this switch is not itself authorisation')
 app=create_app();results=[];errors=[]
 with app.app_context():
  db=get_db();rows=[dict(r) for r in db.execute("SELECT * FROM images WHERE rights='pending' AND path='' ORDER BY id")];dest=Path(app.config['MEDIA_DIR'])
  with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
   futures={pool.submit(fetch,r,dest):r for r in rows}
   for i,future in enumerate(concurrent.futures.as_completed(futures),1):
    row=futures[future]
    try:
     result=future.result()
     with db:db.execute("UPDATE images SET path=?,sha256=?,rights='local_permission' WHERE id=? AND rights='pending'",(result['path'],result['sha256'],row['id']))
     results.append(result)
    except Exception as e:errors.append(dict(id=row['id'],source_url=row['source_url'],error=str(e)))
    if i%50==0:print(f'{i}/{len(rows)} checked; {len(errors)} errors',flush=True)
 receipt=dict(timestamp=int(time.time()),scope='LOCAL CONCEPT ONLY — NOT PRODUCTION OR TRANSFER',permission_reference=args.permission_reference,downloaded=results,errors=errors)
 out=ROOT/'evidence'/('media-import-'+str(time.time_ns())+'.json');out.write_text(json.dumps(receipt,indent=2));print(json.dumps(dict(downloaded=len(results),errors=len(errors),receipt=str(out))));return 1 if errors else 0
if __name__=='__main__':sys.exit(main())
