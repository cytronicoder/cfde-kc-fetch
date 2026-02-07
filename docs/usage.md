# Usage & Reference

This document contains the detailed usage information and reference material for `cfde-kc-fetch`.

## API Endpoints

This tool interacts with the following CFDE Knowledge Center API endpoints:

### Dataset Registry

- **URL**: `https://cfde.hugeampkpnbi.org/api/raw/file/single_cell_metadata/dataset_metadata.json.gz`
- **Purpose**: Metadata for all available single-cell datasets

### Raw File Downloads

- **Base URL**: `https://cfde.hugeampkpnbi.org/api/raw/file/`
- **Examples**:
  - `single_cell/<dataset_id>/coordinates.tsv.gz` - Cell coordinate data for visualization
  - `single_cell/<dataset_id>/fields.json.gz` - Field definitions and metadata

### Gene Expression Query

- **URL**: `https://cfde.hugeampkpnbi.org/api/bio/query/single-cell-lognorm`
- **Parameters**: `q=<dataset_id>,<gene>` (comma-separated)
- **Purpose**: Query log-normalized gene expression values for a specific dataset and gene

For complete API documentation, see the **[Swagger UI](https://cfde.hugeampkpnbi.org/docs)**.

## Installation

### From Source

```bash
git clone https://github.com/cytronicoder/cfde-kc-fetch.git
cd cfde-kc-fetch
pip install -e .
```

### Dependencies

Minimal dependencies (stdlib + requests):

- `requests>=2.25.0` - HTTP client with retry support
- `urllib3>=1.26.0` - HTTP connection pooling

## Quickstart

Three short examples to get going; use `--help` for options.

List datasets (download registry):

```bash
cfde-kc-fetch list-datasets --out data/registry.json.gz
```

Download dataset assets (coordinates + fields):

```bash
cfde-kc-fetch fetch-assets heart --out data/heart
# or add --decompress to write decompressed copies alongside .gz files
```

Query a gene (saves JSON):

```bash
cfde-kc-fetch fetch-gene heart CP --out data/heart/genes/CP.json
```

Each command writes a `run_params.json` file with the CLI arguments and endpoints used; use it to record provenance.

## Output Directory Structure

```
data/
├── registry.json.gz              # Dataset registry
├── run_params.json               # Reproducibility metadata
└── heart/
    ├── coordinates.tsv.gz        # Cell coordinates for visualization
    ├── fields.json.gz            # Field definitions
    ├── run_params.json           # Asset download metadata
    └── genes/
        ├── CP.json               # Gene expression data for CP
        └── run_params.json       # Gene query metadata
```

## CLI Reference

### Global Options

```bash
cfde-kc-fetch --help
cfde-kc-fetch --version
cfde-kc-fetch --timeout 120 --retries 5 <command>
```

- `--timeout`: Request timeout in seconds (default: 60)
- `--retries`: Number of retry attempts for failed requests (default: 3)

### Commands

#### `list-datasets`

Download and display the dataset registry.

```bash
cfde-kc-fetch list-datasets [options]
```

**Options:**

- `--out PATH`: Output path for registry file (default: `dataset_metadata.json.gz`)
- `--overwrite`: Overwrite existing files

**Example:**

```bash
cfde-kc-fetch list-datasets --out registries/latest.json.gz --overwrite
```

#### `fetch-assets`

Download single-cell dataset assets (coordinates and fields).

```bash
cfde-kc-fetch fetch-assets <dataset_id> [options]
```

**Arguments:**

- `dataset_id`: Dataset identifier (e.g., `heart`, `lung`)

**Options:**

- `--out DIR`: Output directory (default: current directory)
- `--overwrite`: Overwrite existing files
- `--decompress`: Decompress `.gz` files (keeps `.gz` by default)

**Example:**

```bash
cfde-kc-fetch fetch-assets kidney --out data/kidney --decompress
```

#### `fetch-gene`

Query log-normalized gene expression data.

```bash
cfde-kc-fetch fetch-gene <dataset_id> <gene> --out <path>
```

**Arguments:**

- `dataset_id`: Dataset identifier (e.g., `heart`, `lung`)
- `gene`: Gene symbol (e.g., `CP`, `TP53`, `GAPDH`)

**Options:**

- `--out PATH`: **Required**. Output path for JSON response

**Example:**

```bash
cfde-kc-fetch fetch-gene lung TP53 --out data/lung/genes/TP53.json
```

## Python API

You can also use the package programmatically:

```python
from cfde_kc_fetch import CFDEClient, download_dataset_registry, download_single_cell_assets, fetch_single_cell_lognorm

# Initialize client
client = CFDEClient(timeout=120, retries=5)

# Download registry
registry = download_dataset_registry("data/registry.json.gz", client=client)
print(f"Found {len(registry)} datasets")

# Download dataset assets
assets = download_single_cell_assets(
    dataset_id="heart",
    output_dir="data/heart",
    decompress=True,
    client=client
)

# Query gene expression
data = fetch_single_cell_lognorm(
    dataset_id="heart",
    gene="CP",
    output_path="data/heart/genes/CP.json",
    client=client
)
```

## Troubleshooting

If a command fails, the message usually explains why. Common fixes:

- Timeouts or slow networks: increase `--timeout` and `--retries` (e.g., `--timeout 300 --retries 5`).
- Invalid dataset ID: ensure it matches `[A-Za-z0-9._-]+` (no slashes or spaces).
- File exists: add `--overwrite` to replace existing files.
- 404 Not Found: run `cfde-kc-fetch list-datasets` and confirm the dataset ID; some datasets do not expose every asset.
- Gzip issues: use `--decompress` or decompress manually with `gunzip -k`.

If none of these help, please include the exact command and error message when opening an issue.

## Notes

- Some datasets do not provide a full expression matrix; gene-by-gene queries (`single-cell-lognorm`) are available as an alternative.
- Each run writes `run_params.json` to the output directory to help record provenance.
- The client uses exponential backoff for retries; be considerate of the API when making repeated requests.
