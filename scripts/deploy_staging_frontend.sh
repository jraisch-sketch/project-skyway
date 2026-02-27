#!/usr/bin/env bash
set -euo pipefail

AWS_REGION="${AWS_REGION:-us-east-1}"
AWS_ACCOUNT_ID="${AWS_ACCOUNT_ID:-647420212384}"
ECR_REPO="${ECR_REPO:-skyway-frontend-staging}"
ECS_CLUSTER="${ECS_CLUSTER:-skyway-staging-cluster}"
ECS_SERVICE="${ECS_SERVICE:-skyway-frontend-staging-service}"
TASK_FAMILY="${TASK_FAMILY:-skyway-frontend-staging-task}"

NEXT_PUBLIC_API_BASE_URL="${NEXT_PUBLIC_API_BASE_URL:-/api}"
NEXT_PUBLIC_ENV="${NEXT_PUBLIC_ENV:-staging}"
API_PROXY_TARGET="${API_PROXY_TARGET:-http://skyway-staging-alb-1191650900.us-east-1.elb.amazonaws.com}"

VERIFY_ROUTE="${VERIFY_ROUTE:-/favorites}"
VERIFY_EXPECT_JS="${VERIFY_EXPECT_JS:-data-label}"
VERIFY_EXPECT_CSS="${VERIFY_EXPECT_CSS:-favorites-table tbody tr}"

usage() {
  cat <<'EOF'
Usage: scripts/deploy_staging_frontend.sh

Builds and deploys staging frontend with guardrails:
- docker buildx with explicit linux/amd64 platform
- pushes image tag based on current git SHA
- registers new ECS task definition revision for staging service
- waits for ECS service stability
- runs strict staging frontend verification checks
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

for cmd in aws docker jq git; do
  command -v "$cmd" >/dev/null 2>&1 || { echo "Missing command: $cmd" >&2; exit 1; }
done
docker buildx version >/dev/null 2>&1 || {
  echo "docker buildx is required" >&2
  exit 1
}

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Must run inside git repository" >&2
  exit 1
fi

GIT_SHA="$(git rev-parse --short HEAD)"
TAG="staging-${GIT_SHA}-ga-amd64"
IMAGE_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO}:${TAG}"

echo "[INFO] Deploying frontend image: ${IMAGE_URI}"

aws ecr get-login-password --region "${AWS_REGION}" \
  | docker login --username AWS --password-stdin "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

docker buildx build \
  --platform linux/amd64 \
  --build-arg NEXT_PUBLIC_API_BASE_URL="${NEXT_PUBLIC_API_BASE_URL}" \
  --build-arg NEXT_PUBLIC_ENV="${NEXT_PUBLIC_ENV}" \
  --build-arg API_PROXY_TARGET="${API_PROXY_TARGET}" \
  -t "${IMAGE_URI}" \
  --push \
  frontend

CURRENT_TASK_DEF_ARN="$(
  aws ecs describe-services \
    --region "${AWS_REGION}" \
    --cluster "${ECS_CLUSTER}" \
    --services "${ECS_SERVICE}" \
    --query 'services[0].taskDefinition' \
    --output text
)"

TMP_IN="$(mktemp /tmp/skyway-front-task-in.XXXXXX)"
TMP_OUT="$(mktemp /tmp/skyway-front-task-out.XXXXXX)"
trap 'rm -f "$TMP_IN" "$TMP_OUT"' EXIT

aws ecs describe-task-definition \
  --region "${AWS_REGION}" \
  --task-definition "${CURRENT_TASK_DEF_ARN}" \
  --query 'taskDefinition.{family:family,taskRoleArn:taskRoleArn,executionRoleArn:executionRoleArn,networkMode:networkMode,containerDefinitions:containerDefinitions,volumes:volumes,placementConstraints:placementConstraints,requiresCompatibilities:requiresCompatibilities,cpu:cpu,memory:memory,runtimePlatform:runtimePlatform}' \
  --output json > "${TMP_IN}"

jq --arg image "${IMAGE_URI}" '
  (.containerDefinitions[] | select(.name=="frontend") | .image) = $image
  | .runtimePlatform = {"operatingSystemFamily":"LINUX","cpuArchitecture":"X86_64"}
' "${TMP_IN}" > "${TMP_OUT}"

NEW_TASK_DEF_ARN="$(
  aws ecs register-task-definition \
    --region "${AWS_REGION}" \
    --cli-input-json "file://${TMP_OUT}" \
    --query 'taskDefinition.taskDefinitionArn' \
    --output text
)"

echo "[INFO] New task definition: ${NEW_TASK_DEF_ARN}"

aws ecs update-service \
  --region "${AWS_REGION}" \
  --cluster "${ECS_CLUSTER}" \
  --service "${ECS_SERVICE}" \
  --task-definition "${NEW_TASK_DEF_ARN}" >/dev/null

aws ecs wait services-stable \
  --region "${AWS_REGION}" \
  --cluster "${ECS_CLUSTER}" \
  --services "${ECS_SERVICE}"

echo "[INFO] ECS service stable. Running strict staging verification."

./scripts/verify_staging_frontend.sh \
  --route "${VERIFY_ROUTE}" \
  --expect-js "${VERIFY_EXPECT_JS}" \
  --expect-css "${VERIFY_EXPECT_CSS}"

echo "[OK] Staging frontend deploy complete: ${IMAGE_URI}"
