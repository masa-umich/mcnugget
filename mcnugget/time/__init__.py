import numpy as np
import synnax as sy

def elapsed_seconds(time: np.ndarray) -> np.ndarray:
    time -= time[0]
    time = time.astype(np.float64)
    return time / sy.TimeSpan.SECOND