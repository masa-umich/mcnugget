# Launch Autosequene
Authors: Ryan Dunlap (radunlap), Jack Hammerberg (jackmh)

Documentation Last Updated: 11-17-2025

## Usage:
1. Ensure mappings are correct in `mappings.yaml`
2. Launch script:
```sh
./launch.py
```
or
```sh
uv run launch.py
```
3. Follow the in-terminal prompts

## TODO (for developers):
1. Replace FSM package with a standard switch statement inside a loop
2. Replace hard-coded channels dict with importing `mappings.yaml` 
3. Make script to create `mappings.yaml` from `icd.xlsx`
4. Implement the autosequence logic... [link to document](https://docs.google.com/document/d/1rgJRN3EEq3BMmNyXFKvW-fIrCa0_asf7RmsacfWU8j4/edit?usp=sharing)
