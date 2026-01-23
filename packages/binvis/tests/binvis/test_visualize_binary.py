import os
import pytest

from PIL import Image, ImageChops

from binvis.binvis import visualize_binary
from binvis.binvis_iter import visualize_binary_iter


def _img_assert_equals(img1: Image, img2: Image):
    """
    Check whether two images are the same.
    """
    diff = ImageChops.difference(img1, img2)

    assert diff.getbbox() is None


@pytest.mark.parametrize(
    ("data", "color_map", "size", "out_img_path"),
    [
        ("bin_range32", "class", 8, "range32__s8_sq_class.png"),
        ("bin_range32", "magnitude", 8, "range32__s8_sq_magnitude.png"),
        ("bin_range64", "class", 8, "range64__s8_sq_class.png"),
        ("bin_range64", "magnitude", 8, "range64__s8_sq_magnitude.png"),
        ("bin_range256", "class", 8, "range256__s8_sq_class.png"),
        ("bin_range256", "magnitude", 8, "range256__s8_sq_magnitude.png"),
        ("bin_range256", "class", 16, "range256__s16_sq_class.png"),
        ("bin_range256", "magnitude", 16, "range256__s16_sq_magnitude.png"),
        ("bin_range256", "class", 32, "range256__s32_sq_class.png"),
        ("bin_range256", "magnitude", 32, "range256__s32_sq_magnitude.png"),
    ],
)
def test_visualize_binary__square(
    request, golden_base_dir, data, color_map, size, out_img_path
):
    """
    Test iterable colormap outputs.
    """
    GOLD_DIR = golden_base_dir
    BASE_DIR = "outputs/layout_type_square"
    LAYOUT_TYPE = "square"

    path_gold = os.path.join(GOLD_DIR, BASE_DIR, out_img_path)

    img_gold = Image.open(path_gold)

    data = request.getfixturevalue(data)

    img = visualize_binary(
        byte_array=data,
        size=size,
        color_map=color_map,
        layout_map="hilbert",
        layout_type=LAYOUT_TYPE,
        show_progress=False,
    )

    assert img.size == img_gold.size
    assert img.mode == "RGB"

    _img_assert_equals(img_gold, img)


@pytest.mark.parametrize(
    ("data", "color_map", "size", "out_img_path"),
    [
        ("bin_range32", "class", 4, "range32__s4_un_class.png"),
        ("bin_range32", "magnitude", 4, "range32__s4_un_magnitude.png"),
        ("bin_range64", "class", 4, "range64__s4_un_class.png"),
        ("bin_range64", "magnitude", 4, "range64__s4_un_magnitude.png"),
    ],
)
def test_visualize_binary__unrolled(
    request, golden_base_dir, data, color_map, size, out_img_path
):
    """
    Test iterable colormap outputs.
    """
    GOLD_DIR = golden_base_dir
    BASE_DIR = "outputs/layout_type_unrolled"
    LAYOUT_TYPE = "unrolled"

    path_gold = os.path.join(GOLD_DIR, BASE_DIR, out_img_path)

    img_gold = Image.open(path_gold)

    data = request.getfixturevalue(data)

    img = visualize_binary(
        byte_array=data,
        size=size,
        color_map=color_map,
        layout_map="hilbert",
        layout_type=LAYOUT_TYPE,
        show_progress=False,
    )

    assert img.size == img_gold.size
    assert img.mode == "RGB"

    _img_assert_equals(img_gold, img)


# NOTE: There is an indexing error for the `visualize_binary_iter` function
# when the chunk size is large compared to the size
@pytest.mark.parametrize(
    ("label", "data", "size", "color_map", "layout_type"),
    [
        ("range32_s4_sq_class", "bin_range32", 4, "class", "square"),
        ("range32_s8_sq_class", "bin_range32", 8, "class", "square"),
        ("range32_s16_sq_class", "bin_range32", 16, "class", "square"),
        ("range64_s4_sq_class", "bin_range64", 4, "class", "square"),
        ("range64_s8_sq_class", "bin_range64", 8, "class", "square"),
        ("range64_s16_sq_class", "bin_range64", 16, "class", "square"),
        ("range256_s4_sq_class", "bin_range256", 4, "class", "square"),
        ("range256_s8_sq_class", "bin_range256", 8, "class", "square"),
        ("range256_s16_sq_class", "bin_range256", 16, "class", "square"),
        ("range32_s4_sq_magnitude", "bin_range32", 4, "magnitude", "square"),
        ("range32_s8_sq_magnitude", "bin_range32", 8, "magnitude", "square"),
        ("range32_s16_sq_magnitude", "bin_range32", 16, "magnitude", "square"),
        ("range64_s4_sq_magnitude", "bin_range64", 4, "magnitude", "square"),
        ("range64_s8_sq_magnitude", "bin_range64", 8, "magnitude", "square"),
        ("range64_s16_sq_magnitude", "bin_range64", 16, "magnitude", "square"),
        ("range256_s4_sq_magnitude", "bin_range256", 4, "magnitude", "square"),
        ("range256_s8_sq_magnitude", "bin_range256", 8, "magnitude", "square"),
        ("range256_s16_sq_magnitude", "bin_range256", 16, "magnitude", "square"),
        ("range32_s4_un_class", "bin_range32", 4, "class", "unrolled"),
        ("range32_s8_un_class", "bin_range32", 8, "class", "unrolled"),
        ("range32_s16_un_class", "bin_range32", 16, "class", "unrolled"),
        ("range64_s4_un_class", "bin_range64", 4, "class", "unrolled"),
        ("range64_s8_un_class", "bin_range64", 8, "class", "unrolled"),
        ("range64_s16_un_class", "bin_range64", 16, "class", "unrolled"),
        ("range256_s4_un_class", "bin_range256", 4, "class", "unrolled"),
        ("range256_s8_un_class", "bin_range256", 8, "class", "unrolled"),
        ("range256_s16_un_class", "bin_range256", 16, "class", "unrolled"),
        ("range32_s4_un_magnitude", "bin_range32", 4, "magnitude", "unrolled"),
        ("range32_s8_un_magnitude", "bin_range32", 8, "magnitude", "unrolled"),
        ("range32_s16_un_magnitude", "bin_range32", 16, "magnitude", "unrolled"),
        ("range64_s4_un_magnitude", "bin_range64", 4, "magnitude", "unrolled"),
        ("range64_s8_un_magnitude", "bin_range64", 8, "magnitude", "unrolled"),
        ("range64_s16_un_magnitude", "bin_range64", 16, "magnitude", "unrolled"),
        ("range256_s4_un_magnitude", "bin_range256", 4, "magnitude", "unrolled"),
        ("range256_s8_un_magnitude", "bin_range256", 8, "magnitude", "unrolled"),
        ("range256_s16_un_magnitude", "bin_range256", 16, "magnitude", "unrolled"),
        ("ascii_s4_sq_class", "bin_ascii8", 4, "class", "square"),
        ("ascii_s8_sq_class", "bin_ascii8", 8, "class", "square"),
        ("ascii_s16_sq_class", "bin_ascii8", 16, "class", "square"),
        ("ascii_s4_sq_magnitude", "bin_ascii8", 4, "magnitude", "square"),
        ("ascii_s8_sq_magnitude", "bin_ascii8", 8, "magnitude", "square"),
        ("ascii_s16_sq_magnitude", "bin_ascii8", 16, "magnitude", "square"),
        ("ascii_s4_un_class", "bin_ascii8", 4, "class", "unrolled"),
        ("ascii_s8_un_class", "bin_ascii8", 8, "class", "unrolled"),
        ("ascii_s16_un_class", "bin_ascii8", 16, "class", "unrolled"),
        ("ascii_s4_un_magnitude", "bin_ascii8", 4, "magnitude", "unrolled"),
        ("ascii_s8_un_magnitude", "bin_ascii8", 8, "magnitude", "unrolled"),
        ("ascii_s16_un_magnitude", "bin_ascii8", 16, "magnitude", "unrolled"),
        ("range256_s4_unn_magnitude", "bin_range256", 4, "magnitude", "unrolled_n"),
        ("range256_s8_unn_magnitude", "bin_range256", 8, "magnitude", "unrolled_n"),
        ("range256_s16_unn_magnitude", "bin_range256", 16, "magnitude", "unrolled_n"),
    ],
)
def test_visualize_binary_matches_iter(
    tmp_path, request, label, data, size, color_map, layout_type
):
    data = request.getfixturevalue(data)

    input_path = tmp_path / f"{label}.bin"
    input_path.write_bytes(data)

    img = visualize_binary(
        byte_array=data,
        size=size,
        color_map=[color_map] * 3,
        layout_map="hilbert",
        layout_type=layout_type,
        show_progress=False,
    )

    img_iter = visualize_binary_iter(
        path=str(input_path),
        size=size,
        color_map=[color_map] * 3,
        layout_map="hilbert",
        layout_type=layout_type,
        show_progress=False,
        chunk_size=16,
    )

    assert img.size == img_iter.size
    assert img.mode == img_iter.mode
    assert img.tobytes() == img_iter.tobytes()


@pytest.mark.parametrize(
    ("in_file_path", "out_img_path", "size", "layout_type"),
    [
        ("sample_txt.tar", "sample_txt_s256_sq.png", 256, "square"),
        ("sample_img1.tar", "sample_img1_s256_sq.png", 256, "square"),
        ("sample_img2.tar", "sample_img2_s256_sq.png", 256, "square"),
        ("sample_txt.tar", "sample_txt_s256_un.png", 256, "unrolled"),
        ("sample_img1.tar", "sample_img1_s256_un.png", 256, "unrolled"),
        ("sample_img2.tar", "sample_img2_s256_un.png", 256, "unrolled"),
        ("sample_txt.tar", "sample_txt_s256_unn.png", 256, "unrolled_n"),
        ("sample_img1.tar", "sample_img1_s256_unn.png", 256, "unrolled_n"),
        ("sample_img2.tar", "sample_img2_s256_unn.png", 256, "unrolled_n"),
    ],
)
def test_visualize_binary_iter__golden(
    golden_base_dir, in_file_path, out_img_path, size, layout_type
):
    """
    Test iterable colormap outputs.
    """
    COLOR_MAP = ["class", "magnitude", "structure"]
    GOLD_DIR = golden_base_dir
    IN_BASE_DIR = "inputs/golden"
    OUT_BASE_DIR = "outputs/golden"

    in_path_gold = os.path.join(GOLD_DIR, IN_BASE_DIR, in_file_path)
    out_path_gold = os.path.join(GOLD_DIR, OUT_BASE_DIR, out_img_path)

    img_gold = Image.open(out_path_gold)

    img = visualize_binary_iter(
        path=in_path_gold,
        size=size,
        color_map=COLOR_MAP,
        layout_map="hilbert",
        layout_type=layout_type,
        show_progress=False,
        chunk_size=20*512,
    )

    assert img.size == img_gold.size
    assert img.mode == img_gold.mode

    _img_assert_equals(img_gold, img)
