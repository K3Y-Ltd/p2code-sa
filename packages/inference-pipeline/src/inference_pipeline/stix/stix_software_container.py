import stix2

from stix2.properties import (
    StringProperty,
    IntegerProperty,
    ExtensionsProperty,
)
from stix2.v21.vocab import EXTENSION_TYPE_NEW_SDO


# Those who use the extension definition will use the same fixed ID to refer to it.
CONTAINER_EXT_ID = "extension-definition--d2bb1734-2673-492a-92e8-cafc8daff5a0"

software_container_ext = stix2.ExtensionDefinition(
    id=CONTAINER_EXT_ID,
    created_by_ref="identity--87c30030-82c5-4e7c-a253-db6d9782ce3a",
    name="x-software-container",
    schema="A software container object",
    version="0.0.1",
    extension_types=[EXTENSION_TYPE_NEW_SDO],
)

# NOTE: 
# This class `SoftwareContainer` is NOT used in the current implementation. 
# Currently a container is represented by a `stix2.File` instance with the
# custom `SoftwareContainerExtension` defined in `stix_custom_extensions.py`.
# 
# The class would be used inplace as a customly defined stix instance. It is
# left here as an implementation example.

@stix2.CustomObservable(
    "x-software-container",
    [
        ("x_image_name", StringProperty(required=True)),
        ("x_image_tag", StringProperty()),
        ("x_hashes", StringProperty()),
        ("x_description", StringProperty()),
        ("x_size", IntegerProperty()),
        ("classification_results", ExtensionsProperty()),
    ],
    extension_name=CONTAINER_EXT_ID,
)
class SoftwareContainer:
    """
    Custom Software Container object of type stix2.CustomObject.

    Custom Properties
    -----------------
    name : str
        The input software container name.
    tag : str
        The input software container tag.
    hashes : str
        A hash of the input file.
    description : str
        A description of the software container.
    size : int
        The size in bytes of the software container.
    classification_results : Dict
        The classification results after applying a model to the
        software container.
    """

    pass


# print(software_container_ext.serialize(pretty=True))

# software_container = SoftwareContainer(
#     name="benign-1", tag="0.0.1", hashes="", description="", size=1234
# )

# print(software_container.serialize(pretty=True))
