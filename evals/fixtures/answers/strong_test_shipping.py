import pytest
from shipping import shipping_cost


@pytest.mark.parametrize(
    ("weight", "cost"),
    [(0.1, 500), (1.0, 500), (1.2, 700), (2.0, 700), (2.1, 900), (9.9, 2300), (9.99, 2300)],
)
def test_standard_cost(weight, cost):
    assert shipping_cost(weight) == cost


@pytest.mark.parametrize("weight", [10, 10.5, 30])
def test_standard_is_free_from_10kg(weight):
    assert shipping_cost(weight) == 0


@pytest.mark.parametrize(("weight", "cost"), [(1.0, 1000), (2.1, 1800), (10, 4600), (30, 12600)])
def test_express_doubles_and_is_never_free(weight, cost):
    assert shipping_cost(weight, express=True) == cost


@pytest.mark.parametrize("weight", [0, -1, 30.01, 31])
def test_invalid_weights_rejected(weight):
    with pytest.raises(ValueError):
        shipping_cost(weight)
