"""
String replace editor tests
"""

import pytest
from pathlib import Path
from unittest.mock import patch, mock_open
from app.tool.str_replace_editor import StringReplaceEditor

@pytest.fixture
def test_dir(tmp_path):
    """Create test directory structure"""
    test_dir = tmp_path / "test_files"
    test_dir.mkdir()

    # Create test files
    (test_dir / "test.py").write_text("""
def test_function():
    print("Hello, World!")
    return 42

def another_function():
    x = 10
    y = 20
    return x + y
""")

    return test_dir

@pytest.fixture
def editor():
    """Create string replace editor instance"""
    return StringReplaceEditor()

def test_simple_replace(editor, test_dir):
    """Test simple string replacement"""
    file_path = test_dir / "test.py"
    old_string = 'print("Hello, World!")'
    new_string = 'print("Hello, Universe!")'

    editor.replace(str(file_path), old_string, new_string)
    content = file_path.read_text()
    assert new_string in content
    assert old_string not in content

def test_replace_with_indentation(editor, test_dir):
    """Test replacement preserving indentation"""
    file_path = test_dir / "test.py"
    old_string = '    print("Hello, World!")'
    new_string = '    print("Hello, Universe!")'

    editor.replace(str(file_path), old_string, new_string)
    content = file_path.read_text()
    assert new_string in content
    assert old_string not in content

def test_replace_multiple_lines(editor, test_dir):
    """Test multi-line string replacement"""
    file_path = test_dir / "test.py"
    old_string = """def another_function():
    x = 10
    y = 20"""
    new_string = """def another_function():
    a = 30
    b = 40"""

    editor.replace(str(file_path), old_string, new_string)
    content = file_path.read_text()
    assert new_string in content
    assert old_string not in content

def test_replace_with_regex_chars(editor, test_dir):
    """Test replacement with regex special characters"""
    file_path = test_dir / "test.py"
    (file_path).write_text("value = $100 + (200 * 3)")
    old_string = "$100 + (200 * 3)"
    new_string = "$150 + (250 * 4)"

    editor.replace(str(file_path), old_string, new_string)
    content = file_path.read_text()
    assert new_string in content
    assert old_string not in content

def test_replace_with_whitespace(editor, test_dir):
    """Test replacement with significant whitespace"""
    file_path = test_dir / "test.py"
    old_string = "    x = 10\n    y = 20"
    new_string = "    x = 30\n    y = 40"

    editor.replace(str(file_path), old_string, new_string)
    content = file_path.read_text()
    assert new_string in content
    assert old_string not in content

def test_no_match_found(editor, test_dir):
    """Test handling when no match is found"""
    file_path = test_dir / "test.py"
    old_string = "nonexistent code"
    new_string = "replacement code"

    with pytest.raises(ValueError):
        editor.replace(str(file_path), old_string, new_string)

def test_multiple_matches(editor, test_dir):
    """Test handling of multiple matches"""
    file_path = test_dir / "test.py"
    (file_path).write_text("value = 42\nother = 42\n")
    old_string = "42"
    new_string = "100"

    with pytest.raises(ValueError):
        editor.replace(str(file_path), old_string, new_string)

def test_file_not_found(editor, test_dir):
    """Test handling of non-existent files"""
    file_path = test_dir / "nonexistent.py"
    old_string = "test"
    new_string = "replacement"

    with pytest.raises(FileNotFoundError):
        editor.replace(str(file_path), old_string, new_string)

def test_permission_error(editor, test_dir):
    """Test handling of permission errors"""
    file_path = test_dir / "test.py"
    old_string = "test"
    new_string = "replacement"

    with patch("builtins.open", side_effect=PermissionError):
        with pytest.raises(PermissionError):
            editor.replace(str(file_path), old_string, new_string)

def test_empty_strings(editor, test_dir):
    """Test handling of empty strings"""
    file_path = test_dir / "test.py"

    with pytest.raises(ValueError):
        editor.replace(str(file_path), "", "replacement")

    with pytest.raises(ValueError):
        editor.replace(str(file_path), "test", "")

def test_identical_strings(editor, test_dir):
    """Test handling of identical old and new strings"""
    file_path = test_dir / "test.py"
    test_string = "print('test')"

    with pytest.raises(ValueError):
        editor.replace(str(file_path), test_string, test_string)

def test_backup_creation(editor, test_dir):
    """Test backup file creation"""
    file_path = test_dir / "test.py"
    backup_path = file_path.with_suffix(file_path.suffix + ".bak")
    original_content = file_path.read_text()

    editor.replace(str(file_path), 'print("Hello, World!")', 'print("Hello, Universe!")')

    assert backup_path.exists()
    assert backup_path.read_text() == original_content

def test_restore_from_backup(editor, test_dir):
    """Test restoration from backup"""
    file_path = test_dir / "test.py"
    original_content = file_path.read_text()

    editor.replace(str(file_path), 'print("Hello, World!")', 'print("Hello, Universe!")')
    editor.restore_backup(str(file_path))

    assert file_path.read_text() == original_content

def test_backup_not_found(editor, test_dir):
    """Test handling when backup file is not found"""
    file_path = test_dir / "test.py"

    with pytest.raises(FileNotFoundError):
        editor.restore_backup(str(file_path))
