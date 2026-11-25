import unittest,sys
from pathlib import Path
from datetime import datetime,timezone
from email.utils import format_datetime
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import research_news as r, prepare_drafts as p
class ResearchTests(unittest.TestCase):
 def test_extract_and_match(self):
  summary='The company says its latest processor supports multiple workloads and includes additional memory capacity for developers running large applications locally.'
  xml=f'<rss><channel><item><title>Acme Orion processor update</title><link>https://example.org/orion</link><pubDate>{format_datetime(datetime.now(timezone.utc))}</pubDate><description>{summary}</description></item></channel></rss>'
  rows=r.parse_research(xml.encode(),'Example');self.assertEqual(len(rows),1)
  self.assertEqual(r.match_evidence({'title':'Acme Orion processor update - Example','url':'https://news.google.com/rss/a'},rows),rows)
  self.assertEqual(r.match_evidence({'title':'Unrelated security story','url':'https://example.org/b'},rows),[])
 def test_reject_copy(self):
  ev={'title':'Acme Orion processor update','excerpt':'The company says its latest processor supports multiple workloads and includes additional memory capacity.'}
  draft={'sufficient':True,'title':'A different headline','summary':'An original summary','articleBody':ev['excerpt']+' '+('analysis '*200),'verificationNotes':'Review the source'}
  self.assertIsNone(p.validate_draft(draft,ev,[ev]))
 def test_model_declines(self):
  with patch.object(p,'candidates',return_value=iter([('OLLAMA',{'sufficient':False})])):
   self.assertIsNone(p.ai_draft({},[]))
if __name__=='__main__':unittest.main()
