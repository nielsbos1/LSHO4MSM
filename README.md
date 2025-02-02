# LSHO4MSM
Code for Locality Sensitive Hashing Optimization for MSM

## Installation
Almost all code in this repository is Python code. 

Follow installation instructions for uv (Python package maneger) from https://docs.astral.sh/uv/getting-started/installation/#installation-methods

## Run

```bash
uv run python -m src.core.lsh_bootstrap
```

```bash
uv run python -m src.visualization.plotting
uv run python -m src.visualization.max_alpha_table
uv run python -m src.visualization.model_words_jaccard_stat
```


## C dependencies
This project contains a custom Python dependency that depends on certain C binaries to be available on the OS. For Windows machines, https://www.mingw-w64.org/ may be used. 