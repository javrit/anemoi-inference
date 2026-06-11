from anemoi.transform.filters import create_filter
from anemoi.transform.testing import TestingContext


def test_plugin():
    filter = create_filter(TestingContext(), "anemoi-transforms")
    assert filter is not None


if __name__ == "__main__":
    test_plugin()
