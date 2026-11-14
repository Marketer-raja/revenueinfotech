# RevenueInfoTech editorial workflow

## Candidate collection (automated)
- `scripts/fetch_news.py` collects headlines, source URLs, dates and short feed excerpts into `news.json`.
- GitHub Actions refreshes this candidate file every three hours.
- Candidate collection never writes to `home-news.json`.
- `/news/` is a noindex source directory, not a substitute for original reporting.

## Human review and homepage approval
1. Open the original publisher or primary source.
2. Confirm the date, named entities, numbers and claims.
3. Check whether the story is still current and relevant.
4. Write an original summary. Do not lightly paraphrase or reproduce the feed excerpt.
5. Add context: what changed, who is affected, why it matters, and what remains unconfirmed.
6. Attribute and link the original source; use images only when you have permission or a suitable licence.
7. Add the item in `/newsdesk/`, preview it, and press **Publish to site**.
8. Correct or remove an item promptly if a material error is found.

## Before publishing a full article
- Include a clear headline, a real author/editor byline, publication date and update date where applicable. Newsdesk requires a body of at least 600 characters as a basic safeguard; this is not an AdSense minimum.
- Explain the story in original language and add reporting, analysis, comparison, practical implications or primary-source context.
- Link to primary sources (company announcement, regulator, security advisory, research paper) as well as relevant reporting.
- Do not invent tests, interviews, experts, credentials, traffic figures, benchmarks or first-hand experience.
- Disclose sponsorship, affiliate links and conflicts.
- Keep a correction note when a published factual claim is materially changed.

## AdSense readiness
This workflow is a quality-control improvement, not a guarantee of AdSense approval. Review the actual policy notice in AdSense, check all live URLs, remove thin/duplicated or unsupported content, and ensure privacy and consent disclosures match the actual technologies used.
