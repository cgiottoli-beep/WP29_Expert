"""Test filename sanitization"""
import re

def sanitize_filename(name):
    """Remove or replace characters that cause storage issues"""
    # Replace multiple spaces with single space
    name = re.sub(r'\s+', ' ', name)
    # Replace problematic characters with underscore
    name = re.sub(r'[(){}\[\]]', '_', name)
    # Remove any other non-standard characters except dash, underscore, dot, space
    name = re.sub(r'[^\w\s.-]', '', name)
    return name.strip()

# Test cases
test_filenames = [
    "LUPC-01-02-Rev.1e (Chairs) Draft Roadmap   (ToR ver.)   20240105.pdf",
    "Simple filename.pdf",
    "File with [brackets] and {braces}.pdf",
    "Multiple     spaces    everywhere.pdf",
    "Special!@#$%chars.pdf"
]

print("=" * 70)
print("FILENAME SANITIZATION TEST")
print("=" * 70)

for original in test_filenames:
    sanitized = sanitize_filename(original)
    print(f"\nOriginal:  {original}")
    print(f"Sanitized: {sanitized}")
    print(f"Storage path: TF LUPC/2024/1/{sanitized}")
