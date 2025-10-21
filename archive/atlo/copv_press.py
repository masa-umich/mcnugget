import synnax as sy

import numpy as np
import matplotlib.pyplot as plt

from mcnugget.query import read_during_state, ECStates
from mcnugget.tests import TPC
from mcnugget.time import elapsed_seconds


def analyze_copv_press(
    tr: sy.TimeRange,
    copv_press: str = "ec.pressure[12]",
    ambient_tc: str = "ec.tc[0]",
    tcs: list[str] = ["ec.tc[1]", "ec.tc[2]", "ec.tc[3]"],
    time="Time",
    state=ECStates.MANUAL,
):
    """Perform basic high level analysis of a COPV pressurization. Calculates"""
    data = read_during_state(
        tr,
        copv_press,
        time,
        ambient_tc,
        *tcs,
        state=state,
    )
    time = elapsed_seconds(data[time].to_numpy())

    # Get the average of our body TCs and subtract the ambient TC
    ambient_tc_d = data[ambient_tc].to_numpy()
    tc_avg = np.sum([data[tc].to_numpy() for tc in tcs], axis=0) / len(tcs)
    ambientized_body_tc_ds = tc_avg - ambient_tc_d

    copv_press = data[copv_press].to_numpy()
    # Smooth out the pressure data
    copv_press = np.convolve(copv_press, np.ones(100) / 100, mode="same")

    # Find the max and min pressure
    max_press = np.max(copv_press)
    min_press = np.min(copv_press)

    # When we press COPV, we do it in cycles, where we press it, wait for it to
    # settle, and then press it again. We want to separate and identify each
    # cycle. We can do this by looking for the time when the pressure derivative
    # is positive and negtive.
    # find the local minima and maxima of the pressure derivative
    copv_press_deriv = np.gradient(copv_press)
    press_threshold = np.where(copv_press_deriv > 0.15)[0]
    leak_threshold = np.where(copv_press_deriv < 0.05)[0]
    cycle_starts = []
    for i, start in enumerate(press_threshold):
        if i == 0:
            cycle_starts.append(start)
        diff = start - press_threshold[i - 1]
        prevDiff = copv_press_deriv[start] - copv_press_deriv[start - 1]
        if diff > 5 and prevDiff > 0:
            cycle_starts.append(start)
    cycle_ends = []
    for i, end in enumerate(leak_threshold):
        if i == 0:
            cycle_ends.append(end)
        diff = end - leak_threshold[i - 1]
        prevDiff = copv_press_deriv[end] - copv_press_deriv[end - 1]
        if diff > 5 and prevDiff < 0:
            cycle_ends.append(end)

    press_threshold = list(zip(cycle_starts, cycle_ends))
    leak_periods = list(zip(cycle_ends[:-1], cycle_starts[1:]))

    amount_pressed = np.zeros(len(press_threshold))
    press_times = np.zeros(len(press_threshold))
    for i, v in enumerate(press_threshold):
        start, end = v
        # shade the area between the start and end of each cycle
        plt.axvspan(time[start], time[end], alpha=0.2, color="red")
        amount_pressed[i] = copv_press[end] - copv_press[start]
        press_times[i] = time[end] - time[start]

    amount_leaked = np.zeros(len(leak_periods))
    leak_times = np.zeros(len(leak_periods))
    for i, v in enumerate(leak_periods):
        start, end = v
        # shade the area between the start and end of each cycle
        plt.axvspan(time[start], time[end], alpha=0.2, color="green")
        amount_leaked[i] = copv_press[end] - copv_press[start]
        leak_times[i] = time[end] - time[start]

    leak_rates = amount_leaked / leak_times
    press_rates = amount_pressed / press_times

    plt.plot(time, copv_press, label="COPV Pressure")
    plt.xlim(time[press_threshold[0][0]] - 1, time[press_threshold[-1][1]] + 1)
    plt.xlabel("Time (s)")
    plt.ylabel("Pressure (psi)")

    plt.twinx()
    plt.plot(time, ambientized_body_tc_ds, label="Body Temperature", color="orange")
    plt.ylabel("Temperature Delta (C)")

    plt.legend(loc="upper left")

    plt.table(
        cellText=[
            [f"Max Press: {max_press:.2f} psi", f"Min Press: {min_press:.2f} psi"],
            [
                f"Mean Press: {np.mean(amount_pressed):.2f} psi",
                f"Mean Leak: {np.mean(amount_leaked):.2f} psi",
            ],
            [
                f"Mean Press Rate: {np.mean(press_rates):.2f} psi/s",
                f"Mean Leak Rate: {np.mean(leak_rates):.2f} psi/s",
            ],
            [
                f"Max Press Rate: {np.max(press_rates):.2f} psi/s",
                f"Max Leak Rate: {np.max(leak_rates):.2f} psi/s",
            ],
            [
                f"Peak Temperature: {np.max(tc_avg):.2f} K",
                f"Temperature Delta: {np.max(ambientized_body_tc_ds) - np.min(ambientized_body_tc_ds):.2f} C",
            ],
            [
                f"Temperature Climb Rate: {np.max(np.gradient(ambientized_body_tc_ds)):.2f} C/s",
                "",
            ],
        ],
        fontsize=15,
    )

    plt.subplots_adjust(left=0.1, bottom=0.2)
    plt.tight_layout()

    plt.show()


if __name__ == "__main__":
    analyze_copv_press(TPC["02-25-23-01"])
