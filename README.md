# House Tracker — v10 polished

Final polish build. Filters are collapsed by default, Grid/List view is explicit and responsive, and light mode has stronger contrast. The weekly source checker can capture an exact listing page OpenGraph image as a source-linked preview and conservatively detect floorplan image tags. Unverified media is never invented.

# House Tracker — Final Discovery Release

Mobile-first UK house-hunting tracker for the 2028–29 search.

## v5 highlights
- Personal search dashboard with tracked homes, favourites, shortlist and viewing counts
- Favourites page and compare shortlist
- Shortlist tiers: Top shortlist, Maybe, Passed/Rejected
- Shortlist-tier filtering
- Compare up to 4 homes with CSV export and print-friendly comparison
- Transparent, configurable match weights for price, garden, location, bedrooms, parking and energy
- Custom theme accent colours, dark/light mode, grid/list mode and compact density
- Custom budget, bedroom minimum and must-have features
- Personal buying planner: deposit, mortgage rate, term, SDLT estimate, legal fees, moving costs and initial works
- Per-property estimated cash required and monthly mortgage payment based on your own assumptions
- Viewing workflow: status, viewing date, notes, pros, cons, questions and a mobile-friendly viewing checklist
- Recently viewed tracking
- Local tracked price history: records future observed changes while you use the tracker; it does not invent historical prices
- Saved searches with one-tap reapplication
- Share/copy listing links, Google Maps shortcut and exact image-search shortcut
- Manual local property add
- Full local backup export/import including personal decisions and price history
- PWA/service-worker caching for better phone use
- Wider-market searches across Rightmove, Zoopla, OnTheMarket and Google
- Exact-listing photo policy: no generic images are presented as property photos
- Existing scheduled GitHub workflow retained

## Data separation
The repository's scheduled workflow updates verified property data. Your favourites, shortlist tiers, notes, viewing records, checklist, saved searches, price snapshots and settings live in browser localStorage and are not overwritten by the scheduled property update.

Manual properties are local-only and are not written back to GitHub.

## Planning estimates
Mortgage and cash-needed figures are personal planning estimates. SDLT and other purchase costs are entered by the user rather than hard-coded, so the tracker does not silently rely on a tax rule that may change.

## Trust / source policy
Exact listing links are preserved. Property photos are only embedded when an exact source image has been verified; otherwise the tracker sends you to the listing's own gallery. Floorplans are never fabricated.

## Vercel
The project is already connected to GitHub. Push changes to `main` and Vercel should redeploy automatically.

## Local test
```bash
python -m http.server 8000
```
Then open `http://localhost:8000/`.

## v7 media evidence
v7 separates property media into verified photos, exact floorplans, and plot/site plans. The UI only embeds direct image URLs when they are explicitly present in the property data. If no direct image has been verified, it links to the exact listing gallery instead of using generic imagery. Floorplans and plot plans use the same rule. This prevents a house-type plan or unrelated image from being presented as the exact property.

Media fields:
- `media.photos`: direct, verified property image URLs only
- `media.galleryUrl`: exact listing/gallery page
- `media.floorplan`: `{ "url": "...", "label": "...", "source": "..." }` only when the exact plan image is verified
- `media.plotplan`: `{ "url": "...", "label": "...", "source": "..." }` only when the exact plot/site plan image is verified


## v8 reliability additions
- Data Quality tab separates missing evidence from verified fields.
- Repository-backed observed price history is recorded by the scheduled source-check script.
- Local price history can use repository observations as a fallback.
- Backup timestamp is shown in Settings after an export.
- External verification shortcuts are provided for flood risk, planning, broadband and council-tax checks.
- No source failure is interpreted as a sale or removal automatically.


## Final personal features
- My House Search dashboard with editable priorities and progress
- Watchlist without automatic alerts
- Property lifecycle/decision history
- Personal property ratings
- Property-specific improvement projects and costs
- Property snapshot export
- Differences-only comparison
- Personal notes, shortlist and financial planning remain separate from market data
- Accessibility/mobile/performance features from v7/v8 retained


## Weekly discovery workload

The GitHub Actions workflow runs every Sunday at 07:00 Europe/London. It:

1. checks existing tracked listing URLs and records observed source status/title/price;
2. maintains repository-backed observed price history;
3. searches configured priority areas across Rightmove, Zoopla and OnTheMarket through public search indexing;
4. stores newly discovered exact listing URLs in `data/discovery_history.json` as **candidates requiring verification**;
5. never promotes an unverified candidate into the trusted property dataset or invents garden, floorplan, availability, tenure, parking or incentive facts;
6. commits only the resulting source/discovery data back to `main`, allowing the existing Vercel connection to redeploy.

Discovery is intentionally conservative because portal pages can change, block automated access, or expose incomplete search snippets. A candidate is a lead for review, not a claim that it matches every house-search requirement.


## Privacy and public-repository safety
Personal tracker state is stored in the browser only: favourites, notes, ratings, viewing records, watchlist state, projects, decisions, saved searches, financial assumptions and other personal settings are not written by the scheduled GitHub workflow. Manual properties are local-only.

The repository contains an automated public-data audit (`scripts/audit_public_data.py`). The weekly workflow runs this audit before committing; it fails if recognised personal tracker fields appear in the public JSON data files. Backup files are also excluded by `.gitignore`.

There is therefore no personal-data encryption key stored in the public repository because personal data is not supposed to be stored there at all. GitHub Actions secrets are appropriate for future API credentials or other sensitive values; GitHub encrypts secrets before storage and redacts them in workflow logs. Do not put personal backups or passwords into `properties.json` or other public files.

Browser `localStorage` is not encryption. Anyone with access to the same browser profile/device can potentially inspect it. For especially sensitive future data, use an encrypted/password-protected backup or a private authenticated backend rather than committing it to this public repository.

## Weekly discovery safeguards
- Maximum 50 newly discovered candidates are added per run.
- Discovery candidates remain explicitly `needs_verification` and never become trusted properties automatically.
- If every discovery query fails, the previous candidate set is preserved and the run is recorded as failed rather than treating the failure as an empty market.
- Existing property data is never wiped because a source becomes temporarily unreachable.
- The workflow uses an explicit `Europe/London` schedule so the 07:00 run follows UK daylight-saving changes.
- The first source check naturally establishes a baseline because no previous observed price exists, so it does not invent a price change.
