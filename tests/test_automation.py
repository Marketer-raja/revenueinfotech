import unittest, sys, tempfile,json
from datetime import datetime,timezone,timedelta
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import fetch_news, publish_scheduled, prepare_drafts
class Automation(unittest.TestCase):
 def test_feed(self):
  from email.utils import format_datetime
  now=format_datetime(datetime.now(timezone.utc));old=format_datetime(datetime.now(timezone.utc)-timedelta(days=7))
  xml=f'<rss><channel><item><title>AI technology launch</title><link>https://example.com/a</link><pubDate>{now}</pubDate><description>Publisher text</description></item><item><title>AI older</title><link>https://example.com/b</link><pubDate>{old}</pubDate></item></channel></rss>'
  items=fetch_news.parse_feed(xml.encode(),'Test');self.assertEqual(len(items),1);self.assertEqual(items[0]['excerpt'],'');self.assertEqual(items[0]['image'],'')
 def test_release(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);(root/'home-news.json').write_text('{"items":[]}');item={'id':'a','status':'scheduled','publishAt':'2020-01-01T00:00:00+00:00','editorApproved':True,'articleBody':'x'*601,'title':'AI story','summary':'Summary','author':'Editor','source':'Example','url':'https://example.com/a'};future=dict(item,id='b',publishAt='2099-01-01T00:00:00+00:00');(root/'scheduled-news.json').write_text(json.dumps({'items':[item,future]}))
   with patch.object(publish_scheduled,'ROOT',root):publish_scheduled.main();publish_scheduled.main()
   self.assertEqual(len(json.loads((root/'home-news.json').read_text())['items']),1);self.assertEqual(len(json.loads((root/'scheduled-news.json').read_text())['items']),1)
 def test_spacing(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d); (root/'home-news.json').write_text('{"items":[]}')
   item={'status':'scheduled','publishAt':'2020-01-01T00:00:00+00:00','editorApproved':True,'articleBody':'x'*601,'title':'AI story','summary':'Summary','author':'Editor','source':'Example'}
   (root/'scheduled-news.json').write_text(json.dumps({'items':[dict(item,id=str(i),url='https://example.com/'+str(i)) for i in range(23)]}))
   with patch.object(publish_scheduled,'ROOT',root):
    publish_scheduled.main();publish_scheduled.main()
    self.assertEqual(len(json.loads((root/'home-news.json').read_text())['items']),10)
    q=json.loads((root/'scheduled-news.json').read_text());self.assertEqual(len(q['items']),13);q['lastReleasedAt']=(datetime.now(timezone.utc)-timedelta(minutes=11)).isoformat();(root/'scheduled-news.json').write_text(json.dumps(q));publish_scheduled.main()
   self.assertEqual(len(json.loads((root/'home-news.json').read_text())['items']),20)
if __name__=='__main__':unittest.main()
