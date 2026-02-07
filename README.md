# CFDE Knowledge Center Dataset Fetcher

A small CLI and library for downloading CFDE Knowledge Center single-cell artifacts and querying gene-level log-normalized expression.

This repository contains a brief README and a `docs/` directory with usage instructions, examples, and development notes. If you need detailed guidance, see `docs/usage.md` and `docs/examples.md`.

Quick links:

- Full usage: `docs/usage.md`
- Short examples: `docs/examples.md`
- API docs (Swagger UI): <https://cfde.hugeampkpnbi.org/docs>

Install from PyPI:

```bash
pip install cfde-kc-fetch
```

If you spot missing information or a confusing message in the tool, please open an issue with a minimal reproduction and the command you ran.

## Development & Testing

To run tests locally:

```bash
pip install -e ".[dev]"
pytest tests/
```

Project layout (essential):

- `cfde_kc_fetch/` — package code
- `tests/` — unit tests

## References

- CFDE Knowledge Center: <https://cfdeknowledge.org>
- API docs (Swagger UI): <https://cfde.hugeampkpnbi.org/docs>
- Single Cell Browser: <https://cfdeknowledge.org/single-cell/>

## License

MIT License - See LICENSE file for details.

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## Citation

If you use this tool in your research, please cite:

```bibtex
@software{cfde_kc_fetch,
  title = {CFDE Knowledge Center Dataset Fetcher},
  author = {Zeyu Yao},
  year = {2026},
  url = {https://github.com/cytronicoder/cfde-kc-fetch}
}
```
