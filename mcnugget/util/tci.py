import numpy as np 
from scipy.stats import st

#what is this for 
purpose = input("What is the purpose for the confidence interval: ")

# input sample data 
data = np.array([float(x) for x in input("Enter data separated by spaces: ").split()])

#degrees of freedom 
df = len(data) - 1

#input confidence interval value in decimal form (i.e. 95% -> 0.95) 
sig_level = float(input("Enter significance level (e.g. 0.95): "))

c_interval = st.t.interval(sig_level, df, np.mean(data), st.sem(data))

#maybe print something prettier for it like 
#"With 95% confidence the [what the thing is for] is between (c_interval)"

np.array(c_interval)