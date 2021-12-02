import er_web.safe_eval as safe_eval

import numpy as np


def test_to_tuple():
    identity_items = [
        (1, 2, 3),
        ((1, 2), (3, 4)),
    ]
    for item in identity_items:
        assert item == safe_eval._to_tuple(item)

    np_items = [
        (np.array([1, 2, 3]), (1, 2, 3)),
        (np.array([[1, 2], [3, 4]]), ((1, 2), (3, 4))),
    ]
    for np_item, tup in np_items:
        assert tup == safe_eval._to_tuple(np_item)
