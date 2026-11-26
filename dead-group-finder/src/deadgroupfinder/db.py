from pathlib import Path
import csv, io, sqlite3
from datetime import datetime, timezone

def now(): return datetime.now(timezone.utc).isoformat(timespec="seconds")
class Database:
 def __init__(self,path):
  self.path=Path(path)
  if str(path) != ":memory:": self.path.parent.mkdir(parents=True,exist_ok=True)
  self.db=sqlite3.connect(str(path),timeout=20); self.db.row_factory=sqlite3.Row
  self.db.executescript("""PRAGMA journal_mode=WAL;
  CREATE TABLE IF NOT EXISTS candidates(id INTEGER PRIMARY KEY,link TEXT UNIQUE,username TEXT,title TEXT,source TEXT,discovered_at TEXT,verified TEXT DEFAULT 'UNVERIFIED');
  CREATE TABLE IF NOT EXISTS tracked(chat_id INTEGER PRIMARY KEY,title TEXT,username TEXT,chat_type TEXT,started_at TEXT,last_message_at TEXT,last_message_id INTEGER,active INTEGER DEFAULT 1);
  CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY,value TEXT);
  """); self.db.commit()
 def setting(self,k,d=''):
  r=self.db.execute('SELECT value FROM settings WHERE key=?',(k,)).fetchone(); return r[0] if r else d
 def set(self,k,v): self.db.execute('INSERT INTO settings VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value',(k,str(v))); self.db.commit()
 def candidate(self,link,username,title,source):
  before=self.db.total_changes
  self.db.execute('INSERT INTO candidates(link,username,title,source,discovered_at) VALUES(?,?,?,?,?) ON CONFLICT(link) DO UPDATE SET title=COALESCE(excluded.title,title)',(link,username,title,source,now())); self.db.commit(); return self.db.total_changes>before
 def candidates(self): return [dict(r) for r in self.db.execute('SELECT * FROM candidates ORDER BY id DESC LIMIT 30')]
 def track(self,c):
  self.db.execute('INSERT INTO tracked(chat_id,title,username,chat_type,started_at) VALUES(?,?,?,?,?) ON CONFLICT(chat_id) DO UPDATE SET title=excluded.title,active=1',(c['id'],c.get('title','No title'),c.get('username'),c.get('type','group'),now())); self.db.commit()
 def message(self,c,mid,ts):
  self.track(c); dt=datetime.fromtimestamp(ts,timezone.utc).isoformat(timespec='seconds'); self.db.execute('UPDATE tracked SET last_message_at=?,last_message_id=? WHERE chat_id=?',(dt,mid,c['id'])); self.db.commit()
 def deactivate(self,cid): self.db.execute('UPDATE tracked SET active=0 WHERE chat_id=?',(cid,)); self.db.commit()
 def groups(self): return [dict(r) for r in self.db.execute('SELECT * FROM tracked WHERE active=1 ORDER BY title')]
 def export(self):
  s=io.StringIO(); w=csv.writer(s); w.writerow(['chat_id','title','username','chat_type','started_at','last_message_at','last_message_id','active'])
  for r in self.db.execute('SELECT * FROM tracked'): w.writerow(list(r))
  return s.getvalue().encode('utf-8-sig')
