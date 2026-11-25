"""Temporary research from configured public RSS summaries; no page scraping.
Review feed terms before enabling a source. No excerpts are written to site files.
"""
import json, re, math
from datetime import datetime, timezone, timedelta
from difflib import SequenceMatcher
from urllib.parse import urlparse
import xml.etree.ElementTree as ET
from fetch_news import ROOT, ATOM, clean, txt, parse_date, fetch, norm_url

STOP=set('with from that this news technology about after will says have their into what when more over latest launches launch announced announces new report reports company'.split())
def tokens(s):
    return set(re.findall(r'[a-z0-9]{3,}',s.lower()))-STOP

def parse_research(data,source):
    root=ET.fromstring(data); out=[]
    for node in list(root.iter('item'))+list(root.iter(ATOM+'entry')):
        title=clean(txt(node,'title',ATOM+'title')); link=txt(node,'link')
        if not link:
            link=next((l.get('href','') for l in node.findall(ATOM+'link') if l.get('rel','alternate')=='alternate'),'')
        date=parse_date(txt(node,'pubDate',ATOM+'published',ATOM+'updated','{http://purl.org/dc/elements/1.1/}date'))
        summary=clean(txt(node,'description',ATOM+'summary'),1200)
        if not title or not link.startswith('https://') or not date or date<datetime.now(timezone.utc)-timedelta(days=7) or date>datetime.now(timezone.utc)+timedelta(minutes=15): continue
        if len(summary.split())<18 or len(tokens(summary)-tokens(title))<8: continue
        if urlparse(link).hostname=='news.google.com': continue
        out.append(dict(title=title,url=link,source=source,published=date.isoformat(),excerpt=summary))
    return out[:60]

def load_research():
    cfg=json.loads((ROOT/'research-feeds.json').read_text()); out=[]
    for f in cfg['feeds']:
        if not f.get('enabled'): continue
        try:
            rows=parse_research(fetch(f['url']),f['name']);out.extend(rows);print('Research feed:',f['name'],len(rows),'usable summaries',flush=True)
        except Exception as e: print('Research feed unavailable:',f['name'],type(e).__name__,flush=True)
    return out

def match_evidence(item,pool):
    a=tokens(item['title']); result=[]; seen=set()
    for row in pool:
        b=tokens(row['title']); overlap=len(a&b); score=overlap/max(1,len(a|b))
        exact=norm_url(item['url'])==norm_url(row['url'])
        if exact or (overlap>=3 and score>=.42): result.append((1.0 if exact else score,row))
    chosen=[]
    for _,row in sorted(result,key=lambda p:p[0],reverse=True):
        key=norm_url(row['url'])
        if key not in seen: chosen.append(row);seen.add(key)
    return chosen[:3]
