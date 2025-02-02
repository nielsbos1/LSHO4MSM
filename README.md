# LSHO4MSM

![Python Version](https://img.shields.io/badge/python-3.10.6-blue)
![License](https://img.shields.io/badge/license-MIT-green)

Code for Locality Sensitive Hashing Optimization for Multi-component Similarity Method (LSHO4MSM)

## Project overview

This project implements and evaluates Locality Sensitive Hashing (LSH) optimization techniques. It includes implementations of MinHash and Fill Sketch Scheme (FSS) algorithms, along with tools for parameter optimization and performance evaluation.

## Quick Start

```bash
# Clone the repository
git clone https://github.com/nielsbos1/LSHO4MSM
cd lsho4msm

# Create and activate environment
uv sync

# Run a sample analysis
uv run python -m src.core.lsh_bootstrap
```

## Installation

### Requirements

- uv (Python package manager)
- C compiler (MinGW-w64 for Windows)

Follow installation instructions for uv (Python package maneger) from https://docs.astral.sh/uv/getting-started/installation/#installation-methods

### Set-up

The uv virtual environment can be created with the following command.

```bash
uv sync
```

## Running scripts

From the root of repository, use uv to run python scripts. For example:

```bash
uv run python -m src.core.lsh_bootstrap
```

### Other examples

```bash
uv run python -m src.visualization.plotting
uv run python -m src.visualization.max_alpha_table
uv run python -m src.visualization.model_words_jaccard_stat
```

## C dependencies

This project contains a custom Python dependency that depends on certain C binaries to be available on the OS. For Windows machines, https://www.mingw-w64.org/ may be used.

## Project structure

```bash
LSHO4MSM/
├── data/                  # Data directory for input files
├── figures/               # Directory for generated figures and plots
├── results/               # Results and output files
├── src/                   # Source code directory
│   ├── analysis/          # Analysis modules
│   ├── core/              # Core LSH implementation
│   ├── datasketch_niels/  # Custom datasketch implementation based on datasketch Python package
│   ├── utils/             # Utility functions and helpers
│   └── visualization/     # Visualization and plotting modules
├── .gitignore             # Git ignore file
├── .python-version        # Python version specification
├── config.toml            # Configuration file
├── pyproject.toml         # Project metadata and dependencies
├── README.md              # Project documentation
└── uv.lock                # Lock file for uv package manager
```

### Core Modules

#### core/data_preprocessor.py

- Handles data preprocessing and cleaning
- Extracts model words and brands from product data
- Manages duplicate detection

#### core/lsh_bootstrap.py

- Implements bootstrap analysis for LSH performance evaluation
- Configurable parameters for number of permutations and iterations
- Generates comparative metrics between different LSH schemes

#### core/lsh_utils.py

- Utility functions for LSH operations
- Sketch generation and candidate pair filtering

#### core/optimize_parameters.py

- Parameter optimization for LSH schemes
- Error probability calculations

### Analysis

#### analysis/comparing_fss_minhash_preciseness.py

- Comparative analysis between FSS and MinHash approaches
- Preciseness metrics calculation
- Statistical evaluation tools

### Visualization

#### visualization/plotting.py

- Visualization tools for LSH performance metrics
- S-curve generation and comparison plots
- Error analysis visualization

#### visualization/max_alpha_table.py

- Maximum alpha value calculations
- Performance metric tables
- Comparative analysis output

#### visualization/model_words_jaccard_stats.py

- Jaccard similarity statistics for model words
- Distribution analysis

### Support Modules

#### utils/seeds.py

- Seed generation and management for hash functions
- Maintains consistency in random number generation

## Custom Datasketch Implementation

The `datasketch_custom_implementation/` directory contains custom extensions to the Python datasketch package, implementing novel LSH techniques and optimizations:

### Key Components

- `fill_sketch.py`: Implementation of FillSketch, an alternative sketching algorithm that uses a different approach for signature generation than traditional MinHash
- `lsh_amplified.py`: Two-stage LSH implementation that amplifies accuracy through cascaded filtering
- `mixed_tab.py`: Efficient mixed tabulation hashing implementation for faster hash computations

## Configuration

The project uses several configuration files:

- `config.toml`: Main configuration file for LSH parameters and brand names
- `pyproject.toml`: Project metadata and dependencies
- `seeds.txt`: Seed values for reproducible results

## Troubleshooting

Common issues and solutions:

### C Compiler Issues

If you encounter C compiler errors:

1. Ensure MinGW-w64 is properly installed
2. Add MinGW-w64 to your system PATH
