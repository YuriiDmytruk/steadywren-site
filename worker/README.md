# Contact form Worker

`POST https://api.steadywren.com/contact` with JSON `{ email, message, topics: [one], website: "" }` sends the
message as an email (Cloudflare Email Routing `send_email` binding). `website` is a honeypot: when filled, the Worker
answers 200 and sends nothing. CORS allows only the site's origins.

- `src/handler.js` - validation, MIME message, response (plain JS, tested with Node).
- `src/index.js` - Worker entry (`cloudflare:email`).
- `node test.mjs` - tests.

## Deploy (once, then after changes)
Needs: Email Routing enabled on `steadywren.com` with the owner's inbox as a verified destination address, and a
Cloudflare API token with Workers Scripts: Edit + Workers Routes: Edit + Zone: Read for the zone.
```bash
npx wrangler deploy
```
```bash
npx wrangler secret put TO
```
(`TO` = the verified destination address.) Check: `curl -i -X OPTIONS https://api.steadywren.com/contact` returns
204, and a test message from the site arrives in the inbox.
