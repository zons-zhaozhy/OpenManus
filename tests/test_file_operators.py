"""
File operators tests
"""

from pathlib import Path
from unittest.mock import mock_open, patch

import pytest

from app.tool.file_operators import FileOperators


@pytest.fixture
def test_dir(tmp_path):
    """Create test directory structure"""
    test_dir = tmp_path / "test_files"
    test_dir.mkdir()

    # Create test files
    (test_dir / "test1.txt").write_text("Test content 1")
    (test_dir / "test2.txt").write_text("Test content 2")
    (test_dir / "subdir").mkdir()
    (test_dir / "subdir" / "test3.txt").write_text("Test content 3")

    return test_dir


@pytest.fixture
def file_ops():
    """Create file operators instance"""
    return FileOperators()


def test_read_file(file_ops, test_dir):
    """Test file reading"""
    file_path = test_dir / "test1.txt"
    content = file_ops.read_file(str(file_path))
    assert content == "Test content 1"


def test_write_file(file_ops, test_dir):
    """Test file writing"""
    file_path = test_dir / "new_file.txt"
    content = "New test content"

    file_ops.write_file(str(file_path), content)
    assert file_path.read_text() == content


def test_append_file(file_ops, test_dir):
    """Test file appending"""
    file_path = test_dir / "test1.txt"
    additional_content = "\nAdditional content"

    file_ops.append_file(str(file_path), additional_content)
    assert file_path.read_text() == "Test content 1" + additional_content


def test_delete_file(file_ops, test_dir):
    """Test file deletion"""
    file_path = test_dir / "test1.txt"
    assert file_path.exists()

    file_ops.delete_file(str(file_path))
    assert not file_path.exists()


def test_list_files(file_ops, test_dir):
    """Test file listing"""
    files = file_ops.list_files(str(test_dir))
    assert len(files) == 3
    assert "test1.txt" in [Path(f).name for f in files]
    assert "test2.txt" in [Path(f).name for f in files]
    assert "test3.txt" in [Path(f).name for f in files]


def test_list_files_with_pattern(file_ops, test_dir):
    """Test file listing with pattern"""
    files = file_ops.list_files(str(test_dir), pattern="*.txt")
    assert len(files) == 2  # Only files in root directory
    assert "test1.txt" in [Path(f).name for f in files]
    assert "test2.txt" in [Path(f).name for f in files]


def test_create_directory(file_ops, test_dir):
    """Test directory creation"""
    new_dir = test_dir / "new_dir"
    file_ops.create_directory(str(new_dir))
    assert new_dir.is_dir()


def test_delete_directory(file_ops, test_dir):
    """Test directory deletion"""
    subdir = test_dir / "subdir"
    assert subdir.exists()

    file_ops.delete_directory(str(subdir))
    assert not subdir.exists()


def test_copy_file(file_ops, test_dir):
    """Test file copying"""
    source = test_dir / "test1.txt"
    target = test_dir / "test1_copy.txt"

    file_ops.copy_file(str(source), str(target))
    assert target.exists()
    assert target.read_text() == source.read_text()


def test_move_file(file_ops, test_dir):
    """Test file moving"""
    source = test_dir / "test1.txt"
    target = test_dir / "test1_moved.txt"
    original_content = source.read_text()

    file_ops.move_file(str(source), str(target))
    assert not source.exists()
    assert target.exists()
    assert target.read_text() == original_content


def test_get_file_info(file_ops, test_dir):
    """Test file info retrieval"""
    file_path = test_dir / "test1.txt"
    info = file_ops.get_file_info(str(file_path))

    assert info["exists"]
    assert info["size"] > 0
    assert info["is_file"]
    assert not info["is_dir"]
    assert "created" in info
    assert "modified" in info


def test_file_not_found(file_ops, test_dir):
    """Test handling of non-existent files"""
    nonexistent = test_dir / "nonexistent.txt"

    with pytest.raises(FileNotFoundError):
        file_ops.read_file(str(nonexistent))


def test_invalid_path(file_ops):
    """Test handling of invalid paths"""
    with pytest.raises(ValueError):
        file_ops.read_file("")


def test_permission_error(file_ops, test_dir):
    """Test handling of permission errors"""
    file_path = test_dir / "test1.txt"

    with patch("builtins.open", side_effect=PermissionError):
        with pytest.raises(PermissionError):
            file_ops.read_file(str(file_path))


def test_directory_exists(file_ops, test_dir):
    """Test handling of existing directories"""
    with pytest.raises(IsADirectoryError):
        file_ops.read_file(str(test_dir))


def test_file_exists_error(file_ops, test_dir):
    """Test handling of existing files when creating directories"""
    file_path = test_dir / "test1.txt"
    with pytest.raises(FileExistsError):
        file_ops.create_directory(str(file_path))
