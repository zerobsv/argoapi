# Document API

A small FastAPI REST API backed by SQLite. FastAPI provides an interactive
Swagger UI at `/docs` and an OpenAPI schema at `/openapi.json`.

## API

Create a document with `POST /documents`:

```json
{
  "id": 1,
  "name": "xyz",
  "phone_name": ["a", "b", "c"],
  "location": "abc"
}
```

The endpoint returns the created document with status `201`. IDs are supplied
by the client and must be unique; a duplicate ID returns `409`.

Retrieve it with `GET /document/1`. An unknown ID returns `404`.

## Run locally

```sh
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python -m app.main
```

The server listens on `127.0.0.1:8000`. Alternatively, run it with
`uvicorn app.main:app --reload` for automatic reloading during development.
The database is created as `documents.db` in the current directory. Override
its location with the `DATABASE_PATH` environment variable.

## Build and run the container

```sh
docker build -t document-api:1.0.0 .
docker tag document-api:1.0.0 YOUR_REGISTRY/document-api:1.0.0
docker push YOUR_REGISTRY/document-api:1.0.0
docker run --rm -p 8000:8000 -v document-data:/data document-api:1.0.0
```

Open [http://localhost:8000](http://localhost:8000) or
[http://localhost:8000/docs](http://localhost:8000/docs) for Swagger UI.

## Deploy with Helm

The Helm chart in [`helm/`](./helm/) contains the Kubernetes Deployment,
ClusterIP Service, and a PersistentVolumeClaim for the SQLite database. Build
and push the image to a registry reachable by your cluster, then set the image
repository and tag:

```sh
helm upgrade --install document-api ./helm \
  --namespace document-api --create-namespace \
  --set image.repository=YOUR_REGISTRY/document-api \
  --set image.tag=1.0.0
```

To access the API locally:

```sh
kubectl -n document-api port-forward svc/document-api 8000:8000
```

Then visit `http://localhost:8000/docs`.

## Deploy with Argo CD

1. Build and push the container image to a registry accessible by the cluster.
2. Edit [`argocd/application.yaml`](./argocd/application.yaml): replace
   `repoURL` with the Git repository URL containing this chart and replace
   `YOUR_REGISTRY` in `spec.source.helm.values` with your container registry.
3. Commit and push the project to the configured repository.
4. Apply the Argo CD Application manifest:

   ```sh
   kubectl apply -f argocd/application.yaml
   ```

Argo CD syncs the chart from the repository's `helm` directory into the
`document-api` namespace using the configured image.
