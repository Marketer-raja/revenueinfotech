# Implementation notes – November 5, 2026

## Included in this revision
- RSS collection writes candidate headlines to `news.json` and a noindex source directory; it does not overwrite `home-news.json`.
- The active GitHub Actions workflow collects candidates every three hours and also runs when Newsdesk commits `home-news.json`.
- Newsdesk requires an original full article body (at least 600 characters) and a real author/editor byline before an item can be saved for publication.
- The compiled homepage mapper ignores older feed-only entries that do not contain a full article body and byline.
- `scripts/build_articles.py` creates individual `/articles/<slug>/` pages with canonical URLs, NewsArticle structured data, source attribution and an updated sitemap.
- The `/news/` candidate directory remains noindex and is excluded from the sitemap.
- Added an About page, editorial workflow documentation and a practical article template.
- Updated the privacy policy to describe the visible analytics, contact-email and potential advertising setup more accurately.
- Removed the non-functional demo contact form and replaced it with a working email link.
- Added visible publication information to the homepage HTML for crawlers and readers.

## Important limitations and remaining editorial work
The supplied ZIP contains a compiled React bundle, not the original React source, package manifest or build configuration. The compiled bundle still contains preloaded sample article content and author-profile claims that must be checked against real editorial work. Do not represent any sample benchmark, test, credential, review or author biography as genuine unless you can substantiate it. The homepage should not be resubmitted for AdSense until all such content has been verified or removed and a useful set of genuinely original articles has been published.

The existing `home-news.json` contains older RSS-derived homepage entries from before the manual-approval workflow. Those entries lack the new full-article/byline fields and are therefore ignored by the homepage's Newsdesk mapper, but they remain in the Newsdesk list until an editor removes or replaces them.

## Deployment and verification
1. Back up the current GitHub repository before replacing files.
2. Deploy the updated files to the same repository and branch used by the live site.
3. Confirm GitHub Actions can run and has write permission to commit generated article pages and `sitemap.xml`.
4. Open `/newsdesk/`, connect using a fine-grained token restricted to this repository with Contents read/write, and publish a test article only after editorial review.
5. Confirm the generated `/articles/<slug>/` page, canonical URL, structured data and sitemap entry on the live domain.
6. Verify the contact email is monitored and that the privacy policy matches the actual analytics/consent configuration.
7. Check the exact AdSense rejection reason in the account and address it before requesting another review.

The 600-character check is a workflow safeguard, not a Google AdSense word-count rule. These changes do not guarantee approval.
