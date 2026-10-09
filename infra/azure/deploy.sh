#!/usr/bin/env bash
# Deploy Rely Match Brain to Azure Container Apps.
# Prerequisites: Azure CLI logged in (az login), Bicep available (az bicep install).
# Usage:  RG=rely-brain-rg LOCATION=westeurope ACR=relybrainacr ./infra/azure/deploy.sh
# Optional Foundry: AI_PROVIDER=microsoft_foundry FOUNDRY_ENDPOINT=... FOUNDRY_MODEL=... FOUNDRY_API_KEY=... (read from env, never committed)
set -euo pipefail

RG="${RG:-rely-brain-rg}"
LOCATION="${LOCATION:-westeurope}"
ACR="${ACR:-relybrainacr$RANDOM}"
PREFIX="${PREFIX:-relybrain}"
TAG="${TAG:-$(git rev-parse --short HEAD 2>/dev/null || echo latest)}"
AI_PROVIDER="${AI_PROVIDER:-none}"
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

az group create -n "$RG" -l "$LOCATION" -o none
az acr create -g "$RG" -n "$ACR" --sku Basic --admin-enabled true -o none
ACR_SERVER="$(az acr show -n "$ACR" --query loginServer -o tsv)"
ACR_USER="$(az acr credential show -n "$ACR" --query username -o tsv)"
ACR_PASS="$(az acr credential show -n "$ACR" --query 'passwords[0].value' -o tsv)"

echo "Building API image in ACR..."
az acr build -r "$ACR" -t "rely-brain-api:$TAG" -f "$ROOT/apps/api/Dockerfile" "$ROOT" -o none

# The web image needs the public API URL at build time. Container Apps FQDNs are
# <app>.<environment default domain>, so create the environment first to learn the domain.
az deployment group create -g "$RG" -f "$ROOT/infra/azure/main.bicep" -o none \
  -p prefix="$PREFIX" acrServer="$ACR_SERVER" acrUsername="$ACR_USER" acrPassword="$ACR_PASS" \
     apiImage="$ACR_SERVER/rely-brain-api:$TAG" webImage="mcr.microsoft.com/k8se/quickstart:latest" \
     aiProvider="$AI_PROVIDER" foundryEndpoint="${FOUNDRY_ENDPOINT:-}" foundryModel="${FOUNDRY_MODEL:-gpt-4o-mini}" \
     foundryApiKey="${FOUNDRY_API_KEY:-}"
API_URL="https://$(az containerapp show -g "$RG" -n "$PREFIX-api" --query properties.configuration.ingress.fqdn -o tsv)"

echo "Building web image against $API_URL ..."
az acr build -r "$ACR" -t "rely-brain-web:$TAG" --build-arg NEXT_PUBLIC_API_URL="$API_URL" "$ROOT/apps/web" -o none

az deployment group create -g "$RG" -f "$ROOT/infra/azure/main.bicep" -o none \
  -p prefix="$PREFIX" acrServer="$ACR_SERVER" acrUsername="$ACR_USER" acrPassword="$ACR_PASS" \
     apiImage="$ACR_SERVER/rely-brain-api:$TAG" webImage="$ACR_SERVER/rely-brain-web:$TAG" \
     aiProvider="$AI_PROVIDER" foundryEndpoint="${FOUNDRY_ENDPOINT:-}" foundryModel="${FOUNDRY_MODEL:-gpt-4o-mini}" \
     foundryApiKey="${FOUNDRY_API_KEY:-}"

WEB_URL="https://$(az containerapp show -g "$RG" -n "$PREFIX-web" --query properties.configuration.ingress.fqdn -o tsv)"
echo "API: $API_URL   (health: $API_URL/health, ready: $API_URL/ready)"
echo "Web: $WEB_URL"
