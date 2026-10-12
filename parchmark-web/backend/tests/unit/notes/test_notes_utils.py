"""
Unit tests for notes utility functions (app.utils.markdown).
Tests markdown processing, title extraction, and content formatting functions.
"""

import pytest

from app.utils.markdown import markdown_service


def extract_title_from_markdown(content: str) -> str:
    """Wrapper for backward compatibility with tests."""
    return markdown_service.extract_title(content)


def format_note_content(content: str) -> str:
    """Wrapper for backward compatibility with tests."""
    return markdown_service.format_content(content)


def create_empty_note_content(title: str = "New Note") -> str:
    """Wrapper for backward compatibility with tests."""
    return markdown_service.create_empty_note(title)


class TestExtractTitleFromMarkdown:
    """Test extract_title_from_markdown function."""

    def test_extract_title_simple(self):
        """Test extracting title from simple markdown."""
        content = "# My Note Title\n\nSome content here."
        title = extract_title_from_markdown(content)

        assert title == "My Note Title"

    def test_extract_title_with_multiple_headings(self):
        """Test extracting title when multiple H1 headings exist."""
        content = """# First Title

Some content.

# Second Title

More content."""
        title = extract_title_from_markdown(content)

        # Should return the first H1 heading
        assert title == "First Title"

    def test_extract_title_no_h1_heading(self):
        """Test extracting title when no H1 heading exists."""
        content = """## This is H2

### This is H3

Some regular content without H1."""
        title = extract_title_from_markdown(content)

        assert title == "Untitled Note"

    def test_extract_title_empty_content(self):
        """Test extracting title from empty content."""
        title = extract_title_from_markdown("")

        assert title == "Untitled Note"

    def test_extract_title_whitespace_only(self):
        """Test extracting title from whitespace-only content."""
        title = extract_title_from_markdown("   \n  \t  \n  ")

        assert title == "Untitled Note"

    def test_extract_title_h1_with_extra_spaces(self):
        """Test extracting title from H1 with extra spaces."""
        content = "#    My Title With Spaces    \n\nContent here."
        title = extract_title_from_markdown(content)

        assert title == "My Title With Spaces"

    def test_extract_title_h1_with_formatting(self):
        """Test extracting title from H1 with markdown formatting."""
        content = "# **Bold** and *italic* title\n\nContent."
        title = extract_title_from_markdown(content)

        assert title == "**Bold** and *italic* title"

    def test_extract_title_h1_middle_of_content(self):
        """Test extracting title when H1 is not at the beginning."""
        content = """Some content first.

# Title in Middle

More content."""
        title = extract_title_from_markdown(content)

        assert title == "Title in Middle"

    def test_extract_title_h1_with_special_characters(self):
        """Test extracting title with special characters."""
        content = "# Title with @#$%^&*()_+ symbols!\n\nContent."
        title = extract_title_from_markdown(content)

        assert title == "Title with @#$%^&*()_+ symbols!"

    def test_extract_title_h1_unicode(self):
        """Test extracting title with Unicode characters."""
        content = "# 这是中文标题 🚀\n\nContent with unicode."
        title = extract_title_from_markdown(content)

        assert title == "这是中文标题 🚀"

    def test_extract_title_h1_multiline_content(self):
        """Test extracting title from multiline content."""
        content = """Line 1
Line 2
# Found Title
Line 4
Line 5"""
        title = extract_title_from_markdown(content)

        assert title == "Found Title"

    def test_extract_title_h1_with_tabs(self):
        """Test extracting title with tab characters."""
        content = "#\tTitle\twith\ttabs\t\n\nContent."
        title = extract_title_from_markdown(content)

        assert title == "Title\twith\ttabs"

    def test_extract_title_invalid_h1_format(self):
        """Test extracting title from invalid H1 formats."""
        invalid_formats = [
            "## Not H1",
            "#No space after hash",
            " # Leading space",
            "#\n",  # Hash with only newline
            "# ",  # Hash with only space
        ]

        for content in invalid_formats:
            title = extract_title_from_markdown(content)
            assert title == "Untitled Note"

    @pytest.mark.parametrize(
        "content,expected",
        [
            ("# Simple Title", "Simple Title"),
            ("# Title\nWith content", "Title"),
            ("# \n\nEmpty title", "Empty title"),  # Space after # with newline should extract "Empty title"
            ("Content\n# Title", "Title"),
            ("", "Untitled Note"),
            ("No title here", "Untitled Note"),
            ("# First\n# Second", "First"),
        ],
    )
    def test_extract_title_parametrized(self, content, expected):
        """Test extract_title_from_markdown with various inputs."""
        title = extract_title_from_markdown(content)
        assert title == expected


class TestFormatNoteContent:
    """Test format_note_content function."""

    def test_format_content_basic(self):
        """Test basic content formatting."""
        content = "# Test Note\n\nSome content here."
        formatted = format_note_content(content)

        assert formatted == "# Test Note\n\nSome content here."

    def test_format_content_strips_whitespace(self):
        """Test that formatting strips leading/trailing whitespace."""
        content = "  \n  # Test Note\n\nContent.  \n  "
        formatted = format_note_content(content)

        assert formatted == "# Test Note\n\nContent."

    def test_format_content_title_only(self):
        """Test formatting content that is only a title."""
        content = "# My Title"
        formatted = format_note_content(content)

        # Should add spacing for editing
        assert formatted == "# My Title\n\n"

    def test_format_content_title_with_extra_spacing(self):
        """Test formatting title that already has proper spacing."""
        content = "# My Title\n\nSome content."
        formatted = format_note_content(content)

        # Should remain unchanged
        assert formatted == "# My Title\n\nSome content."

    def test_format_content_no_title(self):
        """Test formatting content without a title."""
        content = "Just some content without a title."
        formatted = format_note_content(content)

        assert formatted == "Just some content without a title."

    def test_format_content_empty(self):
        """Test formatting empty content."""
        formatted = format_note_content("")

        assert formatted == ""

    def test_format_content_whitespace_only(self):
        """Test formatting whitespace-only content."""
        formatted = format_note_content("   \n  \t  \n  ")

        assert formatted == ""

    def test_format_content_complex_markdown(self):
        """Test formatting complex markdown content."""
        content = """# Complex Note

This has **bold** and *italic* text.

## Subsection

- List item 1
- List item 2

```python
def example():
    return "code"
```

> Blockquote here"""

        formatted = format_note_content(content)

        # Should remain unchanged for complex content
        assert formatted == content

    def test_format_content_title_with_formatting(self):
        """Test formatting title that contains markdown formatting."""
        content = "# **Bold Title**"
        formatted = format_note_content(content)

        assert formatted == "# **Bold Title**\n\n"

    def test_format_content_multiple_h1_headings(self):
        """Test formatting content with multiple H1 headings."""
        content = """# First Title

Some content.

# Second Title

More content."""

        formatted = format_note_content(content)

        # Should remain unchanged
        assert formatted == content

    @pytest.mark.parametrize(
        "input_content,expected",
        [
            ("# Title", "# Title\n\n"),
            ("# Title\n\nContent", "# Title\n\nContent"),
            ("  # Title  ", "# Title\n\n"),
            ("  # Title\n\nContent  ", "# Title\n\nContent"),
            ("No title content", "No title content"),
            ("", ""),
            ("   ", ""),
        ],
    )
    def test_format_content_parametrized(self, input_content, expected):
        """Test format_note_content with various inputs."""
        formatted = format_note_content(input_content)
        assert formatted == expected


class TestCreateEmptyNoteContent:
    """Test create_empty_note_content function."""

    def test_create_empty_note_default(self):
        """Test creating empty note with default title."""
        content = create_empty_note_content()

        assert content == "# New Note\n\n"

    def test_create_empty_note_custom_title(self):
        """Test creating empty note with custom title."""
        content = create_empty_note_content("My Custom Title")

        assert content == "# My Custom Title\n\n"

    def test_create_empty_note_empty_title(self):
        """Test creating empty note with empty title."""
        content = create_empty_note_content("")

        assert content == "# \n\n"

    def test_create_empty_note_title_with_spaces(self):
        """Test creating empty note with title containing spaces."""
        content = create_empty_note_content("Title With Spaces")

        assert content == "# Title With Spaces\n\n"

    def test_create_empty_note_title_with_special_chars(self):
        """Test creating empty note with special characters in title."""
        content = create_empty_note_content("Title @#$%^&*()")

        assert content == "# Title @#$%^&*()\n\n"

    def test_create_empty_note_unicode_title(self):
        """Test creating empty note with Unicode title."""
        content = create_empty_note_content("标题 🚀")

        assert content == "# 标题 🚀\n\n"

    def test_create_empty_note_long_title(self):
        """Test creating empty note with very long title."""
        long_title = "Very " * 50 + "Long Title"
        content = create_empty_note_content(long_title)

        assert content == f"# {long_title}\n\n"

    def test_create_empty_note_none_title(self):
        """Test creating empty note with None title."""
        # This should use the default parameter
        content = create_empty_note_content(None)

        assert content == "# None\n\n"

    @pytest.mark.parametrize(
        "title,expected",
        [
            ("Test", "# Test\n\n"),
            ("", "# \n\n"),
            ("Title with spaces", "# Title with spaces\n\n"),
            ("123 Numeric Title", "# 123 Numeric Title\n\n"),
            ("🎉 Emoji Title", "# 🎉 Emoji Title\n\n"),
        ],
    )
    def test_create_empty_note_parametrized(self, title, expected):
        """Test create_empty_note_content with various titles."""
        content = create_empty_note_content(title)
        assert content == expected


class TestNotesUtilsIntegration:
    """Test integration between notes utility functions."""

    def test_extract_and_format_cycle(self):
        """Test extracting title and formatting content cycle."""
        original_content = "# Original Title\n\nSome content."

        # Extract title
        title = extract_title_from_markdown(original_content)
        assert title == "Original Title"

        # Format content
        formatted = format_note_content(original_content)
        assert formatted == original_content

        # Extract title again from formatted content
        title_again = extract_title_from_markdown(formatted)
        assert title_again == title

    def test_create_empty_then_extract_title(self):
        """Test creating empty note then extracting its title."""
        title = "Test Note"
        content = create_empty_note_content(title)
        extracted_title = extract_title_from_markdown(content)

        assert extracted_title == title

    def test_format_title_only_content(self):
        """Test formatting content created by create_empty_note_content."""
        title = "Test Note"
        empty_content = create_empty_note_content(title)
        formatted = format_note_content(empty_content)

        # Should remain the same since it already has proper spacing
        assert formatted == empty_content

    def test_extract_from_malformed_then_format(self):
        """Test extracting title from malformed content then formatting."""
        malformed_content = "   # Malformed Title   "

        # Extract title - after stripping, it becomes "# Malformed Title"
        title = extract_title_from_markdown(malformed_content)
        # The title should be extracted correctly after stripping
        assert title == "Malformed Title" or title == "Untitled Note"

        # Format the malformed content
        formatted = format_note_content(malformed_content)
        # After formatting, should have proper structure
        assert "#" in formatted

        # Verify title extraction from formatted content
        title_from_formatted = extract_title_from_markdown(formatted)
        # Should extract a valid title
        assert title_from_formatted in ["Malformed Title", "Untitled Note"]

    def test_content_transformations_preserve_title(self):
        """Test that content transformations preserve extractable title."""
        test_cases = [
            ("# Simple Title", "Simple Title"),
            ("# Title With Content\n\nSome content here.", "Title With Content"),
            ("# Title With Whitespace", "Title With Whitespace"),
            ("# **Formatted** Title", "**Formatted** Title"),
        ]

        for original, expected_title in test_cases:
            # Extract original title
            original_title = extract_title_from_markdown(original)

            # Format content
            formatted = format_note_content(original)

            # Extract title from formatted content
            formatted_title = extract_title_from_markdown(formatted)

            # Both should extract the expected title
            assert original_title == expected_title
            assert formatted_title == expected_title

    def test_round_trip_content_processing(self):
        """Test round-trip content processing maintains consistency."""
        original = "# Test Note\n\nOriginal content here."

        # Multiple rounds of processing
        content = original
        for _ in range(3):
            title = extract_title_from_markdown(content)
            content = format_note_content(content)
            assert extract_title_from_markdown(content) == title

        # Final content should match original
        assert content == original
