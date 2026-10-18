# RevenueInfoTech news starter

## 1. Fix the redirect loop (do this first)
Replace your `_redirects` file with the one here. It removes the two rules
(`/contact -> /contact.html`, `/privacy-policy -> /privacy-policy.html`) that
fight your host's automatic ".html" removal and cause "too many redirects".
Then redeploy. Both /contact and /contact.html will work.

## 2. Add automatic news
Copy these into the ROOT of your GitHub repo (same level as index.html):
  feeds.json
  scripts/fetch_news.py
  .github/workflows/update-news.yml

Then on GitHub: Actions tab -> "Update news" -> Run workflow.
It will create news.json, news/index.html and sitemap.xml, commit them, and
your host (Cloudflare Pages / Netlify) redeploys automatically. After that it
runs every hour by itself. Your page will be live at /news/.

## 3. Choosing feeds
Edit feeds.json. Before adding a feed, read that publisher's terms of use
and confirm their feed URL still works. Prefer official company newsrooms
and press-release feeds. Keep excerpts short and always link to the source.

## 4. Test locally
  python3 scripts/fetch_news.py

## 5. Fully automatic tech-only home page (new)
Every hour the "Update news" GitHub Action now:
- reads the tech feeds in feeds.json,
- drops anything that is not technology news (keyword filter in scripts/fetch_news.py:
  CATEGORIES / EXTRA_TECH keep tech, NON_TECH removes off-topic stories),
- picks a picture for each story (from the feed, or the article's preview image),
- writes home-news.json so the home page hero, briefs, latest list and featured
  cards update by themselves - no Newsdesk publishing needed.
Make sure GitHub -> Settings -> Actions -> General -> "Workflow permissions" is set to
"Read and write permissions", then run the workflow once from the Actions tab.
