# Kenya Works Website

The public website for **Kenya Works**, a rights-based nonprofit partnering with Kenyan communities to secure safety and dignity for vulnerable children, families, and communities through four connected program pillars:

| Pillar | Focus |
|---|---|
| **Shelter Works** | Safe refuge for children in crisis; family reunification; women's empowerment |
| **MHH Works** | Menstrual health education; Makini reusable pads; Boxers for Boys |
| **Education Works** | Student sponsorships; school feeding; school infrastructure |
| **Community Works** | Human rights training; child protection advocacy |

**EIN:** 05-0623727 · **Mailing address:** PO Box 1572, Appleton, WI 54912

---

## Tech stack

- **[Hugo](https://gohugo.io/)** (v0.163+, extended) — static site generator
- **Tailwind CSS** (CDN) — layout utilities
- **Google Fonts** — Roboto, Roboto Condensed, Roboto Slab
- No build pipeline required beyond Hugo itself

---

## Prerequisites

Install Hugo extended:

```bash
brew install hugo
```

Verify:

```bash
hugo version   # must show "+extended"
```

---

## Running locally

```bash
git clone git@github.com:Kenyaworks/Website-Files.git
cd Website-Files
hugo server
```

The site is available at `http://localhost:1313`. Hugo watches for file changes and rebuilds automatically.

For a full rebuild on every save (slower but catches all edge cases):

```bash
hugo server --disableFastRender
```

To build the static output to `public/`:

```bash
hugo
```

---

## Project structure

```
content/             # Markdown pages and stories
  our-work/          # Four pillar program pages
  stories/           # Blog posts (migrated from Wix)
assets/
  images/stories/    # Hero images for blog posts
static/
  css/screen.css     # Brand tokens, component styles
layouts/
  _default/          # Page-level templates
  partials/          # site-header, site-footer, post-card
  stories/           # Story list and single templates
hugo.toml            # Site config, menu, and params
```

---

## Configuration (`hugo.toml`)

| Parameter | Description |
|---|---|
| `baseURL` | Production URL — change before deploying |
| `params.donateURL` | Link to the Wix donation page |
| `params.sponsorURL` | Link to the Wix student sponsorship page |
| `params.fundraiseURL` | Link to the Wix fundraising page |
| `params.ein` | IRS EIN (shown in footer) |
| `params.paypalButtonId` | PayPal donation button ID — replace placeholder |
| `params.giveLivelySlug` | Give Lively campaign slug — replace placeholder |
| `params.mpesaPaybill` | M-Pesa paybill number |
| `params.mpesaAccount` | M-Pesa account format string |
| `params.mailingAddress` | US mailing address (footer) |

The `[menu.main]` section controls top-level navigation and the **About** dropdown.

---

## Adding a blog post

1. Create a file in `content/stories/` named after the post slug:
   ```
   content/stories/my-post-title.md
   ```

2. Add frontmatter:
   ```yaml
   ---
   title: "Post title"
   date: 2026-01-15
   tags: ["education-works"]          # one or more: shelter-works, education-works, mhh-works, community-works
   summary: "One-sentence teaser shown on the listing card."
   image: "/images/stories/my-post-title.jpg"
   ---
   ```

3. Place the hero image (JPG or PNG, ideally 1280×960 or wider landscape) at:
   ```
   assets/images/stories/my-post-title.jpg
   ```
   Hugo processes it automatically to WebP at build time. **GIFs should be converted to JPEG first** — Hugo's WebP conversion of GIFs will crash the build.

4. Write the post body in Markdown below the frontmatter. Headings (`##`, `###`), bold, italic, blockquotes, and lists all render correctly.

Posts without an `image` field render with a plain navy hero banner instead.

---

## Design system

Brand tokens live in `static/css/screen.css` as CSS custom properties:

```css
--kw-primary        /* navy #0D4177 */
--kw-accent         /* orange #F28F0C */
--kw-education      /* blue #2D6DB5 */
--kw-mhh            /* purple #9B2D8F */
--kw-text           /* body text gray-700 */
--kw-text-muted     /* secondary text gray-500 */
--kw-border         /* divider gray-200 */
```

Use these tokens in templates and inline styles rather than hardcoded hex values so palette changes propagate everywhere.

Post body text uses the `.gh-content` class (Roboto 300, 16px, line-height 1.65).

---

## Deployment

The site is built and published to **GitHub Pages** by GitHub Actions — no local build or manual upload is needed.

- **Automatic deploys:** every push to `main` runs [`.github/workflows/hugo.yml`](.github/workflows/hugo.yml), which builds the site with Hugo extended and deploys `public/` to Pages.
- **Manual deploys:** go to **Actions → Deploy Hugo site to Pages → Run workflow** (or run `gh workflow run hugo.yml`).
- **Pull request checks:** [`.github/workflows/build-check.yml`](.github/workflows/build-check.yml) builds the site on every PR to `main` to catch broken templates or content before merge. It does not deploy.

The Hugo version used in CI is pinned via `HUGO_VERSION` in both workflow files — bump it there when upgrading Hugo locally so CI output matches local builds.

The workflow overrides `baseURL` at build time with the URL GitHub Pages reports. Until the custom domain is set up, the site is served for testing at **https://kenyaworks.github.io/Website-Files/**.

### Links must work under a subpath

Because the test site lives under `/Website-Files/`, internal links must not be hard-coded from the site root:

- **Templates:** pass paths to `relURL` **without** a leading slash — `{{ "stories/" | relURL }}`, not `{{ "/stories/" | relURL }}` (a leading slash makes Hugo drop the subpath). Use `.RelPermalink` for pages and resources. Menu entries' `.URL` already includes the subpath — output it as-is.
- **Markdown content:** root-relative links like `[Stories](/stories/)` are fine — `layouts/_default/_markup/render-link.html` rewrites them.
- **Raw HTML in content:** avoid `href="/..."`; use a Markdown link instead.

### One-time setup

In the repository, **Settings → Pages → Build and deployment → Source** must be set to **GitHub Actions**.

### Cutting over to www.kenyaworks.org

`baseURL` in `hugo.toml` is already `https://www.kenyaworks.org/`. When the site is ready to go live:

1. Add a `static/CNAME` file containing `www.kenyaworks.org` so it's copied into every build. **Don't add this earlier** — once a custom domain is set, GitHub redirects the github.io test URL to it.
2. Point DNS at GitHub Pages: a `CNAME` record for `www` → `kenyaworks.github.io` (and optionally A/AAAA records for the apex `kenyaworks.org`).
3. Set the domain in **Settings → Pages → Custom domain** and enable **Enforce HTTPS**.
