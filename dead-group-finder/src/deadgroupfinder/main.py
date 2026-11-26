import logging, re, time
from datetime import datetime, timezone
from pathlib import Path
from .config import settings
from .core import inactivity_status, normalize_telegram_link
from .db import Database
from .discovery import Discovery
from .telegram_api import BotAPI, TelegramError
HELP='''Dead Group Finder 2.0\n/start /help /status /scan /discover text /addlink link /candidates /verify /tracked /report /setrange 2 90 /auto on|off /export\n\nیادآوری: فقط پیام‌های جدیدی که پس از افزودن ربات و با دسترسی لازم دریافت شوند پایش می‌شوند. تاریخچه قبلی قابل خواندن نیست.'''
def run():
 logging.basicConfig(level=logging.INFO,format='%(asctime)s %(levelname)s %(message)s',handlers=[logging.StreamHandler(),logging.FileHandler('dead-group-finder.log',encoding='utf-8')])
 s=settings(); db=Database(s['db']); api=BotAPI(s['token'],s['timeout']); search=Discovery(s['timeout']); me=api.me(); logging.info('Bot started: @%s',me.get('username')); api.webhook_off(); offset=None; last_auto=0
 keywords=[x.strip() for x in Path('keywords.txt').read_text(encoding='utf-8-sig').splitlines() if x.strip() and not x.startswith('#')] if Path('keywords.txt').exists() else ['گروه چت فارسی','گروه دورهمی','گروه خنده']
 while True:
  try:
   for u in api.updates(offset,s['poll']):
    offset=u['update_id']+1
    if 'my_chat_member' in u:
     m=u['my_chat_member']; c=m.get('chat',{}); st=m.get('new_chat_member',{}).get('status')
     if c.get('type') in ('group','supergroup'):
      if st in ('member','administrator'): db.track(c)
      elif st in ('left','kicked'): db.deactivate(c['id'])
     continue
    m=u.get('message');
    if not m: continue
    c=m.get('chat',{}); typ=c.get('type')
    if typ in ('group','supergroup'):
     if m.get('date'): db.message(c,m.get('message_id'),m['date'])
     continue
    sender=m.get('from',{}); cid=c.get('id'); text=(m.get('text') or '').strip()
    if typ!='private' or sender.get('id') not in s['owners'] or not text.startswith('/'): continue
    cmd,_,arg=text.partition(' '); cmd=cmd.split('@')[0].lower(); arg=arg.strip()
    if cmd in ('/start','/help'): api.send(cid,HELP)
    elif cmd=='/status': api.send(cid,f"نامزد لینک: {len(db.candidates())} (حداکثر ۳۰ مورد نمایش)\nگروه‌های تحت پایش: {len(db.groups())}")
    elif cmd in ('/scan','/discover'):
     terms=[arg] if cmd=='/discover' and arg else keywords
     if not terms: api.send(cid,'عبارت جست‌وجو خالی است.'); continue
     try:
      found=search.many(terms); added=0
      for link,(parsed,title) in found.items(): added+=db.candidate(link,parsed.public_username,title,'bing_rss')
      api.send(cid,f'جست‌وجو تمام شد. لینک یکتا: {len(found)} | لینک جدید: {added}. این لینک‌ها هنوز گروه/آخرین پیام تأییدشده نیستند. /candidates')
     except Exception as e: logging.exception('web search failed'); api.send(cid,'جست‌وجوی وب ناموفق بود: '+type(e).__name__)
    elif cmd=='/addlink':
     mt=re.search(r'(?:https?://)?(?:www\\.)?(?:t\\.me|telegram\\.me)/\\S+',arg,re.I); item=normalize_telegram_link(mt.group(0)) if mt else None
     if not item: api.send(cid,'لینک معتبر t.me وارد کن.')
     else: db.candidate(item.normalized_link,item.public_username,None,'manual'); api.send(cid,'لینک ذخیره شد؛ هنوز تأیید نشده است.')
    elif cmd=='/candidates':
     rows=db.candidates(); api.send(cid,'\n'.join(x['link']+' | '+x['verified'] for x in rows) or 'هنوز لینکی نداریم.')
    elif cmd=='/verify':
     rows=[x for x in db.candidates() if x['username']]; counts={'group':0,'channel':0,'unknown':0}
     for x in rows:
      try:
       ch=api.chat('@'+x['username']); state='PUBLIC_GROUP' if ch['type'] in ('group','supergroup') else 'CHANNEL_NOT_GROUP' if ch['type']=='channel' else 'UNKNOWN'; counts['group' if state=='PUBLIC_GROUP' else 'channel' if state=='CHANNEL_NOT_GROUP' else 'unknown']+=1
       db.db.execute('UPDATE candidates SET verified=? WHERE link=?',(state,x['link']))
      except TelegramError: counts['unknown']+=1
     db.db.commit(); api.send(cid,f"گروه: {counts['group']} | کانال: {counts['channel']} | نامشخص: {counts['unknown']}\nاین بررسی زمان آخرین پیام را مشخص نمی‌کند.")
    elif cmd=='/tracked': api.send(cid,'\n'.join(x['title']+' | '+str(x['chat_id']) for x in db.groups()) or 'گروهی تحت پایش نیست.')
    elif cmd=='/report':
     rows=db.groups(); lines=[]
     for x in rows:
      r=inactivity_status(x['last_message_at'],x['started_at'],s['low'],s['high']); label={'ACTIVE':'فعال','INACTIVE':'کم‌فعال','LONG_INACTIVE':'بدون پیام مشاهده‌شده طولانی','NO_MESSAGE_OBSERVED':'هنوز پیامی مشاهده نشده','UNKNOWN':'نامشخص'}[r['status']]; lines.append(f"{x['title']}: {label} ({r['days']} روز)" if r['days'] is not None else f"{x['title']}: {label}")
     api.send(cid,'فقط پیام‌های مشاهده‌شده پس از شروع پایش محاسبه شده‌اند.\n'+'\n'.join(lines))
    elif cmd=='/setrange':
     try:
      lo,hi=map(int,arg.split());
      if lo<1 or hi<lo or hi>3650: raise ValueError()
      s['low'],s['high']=lo,hi; api.send(cid,f'بازه به {lo} تا {hi} روز تغییر کرد (تا اجرای مجدد برنامه).')
     except Exception: api.send(cid,'کاربرد: /setrange 2 90')
    elif cmd=='/auto':
     if arg.lower() not in ('on','off'): api.send(cid,'کاربرد: /auto on یا /auto off')
     else: db.set('auto_scan',arg.lower()); api.send(cid,'جست‌وجوی روزانه: '+arg.lower())
    elif cmd=='/export':
     api.document(cid,'tracked_groups.csv',db.export(),'گزارش گروه‌های تحت پایش')
    else: api.send(cid,'دستور ناشناخته است. /help')
   if db.setting('auto_scan','off')=='on' and time.time()-last_auto >= s['interval']*3600:
    try:
     found=search.many(keywords)
     for link,(parsed,title) in found.items(): db.candidate(link,parsed.public_username,title,'bing_rss')
     last_auto=time.time(); logging.info('scheduled discovery: %s candidates',len(found))
    except Exception: logging.exception('scheduled discovery failed'); last_auto=time.time()
  except KeyboardInterrupt: break
  except TelegramError as e: logging.warning('%s',e); time.sleep(e.retry_after or 5)
  except Exception: logging.exception('main loop error'); time.sleep(5)
if __name__=='__main__': run()
