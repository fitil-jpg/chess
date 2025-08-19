from utils.module_usage import aggregate_module_usage


def test_aggregate_module_usage_basic():
    runs = [
        {"modules_w": ["A", "B"], "modules_b": ["C"]},
        {"modules_w": ["A"], "modules_b": ["B", "C", "C"]},
    ]
    assert aggregate_module_usage(runs) == {"A": 2, "B": 2, "C": 3}


if __name__ == "__main__":
    test_aggregate_module_usage_basic()
