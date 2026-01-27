# Software Attestation

<div align="center">

[![arxiv](https://img.shields.io/badge/arXiv-2504.03238-b31b1b.svg?style=flat-square)](https://arxiv.org/abs/2504.03238)
[![huggingface](https://img.shields.io/badge/🤗%20Hugging%20Face-10.57967/hf/5853-FFD21E.svg?style=flat-square)](https://huggingface.co/datasets/k3ylabs/cosoco-image-dataset)

</div>

![software-attestation-architecture](/docs/p2code-software-attestation-architecture-overview.png)

This repository holds code for the P2CODE component of Software Attestation (SA). The repository is organized
as a monorepo, holding a set of Python packages with complementary functionalities that cover basic stages
of the Software Attestation lifecycle. The packages included are the following:

- **BinVis**: A Python package for visualizing binary files as images using space-filling curves. The supports
  handling visualizing binary files up to several GBs. ([docs](./packages/binvis/README.md))

- **Container Classification**: A Python package that provides training, evaluation and inference tooling for 
  patch-based vision models that classify image representations of software containers. ([docs](./packages/container-classification/README.md))

- **Inference Pipeline**: A Python package that wraps Software Attestation as a REST service ([docs](./packages/inference-pipeline/README.md)).

References:
- **[Dataset]**(https://huggingface.co/datasets/k3ylabs/cosoco-image-dataset)
- **[Paper]**(https://ieeexplore.ieee.org/document/11161263) 
- **[Preprint]**(https://arxiv.org/abs/2504.03238)


## Usage

Software Attestation is a security component that attests an input service order in the form of a `docker-compose` file
or a Kubernetes Helm chart and identifies services that have been malware compromised. The Software Attestation service
can be deployed as a service behind a REST API or deployed as a container. For more information go through the [docs](./packages/inference-pipeline/README.md).


## Installation

The Software Attestation functionality is supported by three python packages that can be installed as-is 
in a virtual environment such as `conda` or `venv`. The packages located under the `packages` folder are:
* `binvis`
* `container-classification`
* `inference-pipeline`


### Installation as packages

Preferably, create a new python environment to hold the package installations. Make sure that the new environment
includes basic installation libraries such as `wheel` and `pip`. Usually, these are supported by default for new 
`conda` and `venv` environments. 

For each package, navigate to the package's `setup.py` file and build a package `.whl` file:
```
python setup.py bdist_wheel 
```

Install the packages via their `.whl` files using `pip`:
```
pip install <my-package>.whl
```

### Installation in development mode

Alternativelly, the packages can be installed in editable mode by navigating to the corresponding package folder 
and execute an editable installation as follows:
```
pip install -e ./src
```


## References

Software Attestation is accompanied by the following publications:

* A. Nousias, E. Katsaros, E. Syrmos, P.R. Grammatikis, T. Lagkas, V. Argyriou, I. Moscholios, E. Markakis, S. Goudos and . Sarigiannidis, “Malware Detection in Docker Containers: An Image is Worth a Thousand Logs”, ICC-W 2025 - IEEE International Conference on Communications Workshops, 2025, doi: 10.1109/ICC52391.2025.11161263.

with the following bibtex entry:

```bibtex
@inproceedings{Nousias2025-kg,
  title           = "Malware detection in docker containers: An image is worth
                     a thousand logs",
  booktitle       = "{ICC} 2025 - {IEEE} International Conference on
                     Communications",
  author          = "Nousias, Akis and Katsaros, Efklidis and Syrmos, Evangelos
                     and Radoglou-Grammatikis, Panagiotis and Lagkas, Thomas
                     and Argyriou, Vasileios and Moscholios, Ioannis and
                     Markakis, Evangelos and Goudos, Sotirios and
                     Sarigiannidis, Panagiotis",
  publisher       = "IEEE",
  pages           = "6401--6407",
  month           =  jun,
  year            =  2025,
  conference      = "ICC 2025 - IEEE International Conference on Communications",
  location        = "Montreal, QC, Canada"
}
```

* A. Nousias E. Katsaros, E. Syrmos, P.R. Grammatikis, T. Lagkas, V. Argyriou, I. Moscholios, E. Markakis, S. Goudos and P. Sarigiannidis, COSOCO Image Dataset (Revision fd5a8dd) . Hugging Face , 2025. doi: 10.57967/hf/5853 .

with the bibtex entry:
```bibtex
@MISC{Nousias2025-nl,
  title     = "cosoco-image-dataset",
  author    = "Nousias, Akis and Katsaros, Efklidis and Syrmos, Evangelos and
               Radoglou-Grammatikis, Panagiotis and Lagkas, Thomas and
               Argyriou, Vasileios and Moscholios, Ioannis and Markakis,
               Evangelos and Goudos, Sotirios and Sarigiannidis, Panagiotis",
  publisher = "Hugging Face",
  year      =  2025
}
```
