from app.similarity import compare, fingerprints, normalize_tokens

ORIGINAL = '''
def two_sum(nums, target):
    """Return indices of the two numbers that add up to target."""
    seen = {}
    for i, n in enumerate(nums):
        if target - n in seen:
            return [seen[target - n], i]
        seen[n] = i
    return []

def is_palindrome(text):
    cleaned = "".join(c.lower() for c in text if c.isalnum())
    return cleaned == cleaned[::-1]
'''

# Same logic: identifiers renamed, comments added, formatting changed,
# functions swapped.
DISGUISED = '''
def check_pal(s):
    # strip everything that is not a letter
    t = ''.join(ch.lower() for ch in s if ch.isalnum())
    return t == t[::-1]


def find_pair(arr, goal):
    lookup = {}   # value -> index
    for idx, val in enumerate(arr):
        if goal - val in lookup:
            return [lookup[goal - val], idx]
        lookup[val] = idx
    return []
'''

UNRELATED = '''
class Stack:
    def __init__(self):
        self.items = []

    def push(self, item):
        self.items.append(item)

    def pop(self):
        if not self.items:
            raise IndexError("pop from empty stack")
        return self.items.pop()
'''


def test_renaming_and_comments_do_not_change_tokens():
    a = normalize_tokens("total = price * 2  # double it", "python")
    b = normalize_tokens("x=y*7", "python")
    assert a == b == ["ID", "=", "ID", "*", "NUM"]


def test_javascript_comments_and_strings_are_normalized():
    tokens = normalize_tokens("const msg = 'hi'; /* note */ // done\nconsole.log(msg)", "javascript")
    assert tokens == ["const", "ID", "=", "STR", ";", "console", ".", "log", "(", "ID", ")"]


def test_disguised_copy_scores_high():
    result = compare(ORIGINAL, DISGUISED, "python")
    assert result["score"] >= 70
    # Reordering the functions hurts the sequence match more than the
    # fingerprints, which is why both are computed.
    assert result["fingerprint_similarity"] > result["token_similarity"]


def test_unrelated_code_scores_low():
    assert compare(ORIGINAL, UNRELATED, "python")["score"] < 50


def test_identical_code_scores_100():
    assert compare(ORIGINAL, ORIGINAL, "python")["score"] == 100


def test_raw_difflib_would_miss_the_copy():
    import difflib
    raw = difflib.SequenceMatcher(None, ORIGINAL.strip(), DISGUISED.strip()).ratio() * 100
    assert raw < 70 <= compare(ORIGINAL, DISGUISED, "python")["score"]


def test_short_code_has_no_fingerprints_but_still_compares():
    assert fingerprints(["ID", "="]) == set()
    assert compare("x = 1", "y = 2", "python")["score"] == 100
