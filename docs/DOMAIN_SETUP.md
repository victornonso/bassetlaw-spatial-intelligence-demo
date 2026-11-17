# Verified subdomain configuration

Vercel project: bassetlaw-spatial-intelligence-demo
Production frontend: https://bassetlaw-spatial-intelligence-demo.vercel.app
Requested custom hostname: bassetlaw-demo.victorokeke.co.uk

Vercel returned the following exact record on 17 November 2026:

| Type | Host/name | Target/value | Proxy | TTL |
| --- | --- | --- | --- | --- |
| CNAME | bassetlaw-demo | b6c9698c1fac8db0.vercel-dns-017.com. | Disabled (DNS only) | Auto or 300 seconds |

The DNS provider is Cloudflare, as identified by Vercel. Only create/update this exact subdomain; do not change root, www, nameservers or other records.

After saving, check the CNAME resolves, refresh this project's Vercel domain status, wait for the managed TLS certificate and test HTTPS, HTTP redirect and the API from the custom hostname. Do not generate custom-domain QR codes before this succeeds.

Status: active. Cloudflare CNAME saved with DNS-only proxy state and Auto TTL on 17 November 2026. Vercel reports Valid Configuration. Public HTTPS returns 200 with valid managed TLS; HTTP returns 308 to HTTPS. The application was opened on the actual custom hostname. Existing root, www and verification records were retained. No DNS action remains.
