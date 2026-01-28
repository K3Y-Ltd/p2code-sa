# Inference Pipeline

The `inference-pipeline` package implements a REST service (Flask) that performs 
“software attestation” on software containers. The service, given a “service order”,
i.e. a list of to-be-deployed services, attests them whether they have been malware
compromised. The attestation results are organized in the form a report using the 
STIX 2.1 standard.

More specifically, the service performs the following steps:

1. Receive a `docker-compose` YAML or a Kubernetes/Helm `values.yaml`-like YAML.
2. Extract the referenced container images.
3. For each image, create and export a container filesystem as a `.tar`.
4. Convert the tar archive into a 1024×1024 RGB image using `binvis`.
5. Classify the image using one of several pre-trained models from `container-classification`.
6. Return a STIX 2.1 report and cache results in an internal SQLite database.


## Installation (monorepo)

From the repository root (in development mode):

```bash
pip install -e packages/binvis
pip install -e packages/container-classification
pip install -e packages/inference-pipeline
```

Notes:
- This package imports `binvis` and `container-classification` at runtime.


## Quick start

Start the API server:

```bash
p2code-inference-pipeline --cfg_path packages/inference-pipeline/cfgs/config.yaml
```

By default, `cfgs/config.yaml` runs Flask on `127.0.0.1:8000`.

### Minimal attestation request (docker-compose)

Send a request with `Content-Type: application/x-yaml` and query parameter `aa`
(application area), where `aa` selects which loaded model to use.

```bash
curl -X POST "http://127.0.0.1:8000/attestation?aa=1" \
  -H "Content-Type: application/x-yaml" \
  --data-binary $'services:\n  influxdb:\n    image: influxdb:latest\n'
```

The response is in JSON format with two fields:
- `metadata`: request/result metadata + HATEOAS links
- `data`: a STIX bundle (JSON)


## API endpoints

Base URL is `http://<host>:<port>` from the Flask config.

### Health and Readiness Endpoints

- `GET /api/healthz` → `{ "status": "alive" }`
- `GET /api/ready` → `{ "status": "ready" }` (checks DB connectivity)
- `GET /api/db` → `{ "status": "database is running" }` (checks DB connectivity)

Examples:

```bash
curl http://127.0.0.1:8000/api/healthz
curl http://127.0.0.1:8000/api/ready
```

### Attestation Endpoints


#### `POST /attestation?aa=<int>`

Creates (or returns a cached) attestation result.

Requirements:
- Query param `aa`: integer application area (used to select the ML model).
- Header `Content-Type: application/x-yaml`
- Body: YAML text representing either:
  - `docker-compose` (must contain top-level `services`)
  - Kubernetes/Helm values-style YAML (no `services` key; parsed heuristically)

Response (high level):

```json
{
  "metadata": {
    "id": 123,
    "created_at": "2025-01-01T00:00:00.000000",
    "application_area": 1,
    "status": "completed",
    "links": [
      { "rel": "self", "href": "/attestation/123", "method": "GET" },
      { "rel": "report", "href": "/attestation/123/report", "method": "GET" },
      { "rel": "status", "href": "/attestation/123/status", "method": "GET" }
    ]
  },
  "data": { "...": "STIX bundle (JSON)" }
}
```

Given a service order the service computes an MD5 of the raw YAML request body 
and looks up an existing attestation in its database. If found, it returns it 
without re-running Docker/binvis/model inference.


#### `GET /attestation`

Lists all cached attestations.

Response:

```json
{
  "metadata": { "total": 2 },
  "data": [
    { "id": 1, "created_at": "...", "application_area": 1, "status": "completed" }
  ]
}
```

Example:

```bash
curl http://127.0.0.1:8000/attestation
```


#### `GET /attestation/<id>`

Returns the full result for a specific attestation id (metadata + STIX report).


#### `GET /attestation/<id>/report`

Returns only:

```json
{ "data": { "...": "STIX bundle (JSON)" } }
```


#### `GET /attestation/<id>/status`

Returns:

```json
{ "status": "pending|completed|failed" }
```

Example:

```bash
curl http://127.0.0.1:8000/attestation/123/status
curl http://127.0.0.1:8000/attestation/123/report
```

## Configuration

The server entry point is `src/bin/inference_api.py`. It loads a YAML config and
passes it into the Flask app factory. The config file requires the following fields:
- `flask`: Configuration arguments to be passed to a flask app configuration via `app.config.update`.
- `logging`: Configuration arguments passed to `logging.config`.
- `database`: Configuration arguments for initialization of an sqlite database.
- `models`: Configuration arguments for machine learning models:
  - `models.path`: Directory containing model checkpoints.
  - `models.files`: A list of checkpoint filenames, one for each application area. 

The models are assigned to application areas based on their given order and mapped 
to keys `1..N`. Then the request query param `aa=<int>` selects `models[aa]`.


## Dependencies and integrations

This package builds on:

- `binvis` to convert exported container tar files into a consistent RGB image
  representation (Hilbert layout, unrolled).
- `container-classification` to load PyTorch checkpoints and run patch-based
  inference returning `{ "class": "...", "probability": ... }`.
- `stix2` to format the final output as a STIX bundle.
- Docker engine access (`docker` SDK) to materialize/export images.

The integration details are documented in:

- `docs/sqlite-cache.md`
- `docs/stix-reporting.md`
- `docs/dependencies-binvis.md`
- `docs/dependencies-container-classification.md`


## Operational assumptions (important)

- The service reads Docker registry credentials from environment variables:
  - `CONTAINER_REGISTRY` (default: `ghcr.io`)
  - `CONTAINER_REGISTRY_USERNAME`
  - `CONTAINER_REGISTRY_TOKEN`
- The service pulls images from specified remote repository.
- Model checkpoints must match the `container-classification` checkpoint format
  i.e. a `.pth` dict containing a `state` key with the model weights.
