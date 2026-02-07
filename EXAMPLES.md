# Examples

This page gives a few short, practical examples.

Install (editable):

```bash
pip install -e .
```

Basic commands:

- List datasets (download registry):

```bash
cfde-kc-fetch list-datasets --out data/registry.json.gz
```

- Download assets for a dataset:

```bash
cfde-kc-fetch fetch-assets heart --out data/heart
```

- Query a single gene and save the JSON result:

```bash
cfde-kc-fetch fetch-gene heart CP --out data/heart/genes/CP.json
```

> [!TIP]
>
> - Use `--decompress` to create decompressed copies alongside `.gz` files.
> - Increase `--timeout` and `--retries` for slow or unstable networks.
> - Each run writes `run_params.json` to the output directory to record provenance.

If something is unclear or fails, please open an issue with the command you ran and the error message (I'll try to improve the docs).
