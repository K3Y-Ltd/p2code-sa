import stix2

from stix2.properties import (
    StringProperty,
    FloatProperty,
)

# Those who use the extension definition will use the same fixed ID to refer to it.
CLASSIFICATION_EXT_ID = "extension-definition--962d1dd6-d2bb-459c-b374-f140bdf6951d"
CONTAINER_EXT_ID = "extension-definition--d2bb1734-2673-492a-92e8-cafc8daff5a0"


@stix2.v21.CustomExtension(
    CLASSIFICATION_EXT_ID,
    [
        ("x_class", StringProperty(required=True)),
        ("x_probability", FloatProperty(required=True)),
    ],
)
class ClassificationResultsExtension:
    extension_type = "property-extension"


@stix2.v21.CustomExtension(
    CONTAINER_EXT_ID,
    [
        ("x_image_name", StringProperty(required=True)),
        ("x_image_tag", StringProperty()),
        ("x_description", StringProperty()),
        ("x_hashes", StringProperty()),
    ],
)
class SoftwareContainerExtension:
    extension_type = "property-extension"
