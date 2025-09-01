"""Unit tests for CLI glob caching functions."""

from pathlib import Path
from typing import Generator

import pytest

from yamlfix.entrypoints.cli import (
    _GLOB_CACHE,
    _clear_glob_cache,
    _glob_cache,
    _rglob_cache,
)


@pytest.fixture(autouse=True)
def _clear_cache() -> Generator[None, None, None]:
    """Clear the glob cache before and after each test."""
    _clear_glob_cache()
    yield
    _clear_glob_cache()


@pytest.fixture
def test_directory(tmp_path: Path) -> Path:
    """Create a test directory structure with YAML files."""
    # Create files in root
    (tmp_path / "test.yaml").write_text("test")
    (tmp_path / "test.yml").write_text("test")
    (tmp_path / "other.txt").write_text("test")

    # Create subdirectory with nested files
    subdir = tmp_path / "subdir"
    subdir.mkdir()
    (subdir / "nested.yaml").write_text("test")
    (subdir / "nested.yml").write_text("test")

    return tmp_path


class TestGlobCache:
    """Test the _glob_cache function."""

    def test_glob_cache_basic_functionality(self, test_directory: Path) -> None:
        """Test that _glob_cache returns correct files and caches results."""
        result = _glob_cache(test_directory, "*.yaml")

        # Should find files in current directory only (not recursive)
        assert test_directory / "test.yaml" in result
        assert test_directory / "subdir" / "nested.yaml" not in result

        # Cache should be populated
        assert len(_GLOB_CACHE) == 1
        cache_key = (str(test_directory), "*.yaml", "g")
        assert cache_key in _GLOB_CACHE

    def test_glob_cache_uses_cache_on_repeat_calls(self, test_directory: Path) -> None:
        """Test that subsequent calls use cached results."""
        # First call
        result1 = _glob_cache(test_directory, "*.yaml")
        cache_size_after_first = len(_GLOB_CACHE)

        # Second call should use cache
        result2 = _glob_cache(test_directory, "*.yaml")
        cache_size_after_second = len(_GLOB_CACHE)

        assert result1 == result2
        assert cache_size_after_first == cache_size_after_second == 1

    def test_glob_cache_different_patterns_create_separate_entries(
        self, test_directory: Path
    ) -> None:
        """Test that different glob patterns create separate cache entries."""
        result_yaml = _glob_cache(test_directory, "*.yaml")
        result_yml = _glob_cache(test_directory, "*.yml")

        assert len(_GLOB_CACHE) == 2
        assert result_yaml != result_yml
        assert test_directory / "test.yaml" in result_yaml
        assert test_directory / "test.yml" in result_yml

    def test_glob_cache_different_directories_create_separate_entries(
        self, test_directory: Path
    ) -> None:
        """Test that different directories create separate cache entries."""
        # Create another directory
        other_dir = test_directory / "other"
        other_dir.mkdir()
        (other_dir / "other.yaml").write_text("test")

        result1 = _glob_cache(test_directory, "*.yaml")
        result2 = _glob_cache(other_dir, "*.yaml")

        assert len(_GLOB_CACHE) == 2
        assert result1 != result2
        assert test_directory / "test.yaml" in result1
        assert other_dir / "other.yaml" in result2


class TestRglobCache:
    """Test the _rglob_cache function."""

    def test_rglob_cache_basic_functionality(self, test_directory: Path) -> None:
        """Test that _rglob_cache returns correct files recursively and caches results."""
        result = _rglob_cache(test_directory, "*.yaml")

        # Should find files recursively
        assert test_directory / "test.yaml" in result
        assert test_directory / "subdir" / "nested.yaml" in result

        # Cache should be populated with rglob key
        assert len(_GLOB_CACHE) == 1
        cache_key = (str(test_directory), "*.yaml", "r")
        assert cache_key in _GLOB_CACHE

    def test_rglob_cache_vs_glob_cache_different_keys(
        self, test_directory: Path
    ) -> None:
        """Test that rglob and glob use different cache keys."""
        glob_result = _glob_cache(test_directory, "*.yaml")
        rglob_result = _rglob_cache(test_directory, "*.yaml")

        # Should have separate cache entries
        assert len(_GLOB_CACHE) == 2

        # Results should be different (rglob includes nested files)
        assert len(rglob_result) > len(glob_result)
        assert test_directory / "subdir" / "nested.yaml" in rglob_result
        assert test_directory / "subdir" / "nested.yaml" not in glob_result

    def test_rglob_cache_uses_cache_on_repeat_calls(self, test_directory: Path) -> None:
        """Test that subsequent rglob calls use cached results."""
        result1 = _rglob_cache(test_directory, "*.yaml")
        cache_size_after_first = len(_GLOB_CACHE)

        result2 = _rglob_cache(test_directory, "*.yaml")
        cache_size_after_second = len(_GLOB_CACHE)

        assert result1 == result2
        assert cache_size_after_first == cache_size_after_second == 1


class TestCacheClear:
    """Test the _clear_glob_cache function."""

    def test_clear_glob_cache_empties_cache(self, test_directory: Path) -> None:
        """Test that cache clearing removes all entries."""
        # Populate cache with several entries
        _glob_cache(test_directory, "*.yaml")
        _glob_cache(test_directory, "*.yml")
        _rglob_cache(test_directory, "*.yaml")

        assert len(_GLOB_CACHE) == 3

        # Clear cache
        _clear_glob_cache()

        assert len(_GLOB_CACHE) == 0

    def test_clear_glob_cache_allows_fresh_caching(self, test_directory: Path) -> None:
        """Test that after clearing, caching works normally again."""
        # First round of caching
        _glob_cache(test_directory, "*.yaml")
        assert len(_GLOB_CACHE) == 1

        # Clear and verify empty
        _clear_glob_cache()
        assert len(_GLOB_CACHE) == 0

        # Second round should work normally
        _glob_cache(test_directory, "*.yaml")
        assert len(_GLOB_CACHE) == 1


class TestCacheKeyConstruction:
    """Test that cache keys are constructed correctly."""

    def test_cache_key_includes_directory_path(self, test_directory: Path) -> None:
        """Test that cache keys include the directory path."""
        _glob_cache(test_directory, "*.yaml")

        expected_key = (str(test_directory), "*.yaml", "g")
        assert expected_key in _GLOB_CACHE

    def test_cache_key_distinguishes_glob_vs_rglob(self, test_directory: Path) -> None:
        """Test that glob and rglob operations have different key suffixes."""
        _glob_cache(test_directory, "*.yaml")
        _rglob_cache(test_directory, "*.yaml")

        glob_key = (str(test_directory), "*.yaml", "g")
        rglob_key = (str(test_directory), "*.yaml", "r")

        assert glob_key in _GLOB_CACHE
        assert rglob_key in _GLOB_CACHE
        assert len(_GLOB_CACHE) == 2
