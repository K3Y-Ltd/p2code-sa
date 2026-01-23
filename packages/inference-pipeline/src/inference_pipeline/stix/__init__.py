"""
The output of the Software Attestation service follows the STIX 2.1 specification. STIX is
a specification widely used in cyber-security for sharing cyber-intelligence information
and includes a series of abstractions for representing cyber-security entities, relations 
and actions.   

The Software Attestation report comprises the following STIX objects:
- `STIX Report`
- `STIX Grouping`
- `STIX File`
- `STIX ObservedData`
- `STIX Malware`

The JSON response is a flat list (STIX bundle) of STIX objects and consists of:

- A `STIX Report`:

  This is always the first element of the list. The report holds the overall attestation
  label along with pointers to the attestation results for each service separately.

  ```
  report = response["objects"][0]

  report_label = report["labels][0]
  ```

- A number of `STIX Grouping` elements which correspond to the number of services being attested. 

  The attestation result for each separate service is represented by a `STIX Grouping`.
  The attestation result is stored to the objects "labels" key and can be retrieved as
  as in:

  ```
  attested_services_uids = report["object_refs"]

  srvcs = [obj for obj in response["objects"] if obj["id"] in attested_services_uids]    
    
  for srvc in srvcs:
        
      srvc_label = srvc["labels"][0]

      print("For service `{name}` the label is `'{label}'`".format(name=srvc["name"], label=srvc_label))
  ```

  The `STIX Grouping` instances include pointers to the corresponding `STIX File`, `STIX Observed
  Data` and `STIX Malware` instances related to the attested service including further metadata.

- A number of `STIX File`, `STIX Observed Data` and optionally a `STIX Malware` if a malware was detected.
  These can be accessed in a similar way with the groupings by retrieving the referenced objects via
  the `"object_refs"` key and searching these objects through the overall `STIX bundle`.

-------
Example
-------
```
[
    {
        "name": "ghcr.io/k3y-ltd/test-01",
        "tag": "0.0.1",
        "path_to_tar": ".",
        "hash": "sha256:7dfac52e5676a2a42981b36aa94062baba3f2931f1a72acbf1a4602a5180eede",
        "classification": {"class": "benign", "probability": 0.9434},
    },
    {
        "name": "ghcr.io/k3y-ltd/test-02",
        "tag": "0.0.2",
        "path_to_tar": ".",
        "hash": "sha256:7dfac52e5676a2a42981b36aa94062baba3f2931f1a72acbf1a4602a5180eede",
        "classification": {"class": "malevolent", "probability": 0.854},
    },
]
```
"""

from .stix_report_builder import (
    build_stix_event_for_container_attestation,
    build_stix_attestation_report,
)
