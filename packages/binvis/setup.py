import setuptools

from setuptools import find_namespace_packages

NAME = "binvis"
VERSION = "0.0.1"
DESCRIPTION = "Tools for visualizing binary files as images using space-filling curves" 

setuptools.setup(
    name=NAME,
    version=VERSION,
    description=DESCRIPTION,
    author="Akis Nousias",
    author_email="anousias@k3y.bg",
    package_dir={"": "src"},
    packages=find_namespace_packages(where="src"),
    entry_points={
        "console_scripts": [
            "p2code-binvis-visualize-tar = bin.tarfile_visualizer:main",
            "p2code-binvis-visualize-bin = bin.binary_visualizer:main",
            "p2code-binvis-visualize-iter-tar = bin.tarfile_visualizer:main",
            "p2code-binvis-visualize-iter-bin = bin.binary_visualizer:main",
        ],
    },
    install_requires=[
        "pillow>10.0.0",
        "numpy>=1.20.0",
        "scipy>=1.10.0",
        "numpy-hilbert-curve==1.0.1",
    ],
)
