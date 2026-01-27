from binvis.scurve_np import create_layout_map_from_size


def _validate_layout(layout, size):
    assert len(layout) == size * size
    for x, y in layout:
        assert 0 <= x < size
        assert 0 <= y < size


def test_create_layout_map_from_size_hilbert():
    size = 8
    layout = create_layout_map_from_size("hilbert", 2, size)
    _validate_layout(layout, size)


def test_create_layout_map_from_size_zigzag():
    size = 8
    layout = create_layout_map_from_size("zigzag", 2, size)
    _validate_layout(layout, size)
