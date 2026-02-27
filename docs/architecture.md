# Architecture: Envoy-based Secure Web Gateway Prototype

## Request flow (default path)

1. Client sends plaintext proxy request to Envoy with `Proxy-Authorization` bearer token.
2. Envoy calls `ext_authz` service (`authz-graph`) before forwarding.
3. `authz-graph`:
   - validates token (prototype-level validation + optional JWKS signature validation)
   - queries Microsoft Graph for `preferredLanguage`
   - caches `preferredLanguage` in Redis (TTL)
   - returns `x-user-lang` response header to Envoy
4. Envoy Lua filter copies `x-user-lang` to `Accept-Language` and strips `x-user-lang`.
5. Envoy uses dynamic forward proxy and TLS origination to upstream HTTPS app.

## Optional TLS break/inspect/modify (CONNECT MITM)

For true HTTPS interception with on-the-fly certificates, run mitmproxy sidecar/container:

- Envoy routes CONNECT traffic to mitmproxy upstream mode.
- mitmproxy dynamically generates leaf certs signed by its local CA.
- For policy experiments, keep core identity/auth in Envoy and implement deep payload checks in mitmproxy addon.

> This split keeps Envoy as the policy control point and uses mitmproxy only for TLSi experiments.

## Components

- **Envoy container**
  - HTTP proxy listener (:8080)
  - ext_authz HTTP filter
  - Lua header policy injection
  - dynamic forward proxy cluster
- **authz-graph container**
  - `POST /check` endpoint compatible with Envoy ext_authz
  - Graph lookup + Redis write-through cache
- **Redis container**
  - key pattern: `user_lang:<oid>`
  - TTL defaults to 1 hour
- **mitmproxy container (optional)**
  - explicit proxy mode on :8081
  - on-the-fly cert generation

## Azure/Kubernetes notes

- Use AKS with workload identity / managed identity for Graph calls where possible.
- Use Azure Cache for Redis in non-local environments.
- Put Envoy behind an internal LB for enterprise egress testing.
- Add Key Vault CSI for secrets (`AAD_CLIENT_ID`, `AAD_CLIENT_SECRET`) if using confidential client flow.
