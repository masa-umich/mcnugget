import pandas as pd
import sys
import matplotlib.pyplot as plt
import synnax as sy

doa_instrumentation = {
    1:"Ox Press Iso Pilot",
    2:"Fuel Press Iso Pilot",
    3:"Ox Dome Iso",
    4:"Air Drive Iso 2",
    5:"Air Drive Iso 1",
    6:"Ox MPV Pilot",
    7:"Fuel Feedline Purge",
    8:"Ox Feedline Purge",
    9:"Fuel Pre-Press",
    10:"Ox Pre-Press",
    11:"Ox Fill Purge",
    12:"",
    13:"",
    14:"Ox Drain Pilot",
    15:"Fuel Vent Pilot",
    16:"Ox Low-Flow Vent Pilot",
    17:"Ox High-Flow Vent Pilot",
    18:"Press Vent Pilot",
    19:"Ox Fill Valve Pilot",
    20:"Gas Booster Fill Pilot",
    21:"Ox Prevalve Pilot",
    22:"Fuel Prevalve Pilot",
    23:"Press Fill Pilot",
    24:"Fuel MPV Pilot",
    25:"Igniter",
}

ai_instrumentation = {
    1:"Ox Pre-Fill PT",
    2:"Ox Dome PT",
    3:"Fuel Tank PT 1",
    4:"Fuel Tank PT 2",
    5:"Ox Post Reg PT",
    6:"Ox Tank PT 1",
    7:"Ox Tank PT 2",
    8:"Ox Tank PT 3",
    9:"Ox Flowmeter Inlet PT",
    10:"Ox Flowmeter Throat PT",
    11:"Ox Level Sensor",
    12:"Fuel Flowmeter Inlet PT",
    13:"Fuel Flowmeter Throat PT",
    14:"Fuel Level Sensor",
    15:"Trickle Purge Post Reg PT",
    16:"Trickle Purge 2k Bottle PT",
    17:"Regen Manifold PT",
    18:"Fuel Manifold PT",
    19:"Chamber PT 1",
    20:"Air Drive 2k PT",
    21:"Air Drive Post Reg PT",
    22:"Press Tank PT 3",
    23:"Press 2k PT",
    24:"Press Tank PT 2",
    25:"Gas Booster Outlet PT",
    26:"Press Tank PT 1",
    27:"Press 2k Pre Fill PT",
    28:"Chamber PT 2",
    29:"Chamber PT 3",
    30:"Pneumatics Bottle PT",
    31:"Trailer Pneumatics PT",
    32:"",
    33:"Engine Pneumatics PT",
    34:"Purge 2k Bottle PT",
    35:"Fuel Tank PT 3",
    36:"Purge Post Reg PT",
}

def run_data_analyzer():
    csv_file_path = input("Enter the path to the CSV file you would like to analyze: ")
    if "doa" in csv_file_path:
        mode = "doa"
    else:
        mode = "ai"
    df = parse_df(csv_file_path)
    channels = []
    for x in df.iloc[:, 0]:
        channels.append(str(x))
    # if mode == "doa":
    #     timestamp_channel = channels.index("gse_doa_time")
    # else:
    #     timestamp_channel = channels.index("gse_ai_time")
    timestamps =  df.iloc[-1, 1:].astype(float)
    translated_timestamps = [pd.Timestamp(ts, unit='ns') for ts in timestamps]  # if ts > 1715754150000000000
    while True:
        chan = input("Enter channel you would like to see (or exit to finish analysis): ")
        if chan == "exit":
            break
        else:
            try:
                chan_index = channels.index(chan)
                if mode == "doa":
                    title = doa_instrumentation[int(chan[8:])]
                else:
                    title = ai_instrumentation[int(chan[7:])]
            except ValueError:
                print(f"Channel {chan} not found.")
                continue
            graph_row_with_timestamps(title, df, chan_index, translated_timestamps)

def graph_row_with_timestamps(title, df, row_number, timestamps):
    data_row = df.iloc[row_number, (len(df.columns) - len(timestamps)):].astype(float) 
    plt.figure(figsize=(13, 8))
    plt.title(title)
    plt.plot(timestamps, data_row)
    plt.grid(True)
    plt.show()

def parse_df(csv_file_path):
    df = pd.read_csv(csv_file_path) 
    print(f"Successfully read CSV file: {csv_file_path}")
    return df

if __name__ == "__main__":
    if (len(sys.argv) != 1):
        print("Usage: python script.py")
    else:
        run_data_analyzer()
