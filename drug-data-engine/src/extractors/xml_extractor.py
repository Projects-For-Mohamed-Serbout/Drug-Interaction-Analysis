"""
Base XML Extractor class for parsing CIMA XML files.
"""
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional, Iterator, Any
import logging

logger = logging.getLogger(__name__)


class XMLExtractor:
    """Base class for extracting data from CIMA XML files."""

    def __init__(self, file_path: Path):
        """
        Initialize the extractor with the XML file path.

        Args:
            file_path: Path to the XML file
        """
        self.file_path = file_path
        self.namespace = None
        self._tree = None
        self._root = None

    def parse(self) -> bool:
        """
        Parse the XML file.

        Returns:
            True if parsing was successful, False otherwise
        """
        try:
            logger.info(f"Parsing XML file: {self.file_path}")
            self._tree = ET.parse(self.file_path)
            self._root = self._tree.getroot()

            # Extract namespace from root element
            if self._root.tag.startswith('{'):
                self.namespace = self._root.tag.split('}')[0] + '}'
            else:
                self.namespace = ''

            logger.info(f"Successfully parsed XML file. Namespace: {self.namespace}")
            return True
        except ET.ParseError as e:
            logger.error(f"Error parsing XML file {self.file_path}: {e}")
            return False
        except FileNotFoundError:
            logger.error(f"XML file not found: {self.file_path}")
            return False

    def get_text(self, element: ET.Element, tag: str, default: Any = None) -> Optional[str]:
        """
        Get text content of a child element.

        Args:
            element: Parent element
            tag: Tag name of the child element
            default: Default value if element not found

        Returns:
            Text content or default value
        """
        child = element.find(f"{self.namespace}{tag}")
        if child is not None and child.text:
            return child.text.strip()
        return default

    def get_int(self, element: ET.Element, tag: str, default: int = None) -> Optional[int]:
        """Get integer value of a child element."""
        text = self.get_text(element, tag)
        if text is not None:
            try:
                return int(text)
            except ValueError:
                logger.warning(f"Could not convert '{text}' to int for tag '{tag}'")
        return default

    def get_float(self, element: ET.Element, tag: str, default: float = None) -> Optional[float]:
        """Get float value of a child element."""
        text = self.get_text(element, tag)
        if text is not None:
            try:
                # Handle comma as decimal separator
                text = text.replace(',', '.')
                return float(text)
            except ValueError:
                logger.warning(f"Could not convert '{text}' to float for tag '{tag}'")
        return default

    def get_bool(self, element: ET.Element, tag: str, default: bool = False) -> bool:
        """Get boolean value of a child element (0/1 or true/false)."""
        text = self.get_text(element, tag)
        if text is not None:
            return text.lower() in ('1', 'true', 'yes', 'sí', 'si')
        return default

    def find_all(self, tag: str) -> Iterator[ET.Element]:
        """
        Find all elements with the given tag.

        Args:
            tag: Tag name to search for

        Yields:
            Matching elements
        """
        if self._root is None:
            raise ValueError("XML file not parsed. Call parse() first.")

        for element in self._root.findall(f".//{self.namespace}{tag}"):
            yield element

    def count_elements(self, tag: str) -> int:
        """Count the number of elements with the given tag."""
        return len(list(self.find_all(tag)))

    @property
    def root(self) -> Optional[ET.Element]:
        """Get the root element."""
        return self._root
