# SEO and monetization release checklist

- [ ] `linkdownload.ajaynxt.com` resolves to GitHub Pages.
- [ ] `download.ajaynxt.com` resolves to the intended API VPS only.
- [ ] HTTPS is valid; HTTP redirects once to the canonical HTTPS URL.
- [ ] Home, supported sites and legal pages return `200` with self-canonicals.
- [ ] `/robots.txt` references the production sitemap.
- [ ] `/sitemap.xml` contains only canonical public `200` URLs.
- [ ] API and health routes return `X-Robots-Tag: noindex, nofollow`.
- [ ] Social preview image, title and description pass sharing debuggers.
- [ ] Structured data matches visible copy and passes syntax validation.
- [ ] UPI deep link opens the configured `9929562585@ybl` payment target on a real phone.
- [ ] Owner ad wording and destination are current.
- [ ] Search Console property is verified and sitemap submitted.
- [ ] Copyright contact inbox is monitored.
- [ ] Ad network approval and copyright-policy eligibility are confirmed before third-party ad code is added.
- [ ] Any non-essential analytics/advertising storage has an appropriate consent implementation.
- [ ] Mobile LCP, INP and CLS are checked after ad activation.
