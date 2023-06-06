import numpy as np


def correct_calibration(
        curr_slope: float,
        curr_offset: float,
        target_slope: float,
        target_offset: float,
        data: np.ndarray,
) -> np.ndarray:
    """Corrects the calibration of a dataset.

    Args:
        curr_slope (float): The current slope of the calibration.
        curr_offset (float): The current offset of the calibration.
        target_slope (float): The target slope of the calibration.
        target_offset (float): The target offset of the calibration.
        data (np.ndarray): The data to correct.

    Returns:
        np.ndarray: The corrected data.
    """
    return (data - curr_offset) / curr_slope * target_slope + target_offset
