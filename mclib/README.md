# mclib

`mclib` is a centralized, versioned Python library for the McNugget project. It houses common, duplicated functionality from various scripts in the repository—such as autosequences and simulations—so they can all share the same logic, state management, and configuration components.

## How it Works and Formatting

`mclib` is structured as a standard Python package mapped at the root of the repository. It uses `uv` for dependency and package management. Scripts in other directories (like `/autosequences` or `/simulation`) don't need to manually configure `PYTHONPATH` or duplicate code. Instead, they specify `mclib` as a dependency.

The library code itself lives in `src/mclib/`, and exports to the user through `src/mclib/__init__.py`. This allows you to import directly from `mclib` or its submodules.

## Modules Breakdown

### `config.py`
Provides a consolidated `Config` class for parsing `config.yaml` files. It bridges the gap between hardware aliases and Synnax channels, supporting both autosequence and simulation channel mapping requirements.

### `logger.py`
Provides centralized, class-based logging and printing utilities compatible with `prompt_toolkit`. Avoids global state for storage.
- `log()`: Logs messages with ISO timestamps, optional phase names, and color formatting.
- `write_logs_to_file()`: Writes captured logs to a file.
- `printf()`: A printing utility to handle `prompt_toolkit` display issues smoothly.

### `average.py`
Contains mathematical utilities for data analysis.
- `average_ch`: Implements Exponentially Weighted Moving Average (EWMA) for performant data smoothing.
- `sensor_vote_values()` / `sensor_vote()`: Provides a median-based voting mechanism for sensor redundancy.

### `phase.py`
Manages the `Phase` class for autosequences. A Phase is a function wrapper for a portion of logic, associated with a thread, and provides yielding (`sleep`, `wait_until`) and abort signal handling.

### `autosequence.py`
Manages the `Autosequence` wrapper class. It handles Synnax cluster login, orchestrates multiple `Phase` threads, and provides an interactive command-line interface via `prompt_toolkit`.

### `system.py`
Provides hardware simulation data structures (`State`, `Node`, `Valve`, and `System`). Used heavily by `simulation.py` to calculate thermodynamic properties, valve states, and fluid mass transfer.

### `utils.py`
Contains robust helper functions such as `open_vlv`, `close_vlv`, and `STATE`. These functions automatically consult the `Config` module to safely power or unpower a valve depending on its Normally Open (NO) or Normally Closed (NC) physical state.

---

## Developer Notes: How to Use

### 1. Script Setup
We use `uv` exclusively. When creating or modifying a standalone script (e.g. `launch.py`), use `uv run` and define dependencies in the script header.

To use `mclib` in a script, you must link it. You can automatically configure your script by running:
```bash
uv add --script path/to/your/script.py path/to/mclib
```
This adds `mclib` to the inline PEP 723 metadata block at the top of your script. Keep the Synnax version in your script synchronized with `mclib`'s `pyproject.toml` (e.g., `synnax==0.49.0` or `>=0.49.0`).

### 2. Importing
Once linked, `mclib` exposes all core classes and functions directly. You can import from the primary package or its submodules without worrying about relative `sys.path` hacks:

```python
from mclib import Autosequence, Phase, Config, log, open_vlv
from mclib.system import System
from mclib.average import average_ch
```

### 3. Adding New Functionality
If you need to add shared logic, figure out the logical file it belongs to inside `mclib/src/mclib/`. 
1. **Never use wildcard imports**. 
2. **Consider state carefully**: avoid global state when dealing with properties like simulation time or the active Synnax connections.
3. If you add a new widely used function, consider exposing it in `mclib/src/mclib/__init__.py`.
4. Run `uv lock` in the `mclib` root if you update external dependencies in `mclib/pyproject.toml`.
