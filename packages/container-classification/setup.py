import setuptools

from setuptools import find_namespace_packages

NAME = "container-classification"
VERSION = "0.0.1"
DESCRIPTION = "Provides training, evaluation and inference tooling for patch-based vision models that classify software container images"

setuptools.setup(
    name=NAME,
    version=VERSION,
    description=DESCRIPTION,
    author="Akis Nousias, Efkleidis Katsaros",
    author_email="anousias@k3y.bg, ekatsaros@k3y.bg",
    package_dir={"": "src"},
    packages=find_namespace_packages(where="src"),
    entry_points={
        "console_scripts": [
            "p2code-container-classifier-train = bin.train:main",
            "p2code-container-classifier-infer = bin.infer:main",
            "p2code-container-classifier-explain = bin.explain:main",
            "p2code-container-classifier-evaluate = bin.evaluate:main",
        ],
    },
    install_requires=[
        "torch>=2.0.0",
        "torchvision",
        "opencv-python>=4.8.0",
        "numpy>=1.20.0",
        "scikit-learn>=1.4.0",
        "webdataset>=1.0.0",
        "toml>=0.10",
    ],
    extras_require={
        "dataset": ["huggingface_hub"],
        "log": ["wandb"],
    },
    dependency_links=[
        "https://download.pytorch.org/whl/cpu",
        "https://download.pytorch.org/whl/cpu",
    ],
)
