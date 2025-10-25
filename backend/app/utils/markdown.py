"""
Shared markdown processing utilities
This implementation mirrors the frontend markdown service to ensure consistency
"""

import re
from typing import Protocol


class MarkdownProcessor(Protocol):
    """Protocol defining the interface for markdown processing."""

    def extract_title(self, content: str) -> str: ...
    def format_content(self, content: str) -> str: ...
    def remove_h1(self, content: str) -> str: ...


class MarkdownService:
    """
    Markdown processing service with consistent behavior across frontend/backend.
    """

    H1_REGEX = re.compile(r"^#\s+(.+)$", re.MULTILINE)
    DEFAULT_TITLE = "Untitled Note"

    def extract_title(self, content: str) -> str:
        """
        Extract title from markdown content.
        Looks for the first H1 heading (# Title).
        """
        match = self.H1_REGEX.search(content)
        return match.group(1).strip() if match else self.DEFAULT_TITLE

    def format_content(self, content: str) -> str:
        """
        Format note content to ensure proper structure.
        Ensures content has proper spacing and formatting.
        """
        cleaned = content.strip()
        title = self.extract_title(cleaned)

        return f"# {title}\n\n" if cleaned == f"# {title}" else cleaned

    def remove_h1(self, content: str) -> str:
        """
        Remove the H1 title heading from markdown content.
        Used to avoid duplicating the title in rendered content.
        """
        return self.H1_REGEX.sub("", content).strip()

    def create_empty_note(self, title: str = "New Note") -> str:
        """Create a new empty note content template."""
        return f"# {title}\n\n"


# Singleton instance for convenience
markdown_service = MarkdownService()


# Shared test cases to ensure parity with frontend
MARKDOWN_TEST_CASES = [
    {"input": "# Test\n\nContent", "expected_title": "Test"},
    {"input": "No heading", "expected_title": "Untitled Note"},
    {"input": "## Not H1\n\nContent", "expected_title": "Untitled Note"},
    {"input": "# Multiple\n\n# Headings", "expected_title": "Multiple"},
    {"input": "# Title with spaces  ", "expected_title": "Title with spaces"},
    {"input": "#NoSpace", "expected_title": "Untitled Note"},
    {"input": "", "expected_title": "Untitled Note"},
]
