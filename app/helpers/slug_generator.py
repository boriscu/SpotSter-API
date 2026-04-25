import re
import unicodedata


def generate_slug(text: str) -> str:
    """
    Generates a URL-friendly slug from the given text.

    Converts to lowercase, normalizes unicode characters, removes
    non-alphanumeric characters (except hyphens), and collapses
    multiple hyphens into one.

    Args:
        text: The text to convert into a slug.

    Returns:
        str: A URL-friendly slug string.

    Examples:
        >>> generate_slug("Monster Ultra Sunrise")
        'monster-ultra-sunrise'
        >>> generate_slug("Monster Energy — Zero Sugar!")
        'monster-energy--zero-sugar'
    """
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[-\s]+", "-", text)
    text = text.strip("-")
    return text
