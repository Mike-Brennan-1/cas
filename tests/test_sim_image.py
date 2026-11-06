import pytest

from cas.sim_image import _is_image


def test_accepts_a_real_image(png_bytes):
    assert _is_image(png_bytes)


@pytest.mark.parametrize("data", [b"", b"not an image", b"<svg></svg>"])
def test_rejects_data_that_is_not_an_image(data):
    assert not _is_image(data)
