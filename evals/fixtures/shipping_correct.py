import math


def shipping_cost(weight_kg: float, express: bool = False) -> int:
    if not (0 < weight_kg <= 30):
        raise ValueError("weight must be more than 0 and at most 30 kg")
    cost = 500 + 200 * max(0, math.ceil(weight_kg - 1))
    if express:
        return cost * 2
    return 0 if weight_kg >= 10 else cost
