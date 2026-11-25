"""Release at most ten approved stories per ten minutes (UTC)."""
import json, re, os
from datetime import datetime, timezone, timedelta
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent

def parse(value):
    try:
        d=datetime.fromisoformat(value.replace('Z','+00:00'))
        return d if d.tzinfo else None
    except (AttributeError, ValueError, TypeError): return None

def main():
    path=ROOT/'home-news.json'; data=json.loads(path.read_text()); now=datetime.now(timezone.utc)
    queue=ROOT/'scheduled-news.json'; pending=json.loads(queue.read_text()) if queue.exists() else {'items':[]}
    last=parse(pending.get('lastReleasedAt'))
    if last and now-last<timedelta(minutes=10):
        print("Publication cooldown active; approved items remain queued."); return
    released=0
    for i in sorted(pending['items'],key=lambda x:parse(x.get('publishAt')) or datetime.max.replace(tzinfo=timezone.utc)):
        due=parse(i.get('publishAt'))
        if i.get('status')!='scheduled' or not due or due>now: continue
        if not i.get('editorApproved') or len(i.get('articleBody','').strip())<600 or not all(i.get(k) for k in ('author','title','summary','url','source')): continue
        if any(x.get('id')==i.get('id') or x.get('url')==i.get('url') for x in data['items']):
            pending['items'].remove(i); continue
        i['status']='published'; i['published']=now.isoformat()
        base=re.sub(r'[^a-z0-9]+','-',i['title'].lower()).strip('-')[:80].strip('-') or 'news'
        i['slug']=base
        if any(x.get('slug')==base for x in data['items']): i['slug']=base+'-'+i['id']
        data['items'].insert(0,i); data['updated']=now.isoformat(); pending['items'].remove(i); pending['lastReleasedAt']=now.isoformat()
        released+=1
        if released>=10: break
    print(f"Released {released} approved articles; {len(pending['items'])} queued.")
    if os.getenv("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"],"a",encoding="utf-8") as out: out.write(f"released={released}\n")
    if released: path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    new=json.dumps(pending,ensure_ascii=False,indent=2)+'\n'
    if not queue.exists() or queue.read_text()!=new: queue.write_text(new)
if __name__=='__main__':main()
