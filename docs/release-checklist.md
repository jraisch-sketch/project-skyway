# Skyway Staging + Production Release Checklist

## 1) Environment Setup (One-Time)

- [ ] Create separate backend services:
  - [ ] `skyway-backend-staging` (App Runner)
  - [ ] `skyway-backend-prod` (App Runner)
- [ ] Create separate databases:
  - [ ] `skyway-staging` (RDS PostgreSQL)
  - [ ] `skyway-prod` (RDS PostgreSQL)
- [ ] Create separate frontend deployments (Amplify):
  - [ ] staging branch/site
  - [ ] production branch/site
- [ ] Use separate backend image tags per environment:
  - [ ] staging tags (example: `staging-<sha>`)
  - [ ] prod tags (example: `prod-<sha>`)

## 2) Branch + Promotion Model

- [ ] `main` deploys to **staging**
- [ ] `release` (or a release tag from `main`) deploys to **production**
- [ ] Do not deploy production directly from feature branches

## 3) Required Environment Variables

### Backend (set separately for staging and prod)

- [ ] `DJANGO_SECRET_KEY`
- [ ] `DEBUG=False`
- [ ] `ALLOWED_HOSTS`
- [ ] `POSTGRES_DB`
- [ ] `POSTGRES_USER`
- [ ] `POSTGRES_PASSWORD`
- [ ] `POSTGRES_HOST`
- [ ] `POSTGRES_PORT=5432`
- [ ] `CORS_ALLOWED_ORIGINS`
- [ ] `CSRF_TRUSTED_ORIGINS`
- [ ] `FRONTEND_URL`

Reference values for current domains:

- Staging backend:
  - `CORS_ALLOWED_ORIGINS=http://skyway-staging.yjroutdoors.com,http://skyway.yjroutdoors.com`
  - `CSRF_TRUSTED_ORIGINS=http://skyway-staging.yjroutdoors.com,http://skyway.yjroutdoors.com`
  - `FRONTEND_URL=http://skyway-staging.yjroutdoors.com`
- Production backend:
  - `CORS_ALLOWED_ORIGINS=http://skyway.yjroutdoors.com,http://skyway-staging.yjroutdoors.com`
  - `CSRF_TRUSTED_ORIGINS=http://skyway.yjroutdoors.com,http://skyway-staging.yjroutdoors.com`
  - `FRONTEND_URL=http://skyway.yjroutdoors.com`

When HTTPS is enabled, include `https://` variants in both CORS/CSRF values.

### Frontend (set separately for staging and prod)

- [ ] `NEXT_PUBLIC_API_BASE_URL=/api` (same-origin API path on custom domain)
- [ ] `API_PROXY_TARGET` points to matching backend ALB origin (no trailing slash)

Reference values currently observed:

- Staging frontend:
  - `NEXT_PUBLIC_API_BASE_URL=/api`
  - `API_PROXY_TARGET=http://skyway-staging-alb-1191650900.us-east-1.elb.amazonaws.com`
- Production frontend:
  - `NEXT_PUBLIC_API_BASE_URL=/api`
  - `API_PROXY_TARGET=http://skyway-prod-alb-300389705.us-east-1.elb.amazonaws.com`

SSL + API parity rule:
- [ ] Frontend ALB keeps `80 -> 443` redirect
- [ ] Frontend ALB keeps HTTPS listener with ACM cert + TLS policy
- [ ] `https://<domain>/api/filters` returns `200` in both staging and production

## 4) Data Separation Rules

- [ ] Staging backend must use staging DB only
- [ ] Production backend must use production DB only
- [ ] Separate admin accounts/passwords for staging and production
- [ ] Never test destructive scripts against production first

## 5) Staging Deployment Checklist

- [ ] Merge feature PR into `main`
- [ ] Build and push backend image tagged for staging
- [ ] Deploy staging App Runner to new staging image
- [ ] Run Django migrations in staging
- [ ] Confirm staging frontend points to staging backend URL

## 6) Staging QA Checklist (Go/No-Go Gate)

- [ ] Home page loads
- [ ] Map pins render and counts match expected behavior
- [ ] Search/filter/sort work
- [ ] Login/register/password reset work
- [ ] Favorites add/remove/list works
- [ ] Admin login works
- [ ] API health checks:
  - [ ] `GET /api/filters/` -> 200
  - [ ] `GET /api/schools/` -> 200
  - [ ] CORS check for staging domain returns `Access-Control-Allow-Origin`:
    - [ ] `curl -sS -D - -o /dev/null -H "Origin: http://skyway-staging.yjroutdoors.com" http://skyway-staging-alb-1191650900.us-east-1.elb.amazonaws.com/api/filters/`

## 7) Production Deployment Checklist

- [ ] Promote approved build to `release` (or create approved release tag)
- [ ] Deploy production App Runner to prod image tag
- [ ] Run Django migrations in production
- [ ] Confirm production frontend points to production backend URL
- [ ] Run quick smoke tests on production:
  - [ ] Home + map
  - [ ] Search/filter
  - [ ] Auth flow
  - [ ] Favorites
  - [ ] CORS check for production domain returns `Access-Control-Allow-Origin`:
    - [ ] `curl -sS -D - -o /dev/null -H "Origin: http://skyway.yjroutdoors.com" http://skyway-prod-alb-300389705.us-east-1.elb.amazonaws.com/api/filters/`

## 8) Rollback Procedure

- [ ] Keep previous known-good image tag recorded for each deploy
- [ ] If issue detected:
  - [ ] Redeploy previous backend image tag
  - [ ] Re-verify smoke tests
- [ ] If database rollback is required:
  - [ ] Restore from latest RDS snapshot
  - [ ] Notify stakeholders before and after restore

## 9) Governance (Simple, Solo-Friendly)

- [ ] Protect `release` branch (require PR merge)
- [ ] Use PRs for all feature work (even solo)
- [ ] Record each production deploy in a short release note:
  - [ ] commit/tag
  - [ ] timestamp
  - [ ] deployer
  - [ ] rollback tag
