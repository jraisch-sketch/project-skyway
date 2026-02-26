# Deploy Skyway To AWS (Simple Path)

This path is the least painful for this repo:
- Frontend: AWS Amplify Hosting (Next.js)
- Backend API: AWS App Runner (container from this repo's `backend/Dockerfile`)
- Database: Amazon RDS PostgreSQL

## 1. Prereqs

- AWS account and IAM user with access to Amplify, App Runner, ECR, and RDS.
- App code pushed to GitHub.
- AWS CLI installed and configured locally (`aws configure`).

## 2. Create RDS PostgreSQL

In AWS Console:
1. Go to RDS -> Create database.
2. Engine: PostgreSQL.
3. Template: Free tier (or Dev/Test).
4. Set DB name/user/password and save them.
5. Public access: `Yes` (for quick setup).
6. Security group inbound: allow TCP `5432` from App Runner (or temporarily `0.0.0.0/0` until wiring is done).
7. Create DB and copy the endpoint hostname.

## 3. Build and Push Backend Image to ECR

Set these once:

```bash
export AWS_REGION=us-east-1
export AWS_ACCOUNT_ID=<your-account-id>
export ECR_REPO=skyway-backend
```

Create ECR repo (one-time):

```bash
aws ecr create-repository --repository-name "$ECR_REPO" --region "$AWS_REGION"
```

Build + push:

```bash
cd /Users/johnraisch/Documents/New\ project/backend
aws ecr get-login-password --region "$AWS_REGION" | docker login --username AWS --password-stdin "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"
docker build -t "$ECR_REPO:latest" .
docker tag "$ECR_REPO:latest" "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO:latest"
docker push "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO:latest"
```

## 4. Create App Runner Service (Backend)

In AWS Console:
1. Go to App Runner -> Create service.
2. Source: Container registry -> Amazon ECR.
3. Image URI: `ACCOUNT.dkr.ecr.REGION.amazonaws.com/skyway-backend:latest`
4. Port: `8000`.
5. Environment variables:

```text
DJANGO_SECRET_KEY=<strong-random-secret>
DEBUG=False
ALLOWED_HOSTS=<your-app-runner-domain>
POSTGRES_DB=<db-name>
POSTGRES_USER=<db-user>
POSTGRES_PASSWORD=<db-password>
POSTGRES_HOST=<rds-endpoint-hostname>
POSTGRES_PORT=5432
CORS_ALLOWED_ORIGINS=https://<your-amplify-domain>
CSRF_TRUSTED_ORIGINS=https://<your-amplify-domain>
FRONTEND_URL=https://<your-amplify-domain>
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
DEFAULT_FROM_EMAIL=no-reply@projectskyway.org
USE_S3=False
```

After deploy, copy the App Runner service URL (example: `https://abc123.us-east-1.awsapprunner.com`).

## 5. Deploy Frontend on Amplify

In AWS Console:
1. Go to Amplify -> New app -> Host web app.
2. Connect your GitHub repo.
3. Select the frontend app path: `frontend`.
4. Add environment variables:

```text
NEXT_PUBLIC_API_BASE_URL=/api
API_PROXY_TARGET=http://<your-backend-alb-dns>
```

5. Deploy and copy the Amplify URL.

## 6. Update Backend Allowed Origins

In App Runner service env vars, confirm these values use the real Amplify URL:
- `CORS_ALLOWED_ORIGINS=https://<amplify-domain>`
- `CSRF_TRUSTED_ORIGINS=https://<amplify-domain>`
- `FRONTEND_URL=https://<amplify-domain>`

Then redeploy App Runner.

For custom domains on this project, use explicit comma-separated origins per environment. Example:

```text
# Staging backend service
CORS_ALLOWED_ORIGINS=http://skyway-staging.yjroutdoors.com,http://skyway.yjroutdoors.com
CSRF_TRUSTED_ORIGINS=http://skyway-staging.yjroutdoors.com,http://skyway.yjroutdoors.com
FRONTEND_URL=http://skyway-staging.yjroutdoors.com

# Production backend service
CORS_ALLOWED_ORIGINS=http://skyway.yjroutdoors.com,http://skyway-staging.yjroutdoors.com
CSRF_TRUSTED_ORIGINS=http://skyway.yjroutdoors.com,http://skyway-staging.yjroutdoors.com
FRONTEND_URL=http://skyway.yjroutdoors.com
```

After enabling HTTPS, add `https://` variants to both `CORS_ALLOWED_ORIGINS` and `CSRF_TRUSTED_ORIGINS`.

## 7. Smoke Test

1. Open frontend URL and confirm school list loads.
2. Confirm same-origin API proxy works:

```bash
curl -sS -o /dev/null -w "%{http_code}\n" https://<your-frontend-domain>/api/filters
```

3. Test auth endpoints.
4. Open backend `/admin` and log in with superuser.

If you need a superuser, run once:

```bash
cd /Users/johnraisch/Documents/New\ project/backend
python manage.py createsuperuser
```

(Run this against the production DB using the same env vars as App Runner.)

## 8. Optional Hardening (After MVP Works)

- Move DB to private networking and attach App Runner VPC connector.
- Replace console email backend with SES.
- Add custom domains in Amplify and App Runner.
- Store secrets in AWS Secrets Manager.
