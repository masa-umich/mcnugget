# Launch Autosequene
Authors: Jack Hammerberg (jackmh)

Documentation Last Updated: 12-23-2025

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

## TODO (for developers in no particular order):
- Add pretty colors to print statements
- Rest of press fill sequence
- Abort cases with SRE prompt for venting
- Automatic phase transitions & only allow for certain phase transitions