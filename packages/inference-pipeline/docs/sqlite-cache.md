# SQLite cache and internal database

The inference API is designed to be repeatable and efficient: if you submit the
same YAML again, the service returns a cached response instead of re-running
Docker export, `binvis` image generation, and ML inference.

This caching is implemented using an internal SQLAlchemy-backed database
(typically SQLite).


## Where it lives in the code

- DB initialization and sessions: `src/inference_pipeline/database/db.py`
- Table schema: `src/inference_pipeline/database/models.py`
- Repository methods: `src/inference_pipeline/database/repositories.py`
- Cache check on requests: `src/inference_pipeline/api/inference_endpoint.py`


## Database URL and file location

The DB URL comes from the config:

```yaml
database:
  uri: "sqlite:///data/database.db"
```

For SQLite URLs that start with `sqlite:///`, the service ensures the parent
directory exists before creating the engine.


## Schema: `inference_results`

The `InferenceResult` model (`database/models.py`) stores:

- `id` (integer primary key)
- `sa_hash` (string): hash of the submitted YAML body
- `created_at` (datetime)
- `stix_report` (JSON): the STIX bundle returned to clients
- `application_area` (integer): the model selector from `aa=<int>`
- `status` (enum): `pending|completed|failed`


## What is cached (and how the key is computed)

Cache key:
- The service computes an MD5 hash of the *raw YAML string* using
  `compute_hash(data: str) -> str` (`src/inference_pipeline/utils.py`).

Cache lookup:
- On `POST /attestation`, the service checks `InferenceRepository.get_by_sa_hash(...)`.
- If a record exists, it returns the stored STIX report immediately.

Write path:
- After a successful attestation run, `InferenceRepository.create_record(...)`
  inserts a new row and sets `status=COMPLETED`.

There are two layers of caching:

1. **Cross-request cache (SQLite)**: avoids repeating work across API calls for
the same YAML.

2. **Per-request service cache (in-memory)**: within a single attestation run,
the service caches results by `(image_name, image_tag)` so duplicate services
in the YAML do not trigger duplicate Docker export/inference.


## Operational notes

- The service is synchronous: there is no background job processing and no
  status transitions over time. Status is effectively `completed` for stored
  results, and error cases are returned as HTTP errors.
- SQLite is a good fit for single-instance deployments and local testing. For
  multi-instance deployments you typically want a shared database URL.
