"""Offline restoration to a NEW directory only; live SQLite backup is safe."""
import argparse,sqlite3,shutil,json,hashlib,os
from pathlib import Path

def manifest(root):return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob('*') if p.is_file() and p.name!='manifest.json'}
def backup(source,dest):
 source=Path(source);dest=Path(dest)
 if dest.exists():raise ValueError('Destination must not exist')
 if not (source/'shop.sqlite3').is_file():raise ValueError('Source database missing')
 dest.mkdir(parents=True,mode=0o700)
 with sqlite3.connect(source/'shop.sqlite3') as src,sqlite3.connect(dest/'shop.sqlite3') as dst:src.backup(dst)
 os.chmod(dest/'shop.sqlite3',0o600)
 if (source/'media').exists():shutil.copytree(source/'media',dest/'media')
 (dest/'manifest.json').write_text(json.dumps(manifest(dest),indent=2));return dest

def restore(source,dest):
 source=Path(source);dest=Path(dest)
 expected=json.loads((source/'manifest.json').read_text())
 if manifest(source)!=expected:raise ValueError('Backup integrity failed')
 if dest.exists():raise ValueError('Destination must not exist')
 shutil.copytree(source,dest);os.chmod(dest,0o700)
 with sqlite3.connect(dest/'shop.sqlite3') as db:
  if db.execute('PRAGMA integrity_check').fetchone()[0]!='ok':raise ValueError('Database integrity failed')
  db.execute('DELETE FROM sessions');db.commit()
 return dest
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['backup','restore']);p.add_argument('source');p.add_argument('destination');a=p.parse_args();globals()[a.action](a.source,a.destination);print(a.action+' verified')
