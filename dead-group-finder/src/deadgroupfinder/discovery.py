import html, re, time, urllib.parse, urllib.request, xml.etree.ElementTree as ET
from .core import normalize_telegram_link
PAT=re.compile(r"(?:https?://)?(?:www\\.)?(?:t\\.me|telegram\\.me)/(?:\\+|joinchat/)?[A-Za-z0-9_+/-]{4,80}",re.I)
class Discovery:
 def __init__(self,timeout=20): self.timeout=timeout
 def search(self,keyword):
  q=urllib.parse.quote(f'site:t.me "{keyword}" (گروه OR چت OR دورهمی)')
  req=urllib.request.Request('https://www.bing.com/search?format=rss&q='+q,headers={'User-Agent':'Mozilla/5.0 DeadGroupFinder/2.0','Accept':'application/rss+xml'})
  with urllib.request.urlopen(req,timeout=self.timeout) as r: body=r.read(2_000_000)
  root=ET.fromstring(body); out={}
  for item in root.findall('.//item'):
   title=item.findtext('title') or ''; desc=html.unescape(item.findtext('description') or '')
   for raw in [item.findtext('link') or '',*PAT.findall(title+' '+desc)]:
    link=normalize_telegram_link(raw)
    if link: out[link.normalized_link]=(link,title or None)
  return out
 def many(self,keywords):
  out={}
  for i,k in enumerate(keywords[:6]):
   if i: time.sleep(1.5)
   out.update(self.search(k))
  return out
