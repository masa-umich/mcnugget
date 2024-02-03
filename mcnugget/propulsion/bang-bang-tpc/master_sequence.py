import synnax as sy
import time

client = sy.Synnax(
    host="localhost",
    port=9090,
    username="synnax",
    password="seldon",
    secure=False
)

INC_DELAY = 1

class autosequence_valve:
    # defines a valve with the following properties:
    
    # chan: the human-readable name for the channel
    # cmd: the name of the command channel valve writes to
    # ack: the name of the acknowledgement channel valve reads from
    # press: the channel to read pressure from
    # target: the pressure (int) that the valve will pressurize to
    # max: the pressure (int) that the valve automatically shuts off at
    # inc: the increments for which valve increases 
    # inc_wait: the delay between pressure incrementation (in seconds)

    # this function is called when a new valve is initiated
    def __init__(self, chan: str, cmd: str, ack: str, press: str, final_target: int, max: int, inc: int, inc_delay=INC_DELAY):
        self.chan = chan
        self.cmd = cmd
        self.ack = ack
        self.press = press
        self.target = final_target
        self.max = max
        self.inc = inc
        self.inc_delay = inc_delay
    
    # this function runs until the pressure is at the target pressure
    def run(self):
        # this gives the function access to the channels
        with client.control.acquire(
            "bang_bang_tpc",
            write=[
                self.cmd
            ],
            read=self.ack,
            write_authorities=[255]
        ) as auto:
            # this increments the pressure until it reaches the target
            print(f"Opening {self.chan}")
            partial_target = self.inc
            while True:
                print(f"pressurizing to {partial_target}")

                # opens valve
                auto[self.cmd] = 1

                # waits until the valve reaches the target pressure
                auto.wait_until(lambda c: self.run_valve(c, partial_target))
                
                # closes valve
                auto[self.cmd] = 0

                # checks if the valve is fully pressurized, otherwise increments the target
                if auto[self.press] >= self.target:
                    print(f"final target reached for valve {self.chan}")
                    break
                partial_target += self.inc

                # slight delay for safety reasons
                time.sleep(self.inc_delay)

    # this function checks the pressure against target pressure and max pressure
    # it returns true iff the pressure has reached the target
    def run_valve(self, auto, target: int):
        pressure = auto[self.press]
        open = auto[self.ack]

        # shuts off if the pressure is above the max
        if pressure > self.max:
            if not open:
                print(f"closing valve {self.chan}")
            auto[self.cmd] = False  # this executes either way for safety

        # returns True if the target pressure is reached
        elif pressure >= self.target:
            if open:
                print(f"reached target for valve {self.chan}")
                return True
        
        # if the pressure has not reached the target, opens the valve
        elif pressure < self.target:
            if not open:
                print(f"opening valve {self.chan}")
                auto[self.cmd] = True

    # closes the valve
    def shut_down(self, auto):
        print(f"finished - closing {self.cmd}")
        auto[self.cmd] = False


# closes all the valves in the list
def shut_down(self, valves):
    for valve in valves:
        valve.shut_down()