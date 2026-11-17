# Deployment

## Status at 17 November 2026

Local implementation is separate from production deployment. No production service or DNS record has yet been created. GitHub CLI and browser require sign-in; Render and Supabase also require sign-in. Vercel browser is signed in, but its integration is not connected. The connected GitHub tool does not expose repository creation. A phone sign-in does not establish a computer session.

## Database

Create a Supabase project without accepting paid upgrades. Follow https://supabase.com/docs/guides/database/extensions/postgis to enable PostGIS. Inspect its installed extension schema before applying the migration. Run versioned migrations and the snapshot loader documented in backend/README.md. Use a least-privilege read-only application role. Keep migration credentials separate and never expose DATABASE_URL in Vite variables.

## Render backend

Import the repository using render.yaml. Set DATABASE_URL as a secret and CORS_ORIGINS to the frontend HTTPS origin. Use the manifest build/start commands. Verify /healthz and /readyz, then a real /api/site-insight request. Snapshot mode does not verify PostGIS deployment. Record the actual provider URL here after creation.

Free Render instances can sleep. Before the interview, consider the smallest always-on tier shown in the dashboard. No purchase is authorised or made. See https://render.com/docs/deploy-fastapi and https://render.com/docs/health-checks.

## Vercel frontend

Import the GitHub repository with frontend as root directory. Build with npm ci and npm run build; output directory dist. Set VITE_API_BASE_URL to the verified Render HTTPS URL. Test the Vercel-generated URL anonymously before configuring a custom domain.

## Release verification

Run the documented test suite and build. On the actual public URL test map clicks, layer toggles, sources, community selection, desktop/tablet/mobile layouts, HTTPS and API readiness. Only then create presentation_assets/site-preview.png from the deployed app, generate custom-domain QR codes and decode them to verify the target. A local screenshot is not a deployed screenshot.
