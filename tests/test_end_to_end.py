import unittest, sys, tempfile, json
from pathlib import Path
from unittest.mock import patch
from datetime import datetime, timezone
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import prepare_drafts as p, research_news as r, telegram_bot as t, publish_scheduled as pub, build_articles as build

E={'title':'Acme AI inference system update','source':'Example','url':'https://example.org/ai','published':datetime.now(timezone.utc).isoformat(),'excerpt':'Acme announced a new inference system for developers. The platform supports local testing before deployment. The vendor describes a new dashboard for tracking resource use and says the preview is available to selected teams. The announcement does not include pricing or a general availability date. Documentation covers monitoring and describes the preview as an opportunity to gather feedback from early participants before expanding access. The preview documentation also describes the testing environment and explains how teams can submit feedback.'}
BODY='Example reports that Acme is introducing an inference platform with a limited preview. Teams invited into the program can evaluate the software in a local environment before deploying it. A dashboard is intended to help participants understand how their applications consume resources. The vendor has not provided a price or a date for wider access.\n\nFor developers, the potential value lies in comparing resource requirements during experimentation rather than waiting until a production rollout. This is an implication, not a demonstrated performance improvement. Teams should examine the published documentation and determine whether the preview meets their requirements. Early access does not establish that the platform will suit every workload. A broader release and commercial terms remain unknown, and prospective users should avoid making purchasing assumptions until the vendor provides more information.'
D=dict(sufficient=True,title='Limited preview gives developers a look at Acme inference tools',summary='Example describes a limited preview of inference tools with resource monitoring.',articleBody=BODY,verificationNotes='Check preview eligibility, dashboard details and absence of published pricing against Example.')
class EndToEnd(unittest.TestCase):
 def test_pipeline(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td)
   for name in ('home-news.json','scheduled-news.json','news.json'): (root/name).write_text('{"items":[]}')
   with patch.object(p,'ROOT',root),patch.object(p,'load_research',return_value=[E]),patch.object(p,'candidates',side_effect=lambda prompt:iter([('OPENROUTER',D)])):
    p.main()
   lead=json.loads((root/'news.json').read_text())['items'][0];self.assertEqual(lead['draftStatus'],'review required');self.assertTrue(list((root/'logo/news-graphics').glob('*.svg')))
   calls=[]
   def api(method,**kw):
    calls.append((method,kw));return [] if method=='getUpdates' else {}
   with patch.object(t,'ROOT',root),patch.object(t,'api',side_effect=api),patch.object(t.time,'sleep'),patch.dict('os.environ',{'TELEGRAM_CHAT_ID':'123','TELEGRAM_TEST_ONLY':'false'}):t.main()
   state=json.loads((root/'telegram-state.json').read_text()); batch=state['active']['id'];self.assertTrue(any('articleBody' not in k and 'text' in k and 'Limited preview' in k['text'] for m,k in calls if m=='sendMessage'))
   def callback(uid,update):return {'update_id':update,'callback_query':{'id':str(update),'from':{'id':uid},'message':{'chat':{'id':123}},'data':'approve:'+batch}}
   with patch.object(t,'ROOT',root),patch.object(t,'api',side_effect=lambda method,**kw:[callback(999,1)] if method=='getUpdates' else {}),patch.object(t.time,'sleep'),patch.dict('os.environ',{'TELEGRAM_CHAT_ID':'123','TELEGRAM_TEST_ONLY':'false'}):t.main()
   self.assertEqual(len(json.loads((root/'scheduled-news.json').read_text())['items']),0)
   with patch.object(t,'ROOT',root),patch.object(t,'api',side_effect=lambda method,**kw:[callback(123,2),callback(123,3)] if method=='getUpdates' else {}),patch.object(t.time,'sleep'),patch.dict('os.environ',{'TELEGRAM_CHAT_ID':'123','TELEGRAM_TEST_ONLY':'false'}):t.main()
   q=json.loads((root/'scheduled-news.json').read_text());self.assertEqual(len(q['items']),1);self.assertTrue(q['items'][0]['editorApproved'])
   with patch.object(pub,'ROOT',root),patch.object(build,'ROOT',root):pub.main();build.main()
   self.assertEqual(len(json.loads((root/'home-news.json').read_text())['items']),1);self.assertTrue(list((root/'articles').glob('*/index.html')));self.assertTrue((root/'sitemap.xml').exists())
 def test_specific_rejection(self):
  self.assertEqual(p.validation_reason(dict(D,summary=''),{'title':E['title']},[E]),'missing field: summary')
  self.assertTrue(p.validation_reason(dict(D,articleBody='short'),{'title':E['title']},[E]).startswith('article too short'))
 def test_no_draft_without_evidence(self):
  with patch.object(p,'candidates') as mock:
   self.assertIsNone(p.ai_draft({},[]));mock.assert_not_called()
 def test_repair(self):
  with patch.object(p,'candidates',side_effect=[iter([('OLLAMA',dict(D,summary=''))]),iter([('OLLAMA',D)])]):
   self.assertIsNotNone(p.ai_draft({'title':E['title']},[E]))
if __name__=='__main__':unittest.main()
