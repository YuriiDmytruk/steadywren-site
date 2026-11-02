# steadywren.com

Static site of [Steadywren](https://steadywren.com), served by GitHub Pages from this repo's root.

- `python3 build.py` - builds every page from `data/catalog.json`, `content/*.md` and `assets/` (no dependencies).
- New product: add it to `data/catalog.json` (+ image in `assets/products/`), run the build, commit.
- `worker/` - Cloudflare Worker behind the contact form (`api.steadywren.com`).
- Platform logos in `assets/platforms/` come from each platform's official source (see `data/catalog.json`).
