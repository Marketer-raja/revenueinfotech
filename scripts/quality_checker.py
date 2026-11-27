"""Conservative internal quality screening; scores are not Google metrics."""
import re
from difflib import SequenceMatcher
def quality_score(draft,evidence,review):
    if not review or review.get('supported') is not True or review.get('issues','').strip(): return 0
    body=draft['articleBody']; paras=[p for p in re.split(r'\n\s*\n',body) if p.strip()]
    if len(paras)<2: return 0
    if any(SequenceMatcher(None,a.lower(),b.lower()).ratio()>.85 for i,a in enumerate(paras) for b in paras[i+1:]): return 0
    depth=min(20, 10+sum(len(e['excerpt'].split()) for e in evidence)//30)
    return 25+20+depth+round(1.5*review['usefulness'])+review['readability']+5+5
