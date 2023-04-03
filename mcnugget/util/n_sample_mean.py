import numpy as np

def step_mean(arr: np.array, step: int) -> np.array:
    """
    Returns the n sample average of the input as a new array.

    Parameters:
        arr: The 1-dimensional, numeric array to take the average of. 
        step: integer value representing the sample size to take the average over.

    Returns:
        If step is 0, returns the original array. Otherwise, returns the n
        sample average.
    """

    output = np.zeros(np.ceil(len(arr) / step))
    for i in range(0, len(arr), step):
        output[i] = np.mean(arr[i:i+step]) 
    return output

