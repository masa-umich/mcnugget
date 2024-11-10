import syauto
import threading


'''
This is a demo of how to use the auto_utilities functions.
This autosequence:
1. Pressurizes VALVE1 to 500 psi in increments of 50
2. Pressurizes VALVE2 to 300 all at once
3. Depressurizes VALVE1 to 400 in increments of 25
4. Opens all valves to depressurize the system

It also monitors the pressures to ensure that 
    VALVE1 and VALVE2 stay below their specified MAWPs (max)

'''

V1 = {
    "cmd": "valve_1_cmd",
    "ack": "valve_1_ack",
    "press": "valve_1_press",
    "max": 800
}

V2 = {
    "cmd": "valve_2_cmd",
    "ack": "valve_2_ack",
    "press": "valve_2_press",
    "max": 500
}


with auto_utilities.initialize_for_autosequence as auto:
    auto_utilities.run_safety([V1["max"], V2["max"]], [V1["press"], V2["press"]], auto)
    auto_utilities.press_valve("valve 1", V1["cmd"], V1["press"], 500, 50, auto)
    auto_utilities.press_valve("valve 2", V2["cmd"], V2["press"], 300, 300, auto)
    auto_utilities.depress_valve("valve 1", V1["cmd"], V1["press"], 400, 25, auto)
    

'''
This is another demo of how to use the auto_utilities functions.
This autosequence:
1. Pressurizes VALVE1 to 500 psi in increments of 50
2. Pressurizes VALVE2 to 500 psi in increments of 100
3. Pressurizes VALVE3 to 800 in increments of 100
4. Waits until 1-3 are completed
5. Depressurizes VALVE1 to 200 psi in increments of 50
6. Pressurizes VALVE2 to 800 psi in increments of 50
7. Waits until 5-6 are completed
8. Depressurizing everything

It also monitors the pressures to ensure that all valves remain under safe pressures

'''

V1 = {
    "cmd": "valve_1_cmd",
    "ack": "valve_1_ack",
    "press": "valve_1_press",
    "max": 800
}

V2 = {
    "cmd": "valve_2_cmd",
    "ack": "valve_2_ack",
    "press": "valve_2_press",
    "max": 800
}

V3 = {
    "cmd": "valve_3_cmd",
    "ack": "valve_3_ack",
    "press": "valve_3_press",
    "max": 1200
}


with auto_utilities.initialize_for_autosequence as auto:
    thread1 = threading.Thread(auto_utilities.press_valve("valve 1", V1["cmd"], V1["press"], 500, 50),
                               auto_utilities.press_valve("valve 2", V2["cmd"], V2["press"], 500, 100),
                               auto_utilities.press_valve("valve 3", V3["cmd"], V3["press"], 800, 100))
    thread2 = threading.Thread(auto_utilities.depress_valve("valve 1", V1["cmd"], V1["press"], 200, 50),
                               auto_utilities.press_valve("valve 2", V2["cmd"], V2["press"], 800, 50))
    thread3 = threading.Thread(auto_utilities.depress_valve("valve 1", V1["cmd"], V1["press"], 5, 200),
                               auto_utilities.depress_valve("valve 2", V2["cmd"], V2["press"], 5, 500),
                               auto_utilities.depress_valve("valve 3", V3["cmd"], V3["press"], 5, 800))
    input("Pressurizing V1, V2, and V3 - press Enter to confirm")
    thread1.start()
    thread1.join()
    input("Depressurizing V1 and pressurizing V2 - press Enter to confirm")
    thread2.start()
    thread2.join()
    input("Depressurizing all - press Enter to confirm")
    thread3.start()
    thread3.join()
    print("Finished autosequence")
