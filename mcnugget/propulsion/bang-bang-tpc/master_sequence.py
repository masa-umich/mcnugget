import synnax as sy
import time

client = sy.Synnax(
    host="localhost",
    port=9090,
    username="synnax",
    password="seldon",
    secure=False
)

class autosequencevalve:
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
    def __init__(self, chan: str, cmd: str, ack: str, press: str, target: int, max: int, inc: int, inc_wait: float):
        self.chan = chan
        self.cmd = cmd
        self.ack = ack
        self.press = press
        self.target = target
        self.max = max
        self.inc = inc
    
    # this function runs until the pressure is at the target pressure
    def run(self):
        with client.control.acquire(
            "bang_bang_tpc",
            write=[
                self.cmd
            ],
            read=self.ack,
            write_authorities=[255]
        ) as auto:
            while True:
                print(f"Opening {self.chan}")
                auto[self.cmd] = 1
                auto.wait_until(lambda c: self.run_valve(self, auto))
                auto[self.cmd] = 0
                if auto[self.press] >= self.target:
                    print(f"final target reached for valve {self.chan}")
                    break
                time.sleep()

    def run_valve(self, auto):
        pressure = auto[self.press]
        open = auto[self.ack]

        if pressure > self.max:
            print(f"closing valve {self.chan}")
            auto[self.cmd] = False

        elif pressure > self.target:
            print(f"reached target for valve {self.chan}")


        return pressure < 15