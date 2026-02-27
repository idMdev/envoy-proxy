# Kubernetes deployment notes

`prototype.yaml` includes Deployments/Services for Redis, authz-graph, and Envoy.

Before applying:

1. Build/push `authz-graph` image and replace `YOUR_REGISTRY/authz-graph:prototype`.
2. Create Envoy config ConfigMap from `envoy/envoy.yaml`:

```bash
kubectl -n envoy-gateway create configmap envoy-config --from-file=envoy.yaml=../envoy/envoy.yaml
```

3. Apply resources:

```bash
kubectl apply -f prototype.yaml
```
