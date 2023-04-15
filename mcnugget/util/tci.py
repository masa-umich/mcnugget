import numpy as np 
from scipy.stats import st


def t_interval(
    data: np.array, 
    sig_level: float,
):  

    if len(data) < 2:
        return str("Input data must contain at least two values.")
    if sig_level <= 0 or sig_level >= 1:
        return str("Significance level must be between 0 and 1.")

    df = len(data) - 1
    mean = np.mean(data)

    sig_level = 
    #take sig level as an input argument 
    
    # # input sample data 
    # data = np.array([float(x) for x in input("Enter data separated by spaces: ").split()])
    # #degrees of freedom
    # #input confidence interval value in decimal form (i.e. 95% -> 0.95) 
    c_interval = st.t.interval(sig_level, df, np.mean(data), st.sem(data))
    # #maybe print something prettier for it like 
    # #"With 95% confidence the [what the thing is for] is between (c_interval)"

    return np.array(c_interval)