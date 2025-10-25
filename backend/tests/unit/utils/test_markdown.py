"""
Unit tests for markdown utility functions (app.utils.markdown).
Tests the MarkdownService class and its methods.
"""

import pytest

from app.utils.markdown import MarkdownService, markdown_service


class TestMarkdownServiceExtractTitle:
    """Test extract_title method."""

    def test_extract_title_simple(self):
        """Test extracting title from simple markdown."""
        content = "# My Note Title\n\nSome content here."
        title = markdown_service.extract_title(content)
        assert title == "My Note Title"

    def test_extract_title_with_multiple_headings(self):
        """Test extracting title when multiple H1 headings exist."""
        content = "# First Title\n\nSome content.\n\n# Second Title\n\nMore content."
        title = markdown_service.extract_title(content)
        assert title == "First Title"

    def test_extract_title_no_h1_heading(self):
        """Test extracting title when no H1 heading exists."""
        content = "## This is H2\n\n### This is H3\n\nSome regular content without H1."
        title = markdown_service.extract_title(content)
        assert title == "Untitled Note"

    def test_extract_title_empty_content(self):
        """Test extracting title from empty content."""
        title = markdown_service.extract_title("")
        assert title == "Untitled Note"

    def test_extract_title_whitespace_only(self):
        """Test extracting title from whitespace-only content."""
        title = markdown_service.extract_title("   \n  \t  \n  ")
        assert title == "Untitled Note"

    def test_extract_title_with_extra_spaces(self):
        """Test extracting title from H1 with extra spaces."""
        content = "#    My Title With Spaces    \n\nContent here."
        title = markdown_service.extract_title(content)
        assert title == "My Title With Spaces"

    def test_extract_title_with_special_characters(self):
        """Test extracting title with special characters."""
        content = "# Title with @#$%^&*()_+ symbols!\n\nContent."
        title = markdown_service.extract_title(content)
        assert title == "Title with @#$%^&*()_+ symbols!"

    def test_extract_title_unicode(self):
        """Test extracting title with Unicode characters."""
        content = "# 这是中文标题 🚀\n\nContent with unicode."
        title = markdown_service.extract_title(content)
        assert title == "这是中文标题 🚀"


class TestMarkdownServiceFormatContent:
    """Test format_content method."""

    def test_format_content_basic(self):
        """Test basic content formatting."""
        content = "# Test Note\n\nSome content here."
        formatted = markdown_service.format_content(content)
        assert formatted == "# Test Note\n\nSome content here."

    def test_format_content_strips_whitespace(self):
        """Test that formatting strips leading/trailing whitespace."""
        content = "  \n  # Test Note\n\nContent.  \n  "
        formatted = markdown_service.format_content(content)
        assert formatted == "# Test Note\n\nContent."

    def test_format_content_title_only(self):
        """Test formatting content that is only a title."""
        content = "# My Title"
        formatted = markdown_service.format_content(content)
        assert formatted == "# My Title\n\n"

    def test_format_content_no_title(self):
        """Test formatting content without a title."""
        content = "Just some content without a title."
        formatted = markdown_service.format_content(content)
        assert formatted == "Just some content without a title."

    def test_format_content_empty(self):
        """Test formatting empty content."""
        formatted = markdown_service.format_content("")
        assert formatted == ""

    def test_format_content_whitespace_only(self):
        """Test formatting whitespace-only content."""
        formatted = markdown_service.format_content("   \n  \t  \n  ")
        assert formatted == ""


class TestMarkdownServiceRemoveH1:
    """Test remove_h1 method."""

    def test_remove_h1_basic(self):
        """Test removing H1 heading from content."""
        content = "# Title\n\nBody content"
        result = markdown_service.remove_h1(content)
        assert result == "Body content"

    def test_remove_h1_without_extra_blank_lines(self):
        """Test that removeH1 doesn't leave extra blank lines."""
        content = "# Title\nBody content"
        result = markdown_service.remove_h1(content)
        assert result == "Body content"
        assert not result.startswith("\n")

    def test_remove_h1_only_title(self):
        """Test removing H1 when content is only a title."""
        content = "# Title"
        result = markdown_service.remove_h1(content)
        assert result == ""

    def test_remove_h1_no_h1_exists(self):
        """Test when no H1 exists."""
        content = "Body content\n\n## H2 heading"
        result = markdown_service.remove_h1(content)
        assert result == "Body content\n\n## H2 heading"

    def test_remove_h1_multiple_h1(self):
        """Test that only first H1 is removed."""
        content = "# First Title\n\nContent\n\n# Second Title"
        result = markdown_service.remove_h1(content)
        # Only the first H1 should be removed, second H1 should be preserved
        assert result == "Content\n\n# Second Title"

    def test_remove_h1_with_special_characters(self):
        """Test removing H1 with special characters."""
        content = "# Title @#$%\n\nBody"
        result = markdown_service.remove_h1(content)
        assert result == "Body"

    def test_remove_h1_empty_content(self):
        """Test removing H1 from empty content."""
        result = markdown_service.remove_h1("")
        assert result == ""

    def test_remove_h1_preserves_other_headings(self):
        """Test that other heading levels are preserved."""
        content = "# Title\n\n## Subtitle\n\n### Sub-subtitle\n\nContent"
        result = markdown_service.remove_h1(content)
        assert "## Subtitle" in result
        assert "### Sub-subtitle" in result
        assert "Content" in result
        assert "# Title" not in result


class TestMarkdownServiceCreateEmptyNote:
    """Test create_empty_note method."""

    def test_create_empty_note_default(self):
        """Test creating empty note with default title."""
        content = markdown_service.create_empty_note()
        assert content == "# New Note\n\n"

    def test_create_empty_note_custom_title(self):
        """Test creating empty note with custom title."""
        content = markdown_service.create_empty_note("My Custom Title")
        assert content == "# My Custom Title\n\n"

    def test_create_empty_note_empty_title(self):
        """Test creating empty note with empty title."""
        content = markdown_service.create_empty_note("")
        assert content == "# \n\n"

    def test_create_empty_note_with_spaces(self):
        """Test creating empty note with title containing spaces."""
        content = markdown_service.create_empty_note("Title With Spaces")
        assert content == "# Title With Spaces\n\n"

    def test_create_empty_note_with_special_chars(self):
        """Test creating empty note with special characters in title."""
        content = markdown_service.create_empty_note("Title @#$%^&*()")
        assert content == "# Title @#$%^&*()\n\n"

    def test_create_empty_note_unicode(self):
        """Test creating empty note with Unicode title."""
        content = markdown_service.create_empty_note("标题 🚀")
        assert content == "# 标题 🚀\n\n"

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
        """Test create_empty_note with various titles."""
        content = markdown_service.create_empty_note(title)
        assert content == expected


class TestMarkdownServiceIntegration:
    """Test integration between MarkdownService methods."""

    def test_extract_and_format_cycle(self):
        """Test extracting title and formatting content cycle."""
        original_content = "# Original Title\n\nSome content."

        title = markdown_service.extract_title(original_content)
        assert title == "Original Title"

        formatted = markdown_service.format_content(original_content)
        assert formatted == original_content

        title_again = markdown_service.extract_title(formatted)
        assert title_again == title

    def test_create_empty_then_extract_title(self):
        """Test creating empty note then extracting its title."""
        title = "Test Note"
        content = markdown_service.create_empty_note(title)
        extracted_title = markdown_service.extract_title(content)

        assert extracted_title == title

    def test_remove_h1_then_extract_title(self):
        """Test removing H1 then extracting title."""
        content = "# Title\n\n## Subtitle\n\nBody"
        without_h1 = markdown_service.remove_h1(content)
        title = markdown_service.extract_title(without_h1)

        assert title == "Untitled Note"
        assert "## Subtitle" in without_h1

    def test_round_trip_processing(self):
        """Test round-trip content processing maintains consistency."""
        original = "# Test Note\n\nOriginal content here."

        content = original
        for _ in range(3):
            title = markdown_service.extract_title(content)
            content = markdown_service.format_content(content)
            assert markdown_service.extract_title(content) == title

        assert content == original


class TestMarkdownServiceClass:
    """Test MarkdownService class instantiation."""

    def test_create_instance(self):
        """Test creating new instances of MarkdownService."""
        service = MarkdownService()
        assert service.extract_title("# Test") == "Test"

    def test_singleton_instance(self):
        """Test that singleton instance works correctly."""
        assert isinstance(markdown_service, MarkdownService)

    def test_multiple_instances_independent(self):
        """Test that multiple instances work independently."""
        service1 = MarkdownService()
        service2 = MarkdownService()

        result1 = service1.extract_title("# Title 1")
        result2 = service2.extract_title("# Title 2")

        assert result1 == "Title 1"
        assert result2 == "Title 2"
