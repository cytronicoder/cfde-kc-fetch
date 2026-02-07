"""
Unit tests for the CLI.
"""

import pytest

from cfde_kc_fetch.cli import create_parser, main


class TestCLIParser:
    """Test CLI argument parser."""

    def test_parser_creation(self):
        """Test that parser is created successfully."""
        parser = create_parser()
        assert parser is not None
        assert parser.prog == "cfde-kc-fetch"

    def test_version_flag(self):
        """Test --version flag."""
        parser = create_parser()

        # Should not raise - just test that it's configured
        with pytest.raises(SystemExit):
            parser.parse_args(["--version"])

    def test_help_flag(self):
        """Test --help flag."""
        parser = create_parser()

        with pytest.raises(SystemExit):
            parser.parse_args(["--help"])

    def test_global_timeout_option(self):
        """Test --timeout global option."""
        parser = create_parser()
        args = parser.parse_args(["--timeout", "120", "list-datasets"])
        assert args.timeout == 120

    def test_global_retries_option(self):
        """Test --retries global option."""
        parser = create_parser()
        args = parser.parse_args(["--retries", "5", "list-datasets"])
        assert args.retries == 5


class TestListDatasetsCommand:
    """Test list-datasets command parsing."""

    def test_basic_command(self):
        """Test basic list-datasets command."""
        parser = create_parser()
        args = parser.parse_args(["list-datasets"])

        assert args.command == "list-datasets"
        assert args.out == "dataset_metadata.json.gz"  # default
        assert args.overwrite is False  # default

    def test_with_output_path(self):
        """Test list-datasets with custom output path."""
        parser = create_parser()
        args = parser.parse_args(["list-datasets", "--out", "data/registry.json.gz"])

        assert args.out == "data/registry.json.gz"

    def test_with_overwrite(self):
        """Test list-datasets with overwrite flag."""
        parser = create_parser()
        args = parser.parse_args(["list-datasets", "--overwrite"])

        assert args.overwrite is True


class TestFetchAssetsCommand:
    """Test fetch-assets command parsing."""

    def test_basic_command(self):
        """Test basic fetch-assets command."""
        parser = create_parser()
        args = parser.parse_args(["fetch-assets", "heart"])

        assert args.command == "fetch-assets"
        assert args.dataset_id == "heart"
        assert args.out == "."  # default
        assert args.overwrite is False  # default
        assert args.decompress is False  # default

    def test_with_output_dir(self):
        """Test fetch-assets with custom output directory."""
        parser = create_parser()
        args = parser.parse_args(["fetch-assets", "lung", "--out", "data/lung"])

        assert args.dataset_id == "lung"
        assert args.out == "data/lung"

    def test_with_overwrite(self):
        """Test fetch-assets with overwrite flag."""
        parser = create_parser()
        args = parser.parse_args(["fetch-assets", "heart", "--overwrite"])

        assert args.overwrite is True

    def test_with_decompress(self):
        """Test fetch-assets with decompress flag."""
        parser = create_parser()
        args = parser.parse_args(["fetch-assets", "heart", "--decompress"])

        assert args.decompress is True

    def test_all_options(self):
        """Test fetch-assets with all options."""
        parser = create_parser()
        args = parser.parse_args([
            "fetch-assets",
            "kidney",
            "--out", "data/kidney",
            "--overwrite",
            "--decompress",
        ])

        assert args.dataset_id == "kidney"
        assert args.out == "data/kidney"
        assert args.overwrite is True
        assert args.decompress is True


class TestFetchGeneCommand:
    """Test fetch-gene command parsing."""

    def test_basic_command(self):
        """Test basic fetch-gene command."""
        parser = create_parser()
        args = parser.parse_args([
            "fetch-gene",
            "heart",
            "CP",
            "--out", "data/CP.json"
        ])

        assert args.command == "fetch-gene"
        assert args.dataset_id == "heart"
        assert args.gene == "CP"
        assert args.out == "data/CP.json"

    def test_different_genes(self):
        """Test fetch-gene with different gene symbols."""
        test_cases = [
            ("heart", "TP53", "data/TP53.json"),
            ("lung", "GAPDH", "data/GAPDH.json"),
            ("kidney", "CD8A", "data/CD8A.json"),
        ]

        parser = create_parser()
        for dataset, gene, output in test_cases:
            args = parser.parse_args([
                "fetch-gene",
                dataset,
                gene,
                "--out", output
            ])

            assert args.dataset_id == dataset
            assert args.gene == gene
            assert args.out == output

    def test_output_required(self):
        """Test that --out is required for fetch-gene."""
        parser = create_parser()

        # Should raise error when --out is missing
        with pytest.raises(SystemExit):
            parser.parse_args(["fetch-gene", "heart", "CP"])


class TestCommandRouting:
    """Test command routing in main function."""

    def test_no_command_shows_help(self):
        """Test that no command shows help and returns 1."""
        # When no command is provided, should return 1
        result = main([])
        assert result == 1

    def test_unknown_command(self):
        """Test handling of unknown commands."""
        # Parser validation should catch this before routing
        parser = create_parser()

        # Unknown subcommand should raise error
        with pytest.raises(SystemExit):
            parser.parse_args(["unknown-command"])


class TestGlobalOptions:
    """Test global options work with all commands."""

    def test_timeout_with_all_commands(self):
        """Test --timeout works with all commands."""
        parser = create_parser()

        commands = [
            ["--timeout", "120", "list-datasets"],
            ["--timeout", "120", "fetch-assets", "heart"],
            ["--timeout", "120", "fetch-gene", "heart", "CP", "--out", "out.json"],
        ]

        for cmd in commands:
            args = parser.parse_args(cmd)
            assert args.timeout == 120

    def test_retries_with_all_commands(self):
        """Test --retries works with all commands."""
        parser = create_parser()

        commands = [
            ["--retries", "5", "list-datasets"],
            ["--retries", "5", "fetch-assets", "heart"],
            ["--retries", "5", "fetch-gene", "heart", "CP", "--out", "out.json"],
        ]

        for cmd in commands:
            args = parser.parse_args(cmd)
            assert args.retries == 5
