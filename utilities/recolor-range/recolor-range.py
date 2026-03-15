#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "synnax==0.49",
# ]
# ///
import synnax as sy
import argparse

def parse_args() -> argparse.Namespace:
    global verbose
    parser = argparse.ArgumentParser(
        description="The autosequence for preparring Limeight for launch!"
    )
    parser.add_argument(
        "-c",
        "--cluster",
        help="Specify a Synnax cluster to connect to",
        type=str,
        default="synnax.masa.engin.umich.edu"
    )
    return parser.parse_args()

def synnax_login(cluster: str) -> sy.Synnax:
    global verbose
    try:
        client = sy.Synnax(
            host=cluster,
            port=9090,
            username="synnax",
            password="seldon",
        )
    except Exception as e:
        raise Exception(f"Could not connect to Synnax at {cluster}, are you sure you're connected?")
    return client  # type: ignore

def main():
    args = parse_args()
    cluster = args.cluster
    client = synnax_login(cluster)
    range_key_input = input("Enter the key of the range to recolor: ")
    range: sy.Range = client.ranges.retrieve(key=range_key_input)
    if range is None:
        raise Exception(f"Could not find range with key: {range_key_input}")
    print(f"Current color of range '{range.name}': {range.color}")
    new_color = input("Enter the new color for the range (in hex format, e.g. #FF0000 for red): ")
    if not new_color.startswith("#") or len(new_color) != 7:
        raise Exception("Invalid color format, must be in hex format (e.g. #FF0000 for red)")
    
    client.ranges.create(
        key=range.key,
        name=range.name,
        time_range=range.time_range,
        color=new_color,
    )

    print(f"Range '{range.name}' recolored to {new_color}")

if __name__ == "__main__":
    main()
