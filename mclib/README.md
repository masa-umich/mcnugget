# mclib

A shared library for McNugget project scripts.

## Modules

### `config.py`
Provides a consolidated `Config` class for parsing `config.yaml` files, supporting both autosequence and simulation configuration requirements.

### `logger.py`
Provides centralized logging and printing utilities compatible with `prompt_toolkit`.
- `log()`: Logs messages with ISO timestamps, optional phase names, and color/bold formatting.
- `write_logs_to_file()`: Writes captured logs to a file.
- `printf()`: A printing utility to handle `prompt_toolkit` display issues.

### `math_utils.py`
Contains mathematical utilities for data analysis.
- `average_ch`: Implements Exponentially Weighted Moving Average (EWMA) for performant data smoothing.
- `sensor_vote_values()`: Provides a median-based voting mechanism for sensor redundancy.

### `phase.py` (Coming soon)
Manages phase-based logic for autosequences, including threading and signal handling.

### `autosequence.py` (Coming soon)
Manages the orchestration of phases and configuration for autosequences.

### `utils.py` (Coming soon)
Contains general helper functions such as `open_vlv`, `close_vlv`, and valve state utilities.
