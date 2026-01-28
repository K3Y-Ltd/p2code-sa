import os

import pytest
import tarfile

import numpy as np

from binvis.colormap import (
    ColorByteClass,
    ColorByteValue,
    ColorByteEntropy,
    ColorTarFileStructure,
    ColorMixer,
)

from binvis.colormap_iter import (
    IterableColorByteClass,
    IterableColorByteValue,
    IterableColorTarFileStructure,
    IterableColorMixer,
)


@pytest.mark.parametrize("n_s", [1, 4, 8, 16, 32, 64, 128, 256, 512, 1024])
def test_colormap_np_shape(n_s):
    """
    Test colormap classes input/output shape handling.
    """

    clss = [
        ColorByteClass,
        ColorByteValue,
    ]

    for size in range(n_s):
        for _cls in clss:

            cmap = _cls(bytes([b % 256 for b in range(size)]))

            assert len(cmap) == size

            clrs = cmap.get_point_np(np.arange(size, dtype="int32"), mode="L")

            assert clrs.shape == (size, 1)


@pytest.mark.parametrize(
    "cmap_cls, in_bin_str, out_clr_str",
    [
        ("color_byte_class", "bin_range32", "out_range32_byte_class"),
        ("color_byte_value", "bin_range32", "out_range32_byte_value"),
        ("color_byte_class", "bin_range64", "out_range64_byte_class"),
        ("color_byte_value", "bin_range64", "out_range64_byte_value"),
        ("color_byte_class", "bin_range256", "out_range256_byte_class"),
        ("color_byte_value", "bin_range256", "out_range256_byte_value"),
        ("color_byte_class", "bin_ascii8", "out_ascii8_byte_class"),
        ("color_byte_value", "bin_ascii8", "out_ascii8_byte_value"),
    ],
)
def test_colormap_np_out(request, cmap_cls, in_bin_str, out_clr_str):
    """
    Test colormap outputs.
    """
    _cmap_clss = {
        "color_byte_class": ColorByteClass,
        "color_byte_value": ColorByteValue,
    }

    in_bin = request.getfixturevalue(in_bin_str)
    out_clr = request.getfixturevalue(out_clr_str)

    n = len(in_bin)

    _cmap_cls = _cmap_clss[cmap_cls]

    cmap = _cmap_cls(in_bin)
    clrs = cmap.get_point_np(np.arange(n, dtype="int32"), mode="L")

    assert clrs.tolist() == out_clr


@pytest.mark.parametrize(
    "cmap_cls, in_bin_path_str, out_clr_str",
    [
        ("color_byte_class", "bin_file_range32", "out_range32_byte_class"),
        ("color_byte_value", "bin_file_range32", "out_range32_byte_value"),
        ("color_byte_class", "bin_file_range64", "out_range64_byte_class"),
        ("color_byte_value", "bin_file_range64", "out_range64_byte_value"),
        ("color_byte_class", "bin_file_range256", "out_range256_byte_class"),
        ("color_byte_value", "bin_file_range256", "out_range256_byte_value"),
        ("color_byte_class", "bin_file_ascii8", "out_ascii8_byte_class"),
        ("color_byte_value", "bin_file_ascii8", "out_ascii8_byte_value"),
    ],
)
def test_colormap_iter_np_out(request, cmap_cls, in_bin_path_str, out_clr_str):
    """
    Test iterable colormap outputs.
    """
    _cmap_clss = {
        "color_byte_class": IterableColorByteClass,
        "color_byte_value": IterableColorByteValue,
    }

    in_bin_path = request.getfixturevalue(in_bin_path_str)
    out_clr = request.getfixturevalue(out_clr_str)

    _cmap_cls = _cmap_clss[cmap_cls]

    cmap = _cmap_cls(in_bin_path)
    clrs = [item for item in cmap]
    # Transform to match fixture 
    clrs = np.concatenate(clrs).reshape(-1, 1).tolist()

    assert clrs == out_clr


# class TestColorMapIter:
#     """
#     Set of tests for the colormap classes found in `binvis.colormap_iter`
#     """

#     def test_color_tarfile_structure_len(bin_path):
#         tar_path = tmp_path / "sample.tar"
#         file_path = tmp_path / "a.txt"
#         file_path.write_text("hello")

#         with tarfile.open(tar_path, "w") as tf:
#             tf.add(file_path, arcname="a.txt")

#         data = tar_path.read_bytes()
#         cmap = ColorTarFileStructure(data)

#         assert len(cmap) == len(data)
#         colors = cmap.get_point_np(slice(0, 10), mode="L")
#         assert colors.shape[0] == 10
