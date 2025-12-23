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
`-c | --cluster <host>`
`-m | --config <config.yaml>`
`-v | --verbose`

## TODO (for developers):
1. Replace FSM package with a standard switch statement inside a loop
2. Replace hard-coded channels dict with importing `mappings.yaml` 
3. Make script to create `mappings.yaml` from `icd.xlsx`
4. Implement the autosequence logic... [link to document](https://docs.google.com/document/d/1rgJRN3EEq3BMmNyXFKvW-fIrCa0_asf7RmsacfWU8j4/edit?usp=sharing)


## `Mappings.yaml` required fields:
- Press Iso 1 (NC)
- Press Iso 2  (NC)
- Press Iso 3  (NC)
- Press Fill Iso  (NC)
- Press Fill Vent (NO)
- COPV Vent (NC)

- COPV PT 1
- COPV PT 2
- Fuel Tank 1
- Fuel Tank 2
- Ox Ullage 1
- Ox Ullage 2