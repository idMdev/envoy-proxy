# Envoy L7 Secure Web Gateway Prototype

This repository contains a **prototype** secure web gateway architecture for local macOS testing and Azure/Kubernetes deployment.

## What this prototype demonstrates

- Plaintext HTTP proxy entrypoint for clients (`http://<gateway>:8080`)
- Entra ID token-based authorization via `Proxy-Authorization: Bearer <token>`
- User enrichment via Microsoft Graph (`preferredLanguage`)
- Redis session/user cache for language lookup
- Header injection policy (`Accept-Language`) before egress
- TLS origination to upstream HTTPS destinations
- Optional sidecar TLS interception path with on-the-fly cert generation (mitmproxy)

See [docs/architecture.md](docs/architecture.md) for details.

## Quick start (local)

```bash
docker compose up --build
```

Proxy endpoint:

- `http://localhost:8080`

Redis:

- `localhost:6379`

## Repo layout

- `envoy/` - Envoy bootstrap and filter chain
- `authz-graph/` - ext_authz service (token check + Graph + Redis)
- `mitmproxy/` - optional TLS break/inspect sidecar config
- `k8s/` - Kubernetes manifests for local clusters/AKS
- `docs/` - architecture and deployment notes

