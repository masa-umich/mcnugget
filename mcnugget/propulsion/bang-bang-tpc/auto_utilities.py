import synnax as sy

# this function pressurizes a valve to a pressure in specified increments
def press_valve(vlv: str, cmd: str, press: str, target: float, inc: float, auto):
    partial_target = inc
    input(f"pressurizing {vlv} to {target} - press Enter to continue")
    while True:
        print(f"pressurizing {vlv} to {partial_target}")
        auto[cmd] = True
        auto.wait_until(lambda auto: auto[press] >= partial_target)
        if partial_target >= target:
            print("final pressure reached for {vlv}")
            break
        partial_target += inc

# # this function depresses a valve to a pressure in specified increments
# def depress_valve(vlv: str, cmd: str, press: str, target: float, auto):
#     partial_target = auto[press] - inc
#     input(f"depressurizing {vlv} to {target} - press Enter to continue")
#     while True:
#         print(f"depressurizing {vlv} to {partial_target}")
#         auto[cmd] = False
#         auto.wait_until(lambda auto: auto[press] <= partial_target)
#         if partial_target <= target:
#             print("final pressure reached for {vlv}")
#             break
#         partial_target -= inc

# this function checks pressures and returns FALSE if an abort is needed
def run_safety(max_list: [float], press_list: [str], auto):
    for max, press in max_list, press_list:
        if auto[press] >= max:
            print("valve {vlv.vlv} above MAWP - aborting")
            return False
        # if auto[press] <= vlv.min:
        #     print("valve {vlv.vlv} fell below minimum pressure - aborting")
        #     return False
        #     break
    return True

# this function initializes `auto` for the channels specified
def initialize_for_autosequence(cmds: [str], acks: [str], pressures: [str]):
    client = sy.Synnax(
        host="localhost",
        port=9090,
        username="synnax",
        password="seldon",
        secure=False
    )
    return client.control.acquire(
        "bang_bang_tpc",
        write=[
            cmd for cmd in cmds
        ],
        read=[
            ack_or_press for ack_or_press in acks + pressures
        ],
        write_authorities=[255]
    )