# House Tracker — upgraded static build

A phone-friendly static house-search dashboard for a future first-home purchase.

## Included
- 12 tracked homes/developments from the current tracker dataset.
- Search across road, area, development and notes.
- Price, bedrooms, property type, garden and status filters.
- Garage, driveway, solar, EV, freehold and Walsall-priority filters.
- Best-match sorting plus price/bed/garden sorting.
- Favourites saved locally in the browser.
- Compare up to 4 properties side-by-side.
- Property detail modal with source links and verification notes.
- Personal viewing notes saved locally on the device.
- Export favourites/comparisons/notes to a JSON backup.
- Responsive mobile layout.
- Explicit garden labels and conservative conversion-potential labels.
- No invented photographs or floorplans.

## Important data rule
This build deliberately distinguishes facts previously recorded from information that needs rechecking. A property marked **Verify** must be checked against the live original listing before relying on its price, availability, garden, incentives, EPC, solar/EV or other changing information.

## Run locally
The site is plain HTML/CSS/JavaScript. No npm or build step is required.

If you have Python:

    python -m http.server 8000

Then open http://localhost:8000

## Vercel
The project can be deployed as a static site. Keep `index.html` and `properties.json` together in the deployment root. Vercel can serve static files without a build step.

## GitHub Pages alternative
Because the repository is public, GitHub Pages is also available on GitHub Free. It can publish static files directly from the repository.

## Future upgrades
- Actual listing photos and plot/floorplan previews only when sourced from the exact listing/developer.
- Weekly data-change import.
- Price-history timeline.
- Map view and travel-time checks.
- Development/plot tracker with release dates.
- Viewing checklist and offer calculator.
- Mortgage/SDLT/LISA planning tools.
- Cloud-synced favourites when a backend is added.

## Scheduled updates

This build includes a free GitHub Actions updater. Once the repository is public and this workflow is committed, GitHub checks every tracked listing URL each Sunday at 07:00 Europe/London and can also be run manually from **Actions → House Tracker — scheduled update → Run workflow**. GitHub Actions standard runners are free for public repositories.

The updater is deliberately conservative: it records source reachability and obvious observed title/price signals, but **does not infer that a property is sold, available, reduced, or withdrawn solely from an HTTP response**. Any observed price change is flagged for manual verification.

The website displays the resulting data after the next deployment. If the Vercel project is connected to this GitHub repository, a workflow commit can trigger a new deployment automatically.

This cannot reliably discover every new property on the open market without a property-search API or a search provider. The scheduled updater therefore monitors the exact tracked listings safely rather than pretending to have complete market coverage.
