// Rely Match Brain on Azure Container Apps (API + web), with health probes and Log Analytics.
// Deploy with infra/azure/deploy.sh (builds images in ACR, then deploys this template).
// NOTE: not yet compiled with the Bicep CLI or deployed by the authors (no Azure CLI/subscription on the build machine).

@description('Location for all resources')
param location string = resourceGroup().location

@description('Short prefix for resource names')
param prefix string = 'relybrain'

@description('Azure Container Registry login server, e.g. myacr.azurecr.io')
param acrServer string

@description('ACR username (admin user)')
param acrUsername string

@secure()
@description('ACR password (admin user)')
param acrPassword string

@description('API image, e.g. myacr.azurecr.io/rely-brain-api:1.0.0')
param apiImage string

@description('Web image, e.g. myacr.azurecr.io/rely-brain-web:1.0.0 (built with NEXT_PUBLIC_API_URL pointing at the API)')
param webImage string

@allowed(['none', 'microsoft_foundry'])
param aiProvider string = 'none'

@description('Azure AI Foundry model inference endpoint (only used when aiProvider = microsoft_foundry)')
param foundryEndpoint string = ''

@description('Deployed model name in Azure AI Foundry')
param foundryModel string = 'gpt-4o-mini'

@secure()
param foundryApiKey string = ''

resource logs 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: '${prefix}-logs'
  location: location
  properties: { sku: { name: 'PerGB2018' }, retentionInDays: 30 }
}

resource env 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: '${prefix}-env'
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: { customerId: logs.properties.customerId, sharedKey: logs.listKeys().primarySharedKey }
    }
  }
}

var webFqdn = '${prefix}-web.${env.properties.defaultDomain}'

resource api 'Microsoft.App/containerApps@2024-03-01' = {
  name: '${prefix}-api'
  location: location
  properties: {
    managedEnvironmentId: env.id
    configuration: {
      ingress: { external: true, targetPort: 8000, transport: 'auto', allowInsecure: false }
      registries: [ { server: acrServer, username: acrUsername, passwordSecretRef: 'acr-password' } ]
      secrets: [
        { name: 'acr-password', value: acrPassword }
        { name: 'foundry-api-key', value: empty(foundryApiKey) ? 'unset' : foundryApiKey }
      ]
    }
    template: {
      containers: [
        {
          name: 'api'
          image: apiImage
          resources: { cpu: json('0.5'), memory: '1Gi' }
          env: [
            { name: 'AI_PROVIDER', value: aiProvider }
            { name: 'FOUNDRY_ENDPOINT', value: foundryEndpoint }
            { name: 'FOUNDRY_MODEL', value: foundryModel }
            { name: 'FOUNDRY_API_KEY', secretRef: 'foundry-api-key' }
            { name: 'CORS_ORIGINS', value: 'https://${webFqdn}' }
            { name: 'LOG_LEVEL', value: 'INFO' }
          ]
          probes: [
            { type: 'Liveness', httpGet: { path: '/health', port: 8000 }, initialDelaySeconds: 5, periodSeconds: 15 }
            { type: 'Readiness', httpGet: { path: '/ready', port: 8000 }, initialDelaySeconds: 5, periodSeconds: 10 }
            { type: 'Startup', httpGet: { path: '/health', port: 8000 }, periodSeconds: 5, failureThreshold: 12 }
          ]
        }
      ]
      scale: { minReplicas: 1, maxReplicas: 3, rules: [ { name: 'http', http: { metadata: { concurrentRequests: '50' } } } ] }
    }
  }
}

resource web 'Microsoft.App/containerApps@2024-03-01' = {
  name: '${prefix}-web'
  location: location
  properties: {
    managedEnvironmentId: env.id
    configuration: {
      ingress: { external: true, targetPort: 3000, transport: 'auto', allowInsecure: false }
      registries: [ { server: acrServer, username: acrUsername, passwordSecretRef: 'acr-password' } ]
      secrets: [ { name: 'acr-password', value: acrPassword } ]
    }
    template: {
      containers: [
        {
          name: 'web'
          image: webImage
          resources: { cpu: json('0.5'), memory: '1Gi' }
          probes: [
            { type: 'Liveness', httpGet: { path: '/health', port: 3000 }, initialDelaySeconds: 5, periodSeconds: 15 }
            { type: 'Readiness', httpGet: { path: '/health', port: 3000 }, initialDelaySeconds: 5, periodSeconds: 10 }
          ]
        }
      ]
      scale: { minReplicas: 1, maxReplicas: 2 }
    }
  }
}

output apiUrl string = 'https://${api.properties.configuration.ingress.fqdn}'
output webUrl string = 'https://${web.properties.configuration.ingress.fqdn}'
