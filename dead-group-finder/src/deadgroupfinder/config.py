import os
from pathlib import Path

def load_env():
 p=Path('.env')
 if p.exists():
  for line in p.read_text(encoding='utf-8').splitlines():
   line=line.strip()
   if line and not line.startswith('#') and '=' in line:
    k,v=line.split('=',1); os.environ.setdefault(k.strip(),v.strip().strip('"').strip("'"))
def settings():
 load_env(); token=os.getenv('TELEGRAM_BOT_TOKEN','').strip(); ids={int(x.strip()) for x in os.getenv('OWNER_IDS','').split(',') if x.strip()}
 if ':' not in token: raise ValueError('Set TELEGRAM_BOT_TOKEN in .env')
 if not ids: raise ValueError('Set numeric OWNER_IDS in .env')
 low=int(os.getenv('MIN_INACTIVE_DAYS','2')); high=int(os.getenv('MAX_INACTIVE_DAYS','90'))
 if low<1 or high<low: raise ValueError('Invalid inactivity range')
 return {'token':token,'owners':ids,'db':os.getenv('DATABASE_PATH','data/dead_groups.sqlite3'),'timeout':int(os.getenv('REQUEST_TIMEOUT','20')),'poll':int(os.getenv('POLL_TIMEOUT','25')),'low':low,'high':high,'interval':int(os.getenv('SCAN_INTERVAL_HOURS','24'))}
