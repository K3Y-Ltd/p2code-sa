from typing import Dict, List

import os
import datetime

import stix2

from .stix_custom_extensions import (
    CONTAINER_EXT_ID,
    CLASSIFICATION_EXT_ID,
)

# NOTE:
# Currently a container is represented by a `stix2.File` instance with the
# custom `SoftwareContainerExtension` defined in `stix_custom_extensions.py`.
#
# The classification results are represented by a `stix2.ObservedData`
# instance that refers to the container `stix2.File` instance and holds
# the classification through the custom `ClassificationResultsExtension`
# defined in `stix_custom_extensions.py`.
#
# If a malware is detected an additional `stix2.Malware` instance is defined.


def build_stix_file_instance(file_path: str, container_meta: Dict) -> stix2.File:
    """
    Build a STIX `File` instance.

    Parameters
    ----------
    file_path : str
        Path to file.
    container_kw : Dict
        A dictionary with container metadata with expected keys:
        'x_image_name', 'x_image_tag', 'x_description', 'x_hashes'

    Returns
    -------
    stix2.File
        A `File` instance with attached metadata for software containers.
    """
    # Get file name and size
    _, name = os.path.split(file_path)
    name, _ = os.path.splitext(name)

    size = None

    return stix2.File(
        name=name,
        size=size,
        extensions={
            CONTAINER_EXT_ID: container_meta,
            # {
            #     "x_image_name": "benign",
            #     "x_image_tag": "0.0.1",
            #     "x_description": "dummy desc",
            #     "x_hashes": hash("DUMMYDUMMY"),
            # }
        },
    )


def build_stix_observed_data_instance(
    file_instance: stix2.File, classification_meta
) -> stix2.ObservedData:
    """
    Build a STIX `ObservedData` instance.

    Parameters
    ----------
    file_instance : stix2.File
        Path to `stix2.File` instance related to the `ObservedData`.
    classification_meta : Dict
        A dictionary with classification metadata with expected keys:
        'x_class' and 'x_probability'.

    Returns
    -------
    stix2.ObservedData
        An `ObservedData` instance with attached metadata for
        classification results.
    """
    timestamp = datetime.datetime.now()

    return stix2.ObservedData(
        first_observed=timestamp,
        last_observed=timestamp,
        number_observed=1,
        object_refs=[file_instance],
        extensions={
            CLASSIFICATION_EXT_ID: classification_meta,
            # {
            #     "x_class": "benign",
            #     "x_probability": 0.994,
            # },
        },
    )


def build_stix_malware(confidence: int, sample_refs: List[stix2.File]) -> stix2.Malware:
    """
    Build a STIX `Malware` instance.

    Parameters
    ----------
    confidence : int
        Corresponds to the classifier's probability output.
    sample_refs : List[stix2.File]
        References to the file or files that include the specific malware.

    Returns
    -------
    stix2.Malware
        A `Malware` instance.
    """
    name = "unknown_malware"

    description = (
        "Unknown malware detected using a machine learning model "
        "in a Docker container."
    )

    return stix2.Malware(
        name=name,
        description=description,
        malware_types=["unknown"],
        is_family=False,
        labels=["docker", "machine learning detection"],
        confidence=confidence,
        architecture_execution_envs=["x64"],
        implementation_languages=["unknown"],
        capabilities="compromise-containers",
        sample_refs=sample_refs,
    )


def build_stix_grouping(object_refs: List, **kwargs) -> stix2.Grouping:
    """
    Build a STIX `Grouping` object.

    Returns
    -------
    stix2.Grouping
        A `stix2.Grouping` object.
    """
    return stix2.Grouping(object_refs=object_refs, **kwargs)


def build_stix_bundle(stix_objects) -> stix2.Bundle:
    """
    Build a STIX `Bundle` object.

    Returns
    -------
    stix2.Bundle
        A `stix2.Bundle` object.
    """
    return stix2.Bundle(stix_objects)


def build_stix_report_instance(object_refs, **kwargs) -> stix2.Report:
    """
    Build a STIX `Report` object.

    Parameters
    ----------
    object_refs : List[str] | List[]

    Returns
    -------
    stix2.Report
        A `stix.Report` object.
    """
    name = "container-malware-detection-report"

    report_types = [
        "threat-report",
        "observed-data",
        "malware",
    ]

    header = (
        "Structured Security Report to hold the detection results "
        "of the Malware Detection Component applied on a group of "
        "software instances packaged as docker containers."
    )

    if "description" not in kwargs:
        description = header
    else:
        description = "\n".join([header, kwargs["description"]])

    published = datetime.datetime.now()

    return stix2.Report(
        name=name,
        report_types=report_types,
        description=description,
        published=published,
        object_refs=object_refs,
        **kwargs
    )


def build_structured_security_report(stix_objects):
    """
    Build a Structured Security Report based on STIX standard.
    """
    stix_report = build_stix_report_instance(stix_objects)

    stix_bundle = build_stix_bundle([stix_report] + stix_objects)

    return stix_bundle


def build_course_of_action() -> stix2.CourseOfAction:
    """
    Build a STIX `Course of Action` object.

    Returns
    -------
    stix_coa : Dict
        A dictionary defining a STIX `Course of Action` object.
    """
    return stix2.CourseOfAction()
