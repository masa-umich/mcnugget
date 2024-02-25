import synnax as sy
import time

client = sy.Synnax(
    host="localhost",
    port=9090,
    username="synnax",
    password="seldon",
    secure=False
)

# specifies the default delay between increments
INC_DELAY = 1

# TODO - configure this to match the valve(s) in testing
def main():
    # this creates a valve that will be pressurized 
            # to somewhere between 485 and 492.5 psi in increments of 97
    valve = autosequence_valve(chan="channel name goes here", 
                               cmd="channel_cmd", 
                               ack="channel_ack",
                               press="channel_press", 
                               target_high=492.5, 
                               target_low=485,
                               max=500, 
                               inc=97,
                               )
    
    # this waits for an input
    input(f"pressurizing {valve.chan} to {valve.target_low} - press any key to confirm")
    # this runs the valve procedure
    valve.run()
    # this closes the valve
    print(f"Finished test - press any key to close {valve.chan}")
    close_all([valve])



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
    def __init__(self, chan: str, cmd: str, ack: str, press: str, target_low: float, target_high: float, max: float, inc: float, inc_delay=INC_DELAY):
        self.chan = chan
        self.cmd = cmd
        self.ack = ack
        self.press = press
        self.target_low = target_low
        self.target_high = target_high
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
                if auto[self.press] >= self.target_low:
                    print(f"final target reached for valve {self.chan}")
                    break
                partial_target += self.inc

                # slight delay for safety reasons
                time.sleep(self.inc_delay)

    # this function checks the pressure against target pressure and max pressure
    # it returns true iff the pressure has reached the target
    def run_valve(self, auto):
        pressure = auto[self.press]
        open = auto[self.ack]

        # shuts off if the pressure is above the max or if pressure is negative
        if pressure > self.max or pressure < 0:
            if open:
                print(f"unstable pressure for {self.chan} - ABORTING")
            auto[self.cmd] = False  # this executes either way for safety
            abort()

        # closes the valve if pressure is above the high end of the target
        if pressure > self.target_high:
            if open:
                print(f"closing valve {self.chan}")
                auto[self.cmd] = False

        # returns True if the target pressure is reached
        elif pressure >= self.target_low:
            if open:
                print(f"reached target for valve {self.chan}")
                return True
        
        # if the pressure has not reached the target, opens the valve
        elif pressure < self.target_low:
            if not open:
                print(f"opening valve {self.chan}")
                auto[self.cmd] = True

    # closes the valve
    def close(self, auto):
        print(f"closing {self.cmd}")
        auto[self.cmd] = False
    
    # opens the valve
    def close(self, auto):
        print(f"opening {self.cmd}")
        auto[self.cmd] = True

    ### END OF AUTOSEQUENCE_VALVE CLASS ###


    ### USEFUL FUNCTIONS FOR WORKING WITH VALVES ###

# closes all the valves in the list
def close_all(self, valves):
    for valve in valves:
        valve.close()

def open_all(self, valves):
    for valve in valves:
        valve.open()
    
# TODO - check this for every test and make sure its right
def abort(self):
    # this gives the function access to the channels
    with client.control.acquire(
        "bang_bang_tpc",
        write=[
            self.cmd_chan
        ],
        read=self.ack,
        write_authorities=[255]
    ) as auto:
        auto["valve_cmd"] = False

# this runs the main function defined at the top of the program
main()