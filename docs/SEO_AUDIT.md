# SEO audit

## Release baseline

- Canonical host: `https://download.ajaynxt.com`
- Indexable pages: home, supported sites, privacy, terms, copyright
- Non-indexable surfaces: `/api/*` and `/healthz` through `X-Robots-Tag`
- Discovery: root `robots.txt` and `sitemap.xml` with absolute canonical URLs
- Sharing: 1200×630 Open Graph image and matching social metadata
- Entity signals: AJAYNXT Organization, WebSite and WebApplication JSON-LD without fabricated reviews

## Remaining launch dependencies

1. Point the `download` DNS record to the production VPS.
2. Enable valid HTTPS, then set `ENABLE_HSTS=true`.
3. Verify Search Console and submit `/sitemap.xml`.
4. Test all public URLs with URL Inspection and Rich Results Test.
5. Collect 28 days of impressions, clicks, CTR, position, successful analyses and ready downloads before changing page targeting.

SEO can improve crawlability and relevance; it cannot guarantee ranking or virality.
