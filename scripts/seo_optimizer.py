"""Advisory metadata; existing page builder remains authoritative."""
import re
def metadata(draft):
    summary=' '.join(draft['summary'].split()); description=summary if len(summary)<=160 else summary[:157].rsplit(' ',1)[0]+'...'
    return {'seoTitle':draft['title'][:70], 'metaDescription':description}
