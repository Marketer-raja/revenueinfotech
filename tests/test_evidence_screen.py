import unittest, sys, tempfile, json
from pathlib import Path
from unittest.mock import patch
from datetime import datetime,timezone
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import prepare_drafts as p, research_news as r
E=dict(title='Acme AI developer platform preview',source='Example',url='https://example.org/ai',published=datetime.now(timezone.utc).isoformat(),excerpt='Acme announced an inference platform for developers. A limited preview includes local testing and resource monitoring. The vendor describes a dashboard for tracking consumption and offers documentation for selected participants. Pricing and broader availability were not specified in the announcement itself.')
class Screen(unittest.TestCase):
 def test_short_but_usable_direct_lead(self):
  self.assertTrue(40<=len(E['excerpt'].split())<65)
  with tempfile.TemporaryDirectory() as td:
   root=Path(td)
   for name in ('home-news.json','scheduled-news.json','news.json'): (root/name).write_text('{"items":[]}')
   with patch.object(p,'ROOT',root),patch.object(p,'load_research',return_value=[E]),patch.object(p,'ai_draft',return_value=None) as draft:
    p.main(); draft.assert_called_once()
 def test_no_headline_only(self):
  with patch.object(p,'candidates') as c:
   self.assertIsNone(p.ai_draft({},[dict(E,excerpt='too short')]));c.assert_not_called()
 def test_excluded(self):
  pool=[];r.add_direct_leads(pool,[E],[E['url']]);self.assertEqual(pool,[])
if __name__=='__main__':unittest.main()
