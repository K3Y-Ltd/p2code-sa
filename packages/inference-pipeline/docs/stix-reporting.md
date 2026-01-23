# STIX reporting

Attestation results are returned as a STIX 2.1 bundle (JSON). This gives the
API a machine-readable, standard format for reporting evidence, observations,
and malware detections.


## Where it lives in the code

- Report builder: `src/inference_pipeline/stix/stix_report_builder.py`
- STIX object constructors: `src/inference_pipeline/stix/structured_security_report.py`
- Custom extensions: `src/inference_pipeline/stix/stix_custom_extensions.py`
- (Example/custom observable) `src/inference_pipeline/stix/stix_software_container.py`


## Input to the report builder

The builder consumes a list of “attested container image” dictionaries:

```python
{
  "name": "influxdb",
  "tag": "latest",
  "path_to_tar": "/.../container.tar",
  "hash": "sha-like-id-from-docker",
  "classification": {"class": "benign|malevolent", "probability": 0.0}
}
```

This list is assembled in the `POST /attestation` endpoint after each container
is processed.


## Output: a STIX bundle (JSON)

The endpoint stores the STIX bundle JSON in the database and returns it to the
client. Internally:

- STIX objects are built using the `stix2` library.
- The final `stix2.Bundle` is serialized with `.serialize()`.
- The JSON string is converted to a Python dict via `json.loads(...)` because
  `stix2` does not provide a simple `.todict()` helper in this codebase.


## What objects are included

For each container image, `build_stix_event_for_container_attestation(...)`
creates:

1) `stix2.File`
   - Represents the container “artifact” (the tar path is used as the file path).
   - Carries container metadata via a custom extension:
     - `x_image_name`
     - `x_image_tag`
     - `x_description`
     - `x_hashes`

2) `stix2.ObservedData`
   - References the `File` object via `object_refs`.
   - Carries classification metadata via a custom extension:
     - `x_class` (`benign|malevolent`)
     - `x_probability` (float)

3) `stix2.Malware` (conditional)
   - Included only if:
     - `x_class == "malevolent"` and
     - `x_probability > 0.5`
   - The `confidence` value is derived as `int(probability * 100)`.

4) `stix2.Grouping`
   - Groups the per-container objects.
   - Uses `labels=[label]` where label is `benign` or `malevolent`.

After all containers are processed:

5) `stix2.Report`
   - References all container groupings.
   - Its label is `malevolent` if any container result is malevolent; otherwise `benign`.

6) `stix2.Bundle`
   - Contains: the Report, all Groupings, and all per-container objects.


## Custom STIX extensions

Custom extension IDs are defined in `stix_custom_extensions.py`:

- Container extension:
  `extension-definition--d2bb1734-2673-492a-92e8-cafc8daff5a0`
- Classification extension:
  `extension-definition--962d1dd6-d2bb-459c-b374-f140bdf6951d`

They are used as keys in the `extensions={...}` field of STIX objects.


## Practical notes

- The `SoftwareContainer` custom observable in `stix_software_container.py` is
  documented in code comments as not used in the current implementation. The
  service currently represents containers as `stix2.File` plus extensions.
- If you need a stricter definition of when to emit a `Malware` object, change
  the threshold in `build_stix_event_for_container_attestation(...)`.
