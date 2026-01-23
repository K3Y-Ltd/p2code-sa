from .utils import cntr_msg

_LOGGING_APP_INIT = {
    "log__app_init": "Initializing Software Attestation Service",
}

_LOGGING_APP = {
    "log__docker_init": "Step 1: Initializing docker client",
    "log__models_validate": "Step 2: Validating ML models",
    "log__models_load": "Step 3: Loading ML models",
    "log__db_init": "Step 4: Initializing internal database",
    "log__reg_endpoints": "Step 5: Registering application endpoints",
}

LOGGING_APP = {}
LOGGING_APP.update({k: cntr_msg(msg) for k, msg in _LOGGING_APP_INIT.items()})
LOGGING_APP.update({k: msg for k, msg in _LOGGING_APP.items()})

_LOGGING_INFERENCE_OVERALL = {
    "log__receive_request": "Received Software Attestation request",
}

_LOGGING_INFERENCE_ORDER = {
    "log__parse_request": "Step 1: Parsing request content",
    "log__init_sa_process": "Step 2: Initializing Software Attestation process",
    "log__init_sa_sequentially": "Step 3: Attesting services sequentially",
    "log__create_attestation_report": "Step 4: Creating STIX attestation report",
    "log__cache_response": "Step 5: Caching software attestation response",
}

_LOGGING_INFERENCE_CONTAINER = {
    "log__attest_service": "Attesting service: {}",
    "log__create_container": "Creating dockerized container",
    "log__export_container": "Exporting dockerized container to TAR file.",
    "log__create_image": "Generating container RGB image representation",
    "log__infer": "Attest with ML model",
    "log__parse_response": "Parse ML model response",
    "log__clear_docker": "Remove docker images and containers",
}

LOGGING_INFERENCE = {}
LOGGING_INFERENCE.update(
    {k: cntr_msg(msg) for k, msg in _LOGGING_INFERENCE_OVERALL.items()}
)
LOGGING_INFERENCE.update({k: msg for k, msg in _LOGGING_INFERENCE_ORDER.items()})
LOGGING_INFERENCE.update({k: msg for k, msg in _LOGGING_INFERENCE_CONTAINER.items()})
