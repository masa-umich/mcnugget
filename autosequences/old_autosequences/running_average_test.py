import time
import random
import statistics
from collections import deque 

running_average = []
# running_average = deque()
RUNNING_AVERAGE_SIZE = 20
TEST_SIZE = 60000

test_data = []
N = 100

for j in range(0, N):
    start_1 = time.time()

    for i in range(0, TEST_SIZE):
        running_average.append(random.uniform(-1000000,1000000))
        if len(running_average) > RUNNING_AVERAGE_SIZE:
            running_average.pop(0)
        statistics.mean(running_average)

    # total = 0
    # for i in range(0, TEST_SIZE):
    #     a = random.uniform(-100, 100)
    #     running_average.append(a)
    #     total += a
    #     if len(running_average) > RUNNING_AVERAGE_SIZE:
    #         total -= running_average[0]
    #         running_average.popleft()
    #     total / len(running_average)

    test_data.append(time.time() - start_1)

    print(f"time to run {TEST_SIZE} times: ")
    print(time.time() - start_1)

print(f"average across {N} tests")
print(statistics.mean(test_data))
