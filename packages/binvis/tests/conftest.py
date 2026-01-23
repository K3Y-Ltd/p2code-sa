import os
import json
import pytest

from pathlib import Path

from .constants import (
    _out_range32_byte_class,
    _out_range32_byte_value,
    _out_range64_byte_class,
    _out_range64_byte_value,
    _out_range256_byte_class,
    _out_range256_byte_value,
    _out_ascii8_byte_class,
    _out_ascii8_byte_value,
)


# data fixtures: inputs
# - range32
# - range64
# - range256
# - ascii8
@pytest.fixture(scope="module")
def bin_range32():
    return bytes(range(32))


@pytest.fixture(scope="session")
def bin_range64():
    return bytes(range(64))


@pytest.fixture(scope="session")
def bin_range256():
    return bytes(range(256))


@pytest.fixture(scope="session")
def bin_ascii8():
    return bytes("abcdefgh", "ascii")


# data fixtures: outputs for colormaps ColorByteClass & ColorByteValue
# - range32
# - range64
# - range256
# - ascii8
@pytest.fixture(scope="session")
def out_range32_byte_class():
    return _out_range32_byte_class


@pytest.fixture(scope="session")
def out_range32_byte_value():
    return _out_range32_byte_value


@pytest.fixture(scope="session")
def out_range64_byte_class():
    return _out_range64_byte_class


@pytest.fixture(scope="session")
def out_range64_byte_value():
    return _out_range64_byte_value


@pytest.fixture(scope="session")
def out_range256_byte_value():
    return _out_range256_byte_value


@pytest.fixture(scope="session")
def out_range256_byte_class():
    return _out_range256_byte_class


@pytest.fixture(scope="session")
def out_ascii8_byte_value():
    return _out_ascii8_byte_value


@pytest.fixture(scope="session")
def out_ascii8_byte_class():
    return _out_ascii8_byte_class


# data_fixtures: input factories
@pytest.fixture
def make_bin_range_n():
    def _make_bin_range_n(n: int) -> bytes:
        return bytes((i % 256 for i in range(n)))

    return _make_bin_range_n


@pytest.fixture
def make_bin_text():
    def _make_bin_text(text: str) -> bytes:
        return bytes(text, "ascii")

    return _make_bin_text


# file fixtures
@pytest.fixture(scope="session")
def bin_file_range32(tmp_path_factory):
    tmp_file_path = tmp_path_factory.mktemp("data") / "range32.bin"

    with open(tmp_file_path, mode="wb") as f:
        f.write(bytes(range(32)))

    yield tmp_file_path

    os.remove(tmp_file_path)


@pytest.fixture(scope="session")
def bin_file_range64(tmp_path_factory):
    tmp_file_path = tmp_path_factory.mktemp("data") / "range64.bin"

    with open(tmp_file_path, mode="wb") as f:
        f.write(bytes(range(64)))

    yield tmp_file_path

    os.remove(tmp_file_path)


@pytest.fixture(scope="session")
def bin_file_range256(tmp_path_factory):
    tmp_file_path = tmp_path_factory.mktemp("data") / "range256.bin"

    with open(tmp_file_path, mode="wb") as f:
        f.write(bytes(range(256)))

    yield tmp_file_path

    os.remove(tmp_file_path)


@pytest.fixture(scope="session")
def bin_file_ascii8(tmp_path_factory):
    tmp_file_path = tmp_path_factory.mktemp("data") / "ascii.bin"

    with open(tmp_file_path, mode="wb") as f:
        f.write(bytes("abcdefgh", "ascii"))

    yield tmp_file_path

    os.remove(tmp_file_path)


@pytest.fixture(scope="session")
def golden_base_dir() -> Path:
    return Path(__file__).resolve().parent / "data"
