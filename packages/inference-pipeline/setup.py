from setuptools import setup, find_namespace_packages

NAME = "p2code-sa-inference-pipeline"
VERSION = "0.0.1"
DESCRIPTION = "REST service that supports 'software attestation' on dockerized software containers."

setup(
    name=NAME,
    version=VERSION,
    description=DESCRIPTION,
    author="Evangelos Syrmos, Akis Nousias, Efkleidis Katsaros",
    author_email="esysrmos@k3y.bg, anousias@k3y.bg, ekatsaros@k3y.bg",
    package_dir={"": "src"},
    packages=find_namespace_packages(where="src"),
    entry_points={
        "console_scripts": [
            "p2code-inference-pipeline = bin.inference_api:main",
        ],
    },
    install_requires=[
        "PyYAML>=6.0.0",
        "stix2>=3.0.1",
        "docker>=7.0.0",
        "Flask>=3.1.0",
        "sqlalchemy>=1.4.0",
    ],
)
