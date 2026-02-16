
import os
import re

# Mojibake mapping (UTF-8 bytes interpreted as Windows-1252/ISO-8859-1)
replacements = {
    "Ã³": "ó",
    "Ã¡": "á",
    "Ã©": "é",
    "Ãí": "í",  # complex case, sometimes just Ã
    "Ã": "í",   # careful with this one
    "Ãº": "ú",
    "Ã±": "ñ",
    "ÃWN": "Ñ",
    "Â": "",    # sometimes appears before non-breaking space
    "â€™": "'",
    "â€œ": '"',
    "â€": '"',
}

# Better approach: Read as binary, decode as utf-8 (if it was double encoded, it might be recoverable)
# The current file likely contains the BYTES for Ã³ (which is C3 B3) physically written as characters.
# actually, `Ã³` is C3 83 C2 B3 in UTF-8. 
# The original was `ó` (C3 B3). 
# It was read as `Ã` (C3) and `³` (B3) using ISO-8859-1, then saved as UTF-8.

def fix_encoding():
    try:
        with open("frontend/index.html", "r", encoding="utf-8") as f:
            content = f.read()

        # Extended Latin-1 to UTF-8 mojibake fixes
        fixes = [
            ("Ã³", "ó"),
            ("Ã¡", "á"),
            ("Ã©", "é"),
            ("Ãí", "í"),
            ("Ãº", "ú"),
            ("Ã±", "ñ"),
            ("Ã‘", "Ñ"),
            ("Ã¿", "¿"),
            ("Ã¡", "á"),
            ("Ã ", "à"),
            ("Ã¨", "è"),
            ("Ã¬", "ì"),
            ("Ã²", "ò"),
            ("Ã¹", "ù"),
            ("Ã¼", "ü"),
            ("Ã¶", "ö"),
            ("Ã¤", "ä"),
            ("ÃŸ", "ß"),
            ("Â¿", "¿"),
            ("Â¡", "¡"),
            # Quotation marks and special symbols
            ("â€œ", '"'),
            ("â€", '"'),
            ("â€™", "'"),
            ("â€˜", "'"),
            ("â€”", "—"),
            ("â€“", "–"),
            ("â€¦", "…"),
            ("Â©", "©"),
            ("Â®", "®"),
            ("â„¢", "™"),
            ("Â", ""), # Non-breaking space artifact often appearing as Â 
            
            # New findings from scan
            ("Â·", "·"),  # Middle dot
            ("â€¢", "•"), # Bullet point
            ("ðŸ", ""),   # Broken emoji start (often 4 bytes like ðŸ”…)
            ("”M", ""),   # Broken sequence
            ("â", ""),    # Aggressive cleanup of remaining â if not matched above
            
            # Specific word fixes based on user report
            ("aquÃ", "aquí"),
            ("aquÃ­", "aquí"), # Common C3 AD double encoded
            ("dÃa", "día"),
            ("dÃ­a", "día"),   # Common C3 AD double encoded
            ("tÃ©cnico", "técnico"),
            ("mÃ¡s", "más"),
            ("EstÃ¡", "Está"),
            ("PolÃtica", "Política"),
            ("PolÃ­tica", "Política"),
            ("anÃ¡lisis", "análisis"),
            ("tÃtulo", "título"),
        ]
        
        # Additional regex fix for accented i (í) which seems problematic
        # Ã followed by encoded hyphen/dash sometimes means í
        content = re.sub(r'Ã­', 'í', content) # Very common UTF-8 double encoding for í
        content = re.sub(r'PolÃ­tica', 'Política', content) # Direct hit if regex above misses it
        
        for bad, good in fixes:
            content = content.replace(bad, good)

        # Regex fixes for complex cases
        # Ã followed by uppercase letter -> should be that letter (e.g., ÃM -> M)
        # This is a common pattern where the second byte was lost or merged
        content = re.sub(r'Ã([A-Z])', r'\1', content)
        
        # Ã followed by encoded space or newline
        content = content.replace("Ã\n", "í\n") # heuristic
        content = content.replace("Ã ", "á ")   # heuristic

        # Write back
        with open("frontend/index.html", "w", encoding="utf-8") as f:
            f.write(content)
            
        print(f"Fixed encoding issues in frontend/index.html")

    except Exception as e:
        print(f"Error fixing file: {e}")

if __name__ == "__main__":
    fix_encoding()
