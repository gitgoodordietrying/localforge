"""
Shared image processing utilities used by image_tool and validator_tool.
"""


def check_seamless(image, max_diff: int = 20) -> float:
    """Check if a tile is seamless. Returns score 0.0-1.0."""
    import numpy as np

    arr = np.array(image)
    left_edge = arr[:, 0, :]
    right_edge = arr[:, -1, :]
    lr_diff = np.abs(left_edge.astype(int) - right_edge.astype(int))
    lr_match = float(np.mean(lr_diff < max_diff))

    top_edge = arr[0, :, :]
    bottom_edge = arr[-1, :, :]
    tb_diff = np.abs(top_edge.astype(int) - bottom_edge.astype(int))
    tb_match = float(np.mean(tb_diff < max_diff))

    return (lr_match + tb_match) / 2
