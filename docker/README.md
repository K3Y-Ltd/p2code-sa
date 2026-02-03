# P2CODE Software Attestation Docker Setup

This document the required steps of deploying the Software Attestation component as
a dockerized application. 

For this guide, we take for granted that we have already trained machine learning models
that operate on dockerized software containers, as described in the provided package
`container-classification`.

The Software Attestation service uses a Docker-in-Docker (DinD) setup, as the containerized
service under test needs to be pulled from the remote registry, built and exported to a `.tar`
file, which is converted to an RGB image and further parsed by the other steps of the service. 

For the DinD setup, we use as base image the `cruizba/ubuntu-dind`.


## Notes on Isolation & Security

Executing the Software Attestation component using a Docker-in-Docker setup comes with
security considerations, especially since the docker service inside is used on services
that may have been compromised by malware.

A solution is to use sandboxing with a solution like Sysbox. Sysbox is an open-source 
and free container runtime (a specialized "runc"), originally developed by Nestybox acquired 
by Docker, that enhances isolation and allows execution of system-level software such as 
docker inside docker containers. More information on Sysbox, and Sysbox installation 
instructions can be found [here](https://github.com/nestybox/sysbox).

Although Sysbox is acceptable for handling potentially hostile images under good hygiene,
it may not be enough from a security standpoint. A malicious image may still exploit the
inner Docker daemon during `pull/unpack/export` phase or exploit the container runtime /
kernel boundary.

For *development purposes only*, we can use the `--privileged` flag instead.


## Setup

To run Software Attestation as a containerized service, follow the steps below:

* Build the python packages from `src` as `.wheel` files and copy them to the `/docker/dist` folder.

* Use the trained models from the `container-classification` package to populate the `/docker/models` folder.

* Configure accordingly the application via the `/cfgs/config.yaml` file.

* Build the docker image via a build command:
```bash
docker build -f ./p2code-docker-in-docker-base.Dockerfile -t p2code-inference-pipeline .
```


## Execution via `docker-compose`

Before executing Software Attestation we need to provide credentials for the remote registry 
containing the services under test, by specifying them in a `.env` file:

```
CONTAINER_REGISTRY=<REGISTRY>
CONTAINER_REGISTRY_USERNAME=<USERNAME>
CONTAINER_REGISTRY_TOKEN=<TOKEN>
```

Then the execution of Software Attestation can take place by via `/docker/docker-compose.yaml` 
simply as:
```bash
docker compose -f /path/to/docker-compose.yaml up
```

**Note**: Check the flags regarding `privileged: true` and `runtime: sysbox-runc` in the `docker-compose.yaml`
before execution. Verify that the running container uses `sysbox-runc` via the following command:

```bash
docker inspect -f '{{ .HostConfig.Runtime }}' docker-p2code-inference-pipeline-1
```


## Execution via `docker run`

Executing via `docker run` using the Sysbox runtime `sysbox-runc`:
```bash
docker run \
    --runtime=sysbox-runc \
    --ipc=host \
    -v ./cfgs/config.yaml:/usr/src/p2code/cfgs/config.yaml:ro \
    -e 'CONTAINER_REGISTRY=<TARGET_REGISTRY>' \
    -e 'CONTAINER_REGISTRY_USERNAME=<USERNAME>' \ 
    -e 'CONTAINER_REGISTRY_TOKEN=<TOKEN>' \
    -it p2code-inference-pipeline:latest
```

or via the `--privileged` flag (for *development purposes only*):
```bash
docker run \
    --ipc=host \
    -v ./cfgs/config.yaml:/usr/src/p2code/cfgs/config.yaml:ro \
    -e 'CONTAINER_REGISTRY=<TARGET_REGISTRY>' \
    -e 'CONTAINER_REGISTRY_USERNAME=<USERNAME>' \ 
    -e 'CONTAINER_REGISTRY_TOKEN=<TOKEN>' \
    -it --privileged p2code-inference-pipeline:latest
```

**Note**: In the above commands the flag `--ipc-host` uses all host resources for the Software 
Attestation ML models. These need to be configured separately and based on the host capabilities.
