from typing import List, Dict

import json

from stix2 import File, ObservedData, Malware, Bundle, Report, Grouping

from .structured_security_report import (
    build_stix_file_instance,
    build_stix_observed_data_instance,
    build_stix_malware,
    build_stix_report_instance,
    build_stix_bundle,
    build_stix_grouping,
)


def build_stix_event_for_container_attestation(
    image_name: str, image_tag: str, image_hash: str, image_path: str, clf_results: Dict
) -> List[File | ObservedData | Malware]:
    """
    Build total stix attestation report.

    Parameters
    ----------
    image_name : str
        The container image name.
    image_tag : str
        The container image tag.
    image_hash : str
        The container image path.
    image_path : str
        The container image hash.
    clf_results : Dict
        The container classification results with keys `class` and `probability`.

    Results
    -------
    stix_report_objects : List
        A list of stix object instances.
    """
    # labels = ["benign", "malevolent"]

    stix_objects = []

    label = clf_results["class"]
    proba = clf_results["probability"]

    container_meta = {
        "x_image_name": image_name,
        "x_image_tag": image_tag,
        "x_description": "none",
        "x_hashes": image_hash,
    }

    classification_meta = {
        "x_class": label,
        "x_probability": proba,
    }

    file_instance = build_stix_file_instance(image_path, container_meta)

    data_instance = build_stix_observed_data_instance(
        file_instance, classification_meta
    )

    stix_objects.extend([file_instance, data_instance])

    if label == "malevolent" and proba > 0.5:

        malware_instance = build_stix_malware(
            int(proba * 100), sample_refs=[file_instance]
        )
        stix_objects.append(malware_instance)

    stix_grouping = build_stix_grouping(
        object_refs=stix_objects,
        name="{}:{}".format(image_name, image_tag),
        context="software-container-analysis",
        labels=[label],
    )

    return stix_objects, stix_grouping


def build_stix_attestation_report(container_images_meta: List[Dict]) -> Bundle:
    """
    Example function for building a report from classified container images.

    Parameters
    ----------
    container_images_meta : List[Dict]
        A list of attested container image metadata.

    Returns
    -------
    stix_bundle_instance : Bundle
        An attestation report as a stix Bundle.
    """
    all_stix_grps = []
    all_stix_objs = []
    all_results = []

    for image_meta in container_images_meta:

        image_name = image_meta["name"]
        image_tag = image_meta["tag"]
        image_path = image_meta["path_to_tar"]
        image_hash = image_meta["hash"]

        image_clf_results = image_meta["classification"]

        stix_objects, stix_grouping = build_stix_event_for_container_attestation(
            image_name=image_name,
            image_tag=image_tag,
            image_path=image_path,
            image_hash=image_hash,
            clf_results=image_clf_results,
        )

        all_stix_grps.append(stix_grouping)
        all_stix_objs.extend(stix_objects)
        all_results.append(image_clf_results)

    has_malevolent = any(res["class"] == "malevolent" for res in all_results)

    label_all = "malevolent" if has_malevolent else "benign"

    stix_report_instance = build_stix_report_instance(all_stix_grps, labels=[label_all])

    stix_bundle_instance = build_stix_bundle(
        [stix_report_instance] + all_stix_grps + all_stix_objs
    )

    # NOTE: `stix2` library does not appear to offer a direct `.todict` method
    # and requires a custom function. For now we use the `.serialze()` method
    # and then reload with `json.loads`.
    return json.loads(stix_bundle_instance.serialize())
