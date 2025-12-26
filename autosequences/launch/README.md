# Launch Autosequene
Authors: Jack Hammerberg (jackmh)

Documentation Last Updated: 12-26-2025

## Usage:
1. Ensure channel mappings & variables are correct in `config.yaml`
2. Launch script:
```sh
./launch.py
```
or
```sh
uv run launch.py
```
3. Follow the in-terminal prompts

## CLI Options
```sh
-c | --cluster <host>
```

```sh
-m | --config <config.yaml>
```

```sh
-v | --verbose
```

## Testing:
1. Start your local Synnax cluster
```sh
synnax start --listen localhost:9090 -vmi
```
2. Start the simulation
```sh
cd mcnugget/simulation
./simulation --cluster <localhost or WSL IP>
```
3. Start the launch Autosequence
```sh
cd mcnugget/autosequences/launch
./launch --cluster <localhost or WSL IP>
```

## TODO (for developers in no particular order):
- Add pretty colors to print statements
- Rest of press fill sequence
- Automatic phase transitions & only allow for certain phase transitions