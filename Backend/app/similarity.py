"""Code similarity that survives renaming, reformatting and reordering.

Plain text diffing (difflib on the raw source) is easy to fool: renaming
variables or changing whitespace and comments drops the score sharply even
though the code is the same. Here both submissions are first reduced to a
normalised token stream, then compared in two ways:

1. Token sequence similarity: difflib on the normalised tokens. Catches
   copied code with renamed identifiers, changed literals and comments.
2. Winnowing fingerprints (Schleimer et al., 2003, the algorithm behind
   MOSS): hashes of overlapping token k-grams, of which only the minimum in
   each sliding window is kept. Catches copied code whose functions or
   blocks have been reordered.

The reported score is the higher of the two.
"""

import difflib
import re
import zlib

KEYWORDS = {
    "python": {
        "False", "None", "True", "and", "as", "assert", "async", "await",
        "break", "class", "continue", "def", "del", "elif", "else", "except",
        "finally", "for", "from", "global", "if", "import", "in", "is",
        "lambda", "nonlocal", "not", "or", "pass", "raise", "return", "try",
        "while", "with", "yield", "print", "len", "range",
    },
    "javascript": {
        "break", "case", "catch", "class", "const", "continue", "default",
        "delete", "do", "else", "export", "extends", "false", "finally",
        "for", "function", "if", "import", "in", "instanceof", "let", "new",
        "null", "return", "super", "switch", "this", "throw", "true", "try",
        "typeof", "undefined", "var", "void", "while", "yield", "async",
        "await", "of", "console", "log",
    },
}

_COMMENTS = {
    "python": re.compile(r"#[^\n]*"),
    "javascript": re.compile(r"//[^\n]*|/\*.*?\*/", re.DOTALL),
}

_TOKEN = re.compile(
    r"""
    (?P<string>"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|`(?:\\.|[^`\\])*`)
  | (?P<number>\b\d+(?:\.\d+)?\b)
  | (?P<name>[A-Za-z_$][A-Za-z0-9_$]*)
  | (?P<op>==+|!=+|<=|>=|=>|\*\*|//|&&|\|\||[-+*/%<>=!&|^~?:.,;()\[\]{}])
    """,
    re.VERBOSE,
)

K_GRAM = 5
WINDOW = 4


def normalize_tokens(code: str, language: str) -> list[str]:
    """Turn source code into a token list where identifiers, strings and
    numbers are replaced by placeholders and comments are dropped."""
    language = language.strip().lower()
    keywords = KEYWORDS.get(language, set())
    comment_re = _COMMENTS.get(language)

    # Python docstrings are strings that act like comments; strip them first.
    if language == "python":
        code = re.sub(r'("""|\'\'\')(?:.|\n)*?\1', "", code)

    tokens = []
    pos = 0
    while pos < len(code):
        if comment_re:
            comment = comment_re.match(code, pos)
            if comment:
                pos = comment.end()
                continue
        match = _TOKEN.match(code, pos)
        if not match:
            pos += 1  # whitespace or a character we don't care about
            continue
        kind = match.lastgroup
        text = match.group()
        if kind == "string":
            tokens.append("STR")
        elif kind == "number":
            tokens.append("NUM")
        elif kind == "name":
            tokens.append(text if text in keywords else "ID")
        else:
            tokens.append(text)
        pos = match.end()
    return tokens


def fingerprints(tokens: list[str], k: int = K_GRAM, window: int = WINDOW) -> set[int]:
    """Winnowing: hash every k-gram, keep the minimum hash of each window."""
    if len(tokens) < k:
        return set()
    hashes = [
        zlib.crc32(" ".join(tokens[i:i + k]).encode())
        for i in range(len(tokens) - k + 1)
    ]
    if len(hashes) <= window:
        return {min(hashes)}
    return {min(hashes[i:i + window]) for i in range(len(hashes) - window + 1)}


def compare(code_a: str, code_b: str, language: str) -> dict:
    """Return similarity percentages (0-100) between two pieces of code."""
    tokens_a = normalize_tokens(code_a, language)
    tokens_b = normalize_tokens(code_b, language)

    token_ratio = difflib.SequenceMatcher(None, tokens_a, tokens_b, autojunk=False).ratio()

    fp_a, fp_b = fingerprints(tokens_a), fingerprints(tokens_b)
    if fp_a and fp_b:
        fingerprint_ratio = len(fp_a & fp_b) / len(fp_a | fp_b)
    else:
        fingerprint_ratio = token_ratio  # too short for k-grams

    return {
        "token_similarity": round(token_ratio * 100, 2),
        "fingerprint_similarity": round(fingerprint_ratio * 100, 2),
        "score": round(max(token_ratio, fingerprint_ratio) * 100, 2),
    }
