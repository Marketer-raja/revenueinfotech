import unittest, sys, tempfile, json
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import prepare_drafts as p, quality_checker as q, fact_checker as f, telegram_bot as t
from datetime import datetime,timezone
E=dict(title='Acme AI inference system update',source='Example',url='https://example.org/ai',published=datetime.now(timezone.utc).isoformat(),excerpt='Acme announced an inference platform for developers. The platform supports local testing before deployment. The vendor describes a dashboard for tracking resource use and says the preview is available to selected teams. The announcement does not include pricing or a general availability date. Documentation covers monitoring and describes the preview as an opportunity to gather feedback from early participants before expanding access. The preview documentation also describes the testing environment and explains how teams can submit feedback. Participants must request access through the vendor portal.')
BODY='Example reports that Acme is introducing an inference platform with a limited preview. Teams invited into the program can evaluate the software in a local environment before deploying it. A dashboard is intended to help participants understand how their applications consume resources. The vendor has not provided a price or a date for wider access.\n\nFor developers, the potential value lies in comparing resource requirements during experimentation rather than waiting until a production rollout. This is an implication, not a demonstrated performance improvement. Teams should examine the published documentation and determine whether the preview meets their requirements. Early access does not establish that the platform will suit every workload. A broader release and commercial terms remain unknown, and prospective users should avoid making purchasing assumptions until the vendor provides more information.'
D=dict(sufficient=True,title='Limited preview gives developers a look at Acme inference tools',summary='Example describes a limited preview of inference tools with resource monitoring.',articleBody=BODY,verificationNotes='Check preview eligibility and availability against Example.')
A=dict(supported=True,issues='',usefulness=9,readability=9)
class Quality(unittest.TestCase):
 def test_approved_draft(self):
  with patch.object(p,'candidates',return_value=iter([('OLLAMA',D)])),patch.object(p,'review',return_value=A): self.assertIsNotNone(p.ai_draft(E,[E]))
 def test_unsupported(self):
  self.assertEqual(q.quality_score(D,[E],dict(A,supported=False)),0)
 def test_missing_review(self):
  self.assertEqual(q.quality_score(D,[E],None),0)
 def test_short_evidence(self):
  with patch.object(p,'candidates') as c: self.assertIsNone(p.ai_draft(E,[dict(E,excerpt='short')])) ; c.assert_not_called()
 def test_repair(self):
  with patch.object(p,'candidates',side_effect=[iter([('OLLAMA',dict(D,title=E['title']))]),iter([('OLLAMA',D)])]) as c,patch.object(p,'review',return_value=A):
   self.assertIsNotNone(p.ai_draft(E,[E]));self.assertIn('headline too similar',c.call_args.args[0])
 def test_schema_review(self):
  with patch.object(f,'candidates',return_value=iter([('OLLAMA',dict(A,usefulness=99)),('OLLAMA',A)])):self.assertEqual(f.review(D,[E]),A)
 def test_duplicate_paragraph(self):
  self.assertEqual(q.quality_score(dict(D,articleBody=BODY+'\n\n'+BODY.split('\n\n')[0]),[E],A),0)
 def test_pipeline_preserves_pending(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td)
   for name in ('home-news.json','scheduled-news.json','news.json'): (root/name).write_text('{"items":[]}')
   with patch.object(p,'ROOT',root),patch.object(p,'load_research',return_value=[E]),patch.object(p,'candidates',return_value=iter([('OLLAMA',D)])),patch.object(p,'review',return_value=A):p.main()
   item=json.loads((root/'news.json').read_text())['items'][0];self.assertEqual(item['draftStatus'],'review required')
   self.assertIsNotNone(t.candidate(item))
   with patch.object(p,'ROOT',root),patch.object(p,'load_research',return_value=[]),patch.object(p,'ai_draft') as c:p.main();c.assert_not_called()
   self.assertEqual(json.loads((root/'news.json').read_text())['items'][0],item)
if __name__=='__main__':unittest.main()
