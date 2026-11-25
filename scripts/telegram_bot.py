"""Poll Telegram and queue explicitly approved, unchanged editorial drafts."""
import hashlib
import json
import os
import re
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent.parent
ADMIN = 'https://revenueinfotech.com/newsdesk/'

def read(name, default=None):
    p = ROOT / name
    return json.loads(p.read_text(encoding='utf-8')) if p.exists() else default

def write(name, obj):
    p = ROOT / name
    s = json.dumps(obj, ensure_ascii=False, indent=2) + '\n'
    if not p.exists() or p.read_text(encoding='utf-8') != s:
        p.write_text(s, encoding='utf-8')

def valid_url(s):
    return isinstance(s, str) and urlsplit(s).scheme == 'https' and bool(urlsplit(s).hostname)

def candidate(i):
    d = i.get('draft') or {}
    if i.get('draftStatus') != 'review required' or not all(isinstance(d.get(k), str) and d[k].strip() for k in ('title','summary','articleBody','verificationNotes')):
        return None
    if len(d['articleBody'].strip()) < 600 or not all(valid_url(i.get(k)) for k in ('url','draftImage')) or not i.get('source'):
        return None
    sources = list(dict.fromkeys(x['url'] for x in i.get('researchSources',[]) if valid_url(x.get('url')) and x['url'] != i['url']))
    return dict(id=hashlib.sha256(i['url'].encode()).hexdigest()[:24], title=d['title'], summary=d['summary'], articleBody=d['articleBody'], author='RevenueInfoTech Editorial Desk', source=i['source'], url=i['url'], image=i['draftImage'], category=i.get('category') or 'Software Development', sources=sources, section='latest', verificationNotes=d['verificationNotes'])

def fingerprint(item):
    return hashlib.sha256(json.dumps(item,sort_keys=True,ensure_ascii=False).encode()).hexdigest()

def api(method, **params):
    token = os.environ['TELEGRAM_BOT_TOKEN'].strip()
    req = urllib.request.Request('https://api.telegram.org/bot'+token+'/'+method, data=json.dumps(params).encode(), headers={'Content-Type':'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=20) as r: data=json.load(r)
    except urllib.error.HTTPError as e:
        raise RuntimeError(f'Telegram {method}: HTTP {e.code}') from None
    except (urllib.error.URLError, TimeoutError, ValueError):
        raise RuntimeError(f'Telegram {method}: connection or response error') from None
    if not data.get('ok'): raise RuntimeError(f'Telegram {method}: rejected')
    return data['result']

def main():
    chat = int(os.environ['TELEGRAM_CHAT_ID'])
    if chat <= 0: raise ValueError('Use a private Telegram chat ID')
    if os.getenv('TELEGRAM_TEST_ONLY') == 'true':
        api('sendMessage', chat_id=chat, text='RevenueInfoTech GitHub notification test successful. No articles were approved.')
        return
    state=read('telegram-state.json',{'offset':0,'handled':[],'active':None})
    queue=read('scheduled-news.json',{'items':[]})
    home=read('home-news.json')
    blocked={i.get('url') for i in home['items']+queue['items']}
    items={}
    for lead in read('news.json')['items']:
        i=candidate(lead)
        if i and i['url'] not in blocked: items[fingerprint(i)]=i
    def send(text, **kw): return api('sendMessage',chat_id=chat,text=text,**kw)
    def answer(c,text):
        try: api('answerCallbackQuery',callback_query_id=c['id'],text=text)
        except RuntimeError: print('Callback acknowledgement unavailable')
    updates=api('getUpdates',offset=state['offset'],timeout=0,allowed_updates=['callback_query','message'])
    for u in updates:
        c=u.get('callback_query')
        if c and c.get('from',{}).get('id')==chat and c.get('message',{}).get('chat',{}).get('id')==chat:
            active=state.get('active'); action,_,batch=c.get('data','').partition(':')
            if not active or batch!=active['id'] or action not in ('approve','reject'):
                answer(c,'This batch is no longer active.')
            elif action=='reject':
                state['handled'].extend(active['keys']); state['active']=None; answer(c,'Batch rejected.')
            elif not all(k in items for k in active['keys']):
                state['active']=None; answer(c,'Drafts changed. Review the new batch before approval.')
            else:
                now=datetime.now(timezone.utc).isoformat()
                for k in active['keys']:
                    i=items.pop(k).copy(); i.pop('verificationNotes',None)
                    if i['url'] not in blocked:
                        queue['items'].append(dict(i,status='scheduled',editorApproved=True,publishAt=now)); blocked.add(i['url'])
                state['handled'].extend(active['keys']); state['active']=None
                answer(c,'Approval received. Queue is saved when GitHub commits successfully.')
        state['offset']=max(state['offset'],u['update_id']+1)
    active=state.get('active')
    if active and not all(k in items for k in active['keys']): state['active']=None
    if not state.get('active'):
        keys=[k for k in items if k not in state['handled']][:10]
        if keys:
            batch=hashlib.sha256((''.join(keys)+str(state['offset'])).encode()).hexdigest()[:24]
            text='RevenueInfoTech: '+str(len(keys))+' drafts ready for review\n\n'+'\n'.join(f'{n}. {items[k]["title"][:160]} ({items[k]["source"][:70]})' for n,k in enumerate(keys,1))+'\n\nReview the preceding full articles, sources and image links (or open Newsdesk) before approving. Approval queues these exact drafts; it does not verify their facts.'
            # Send the actual text and source links for review in the private chat.
            # Telegram's message limit is 4096 characters; split conservatively.
            for n,k in enumerate(keys,1):
                i=items[k]
                review=f'{n}. {i["title"]}\n\n{i["summary"]}\n\n{i["articleBody"]}\n\nSource: {i["source"]} — {i["url"]}\nAdditional sources: '+('\n'.join(i['sources']) or 'None')+'\nIllustration: '+i['image']+'\nEditorial notes: '+i['verificationNotes']
                for start in range(0,len(review),1800):
                    send(review[start:start+1800]); time.sleep(1.1)
            send(text,reply_markup={'inline_keyboard':[[{'text':'Review drafts in Newsdesk','url':ADMIN}],[{'text':f'Approve {len(keys)} reviewed drafts','callback_data':'approve:'+batch}],[{'text':'Reject batch','callback_data':'reject:'+batch}]]})
            state['active']={'id':batch,'keys':keys}
        else: print('No new complete drafts to notify.')
    state['handled']=list(dict.fromkeys(state['handled']))
    write('scheduled-news.json',queue); write('telegram-state.json',state)
    print('Telegram polling complete. Approved queue:',len(queue['items']))

if __name__=='__main__': main()
