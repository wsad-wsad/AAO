"""
async name matching with high accuracy.

Strategies applied:
  1. Pre-processing  — strip titles/suffixes, normalize hyphens/punctuation/accents
  2. Nickname lookup — Robert↔Bob, William↔Bill, Elizabeth↔Liz, etc.
  3. Best token pair — greedy best-pairing across all token combinations
  4. Token sort JW   — Jaro-Winkler on sorted tokens (handles name reversal)
  5. Token overlap   — Jaccard similarity
  6. Nickname overlap— counts nickname equivalences as overlaps
  7. Soundex phonetic— homophones / phonetic misspellings

Public API:
    match_names(n1, n2)          → MatchResult  (full score breakdown)
    is_same_person(n1, n2)       → bool         (True/False match)
    find_matches(query, list)    → List[MatchResult]  (1-to-many search)
    batch_match(pairs)           → List[MatchResult]  (many pairs)

Quick examples:

    # Boolean: are these the same person?
    same = asyncio.run(is_same_person("J Smith", "John Smith"))
    print(same)  # True

    # 1-to-many: find matching names in a list
    matches = asyncio.run(find_matches("John Smith", ["J. Smith", "Jane Doe", "Jon Smith"]))
    for m in matches:
        print(m.name2, m.score)
"""

import asyncio
import re
import unicodedata
from dataclasses import dataclass
from typing import List, Tuple, Optional


# ---------------------------------------------------------------------------
# Nickname / alias dictionary
# Each tuple = all equivalent forms of one name
# ---------------------------------------------------------------------------

_NICKNAME_GROUPS: List[Tuple[str, ...]] = [
    ("robert", "rob", "bob", "bobby", "robbie", "bert"),
    ("william", "will", "bill", "billy", "willy", "liam"),
    ("james", "jim", "jimmy", "jamie"),
    ("john", "jon", "johnny", "jonathan", "johnathan", "jack"),
    ("richard", "rick", "rich", "richie", "dick"),
    ("charles", "charlie", "chuck", "chas"),
    ("thomas", "tom", "tommy"),
    ("michael", "mike", "mikey", "mick", "mickey"),
    ("david", "dave", "davey"),
    ("joseph", "joe", "joey"),
    ("edward", "ed", "eddie", "ted", "teddy", "ned"),
    ("george", "georgie"),
    ("henry", "harry", "hank"),
    ("andrew", "andy", "drew"),
    ("christopher", "chris", "kris"),
    ("anthony", "tony", "ant"),
    ("stephen", "steve", "steven", "steph"),
    ("kenneth", "ken", "kenny"),
    ("donald", "don", "donnie"),
    ("daniel", "dan", "danny"),
    ("matthew", "matt", "matty"),
    ("nicholas", "nick", "nicky", "nicolas"),
    ("samuel", "sam", "sammy"),
    ("benjamin", "ben", "benny", "benji"),
    ("patrick", "pat", "patty", "paddy"),
    ("timothy", "tim", "timmy"),
    ("raymond", "ray"),
    ("lawrence", "larry", "laurence"),
    ("gerald", "gerry", "jerry"),
    ("harold", "harry", "hal"),
    ("walter", "walt", "wally"),
    ("frank", "francis", "frankie"),
    ("peter", "pete"),
    ("gregory", "greg"),
    ("jeffrey", "jeff"),
    ("albert", "al", "bert"),
    ("alexander", "alex", "al", "alec", "sandy"),
    ("frederick", "fred", "freddie", "freddy"),
    ("leonard", "len", "lenny"),
    ("arthur", "art"),
    ("vincent", "vince"),
    ("eugene", "gene"),
    ("ernest", "ernie"),
    ("nathaniel", "nathan", "nat"),
    ("theodore", "theo", "ted"),
    ("barbara", "barb", "barbie"),
    ("elizabeth", "liz", "beth", "betty", "bette", "eliza", "lisa", "ellie", "libby"),
    ("margaret", "maggie", "meg", "peggy", "peg", "marge", "rita"),
    ("patricia", "pat", "patty", "tricia", "trish"),
    ("catherine", "cathy", "kate", "katie", "kay", "katherine", "kathryn"),
    ("jennifer", "jen", "jenny"),
    ("dorothy", "dot", "dottie"),
    ("helen", "nell", "nellie"),
    ("mary", "mae", "molly", "polly"),
    ("carol", "carole", "caroline", "carrie"),
    ("virginia", "ginny", "ginger"),
    ("deborah", "debra", "deb", "debbie"),
    ("sharon", "sherry"),
    ("linda", "lin", "lindy"),
    ("susan", "sue", "suzy", "susie"),
    ("jessica", "jess", "jessie"),
    ("sarah", "sara", "sally"),
    ("nancy", "nan"),
    ("sandra", "sandy"),
    ("kimberly", "kim"),
    ("stephanie", "steph"),
    ("angela", "angie"),
    ("melissa", "mel", "missy"),
    ("amanda", "mandy"),
    ("anna", "anne", "ann", "annie"),
    ("rebecca", "becca", "becky"),
    ("evelyn", "evie"),
    ("abigail", "abby", "gail"),
    ("charlotte", "charlie", "lottie"),
    ("eleanor", "ellie", "nell", "nora"),
    ("josephine", "jo", "josie"),
    ("jacqueline", "jackie"),
    ("diane", "di", "diana"),
]

# Flat lookup: token → frozenset of all equivalents (including itself)
_NICKNAME_MAP: dict = {}
for _group in _NICKNAME_GROUPS:
    _fs = frozenset(_group)
    for _n in _group:
        _NICKNAME_MAP[_n] = _NICKNAME_MAP.get(_n, frozenset()) | _fs


# ---------------------------------------------------------------------------
# Titles and suffixes to strip before comparison
# ---------------------------------------------------------------------------

_TITLES = {
    "dr", "mr", "mrs", "ms", "miss", "prof", "professor",
    "sir", "rev", "reverend", "capt", "captain", "lt", "col",
    "sgt", "cpl", "pvt", "gen", "admiral", "judge", "hon",
}

_SUFFIXES = {
    "jr", "sr", "ii", "iii", "iv", "v", "esq", "phd", "md",
    "dds", "dvm", "ret", "snr",
}


# ---------------------------------------------------------------------------
# Text normalisation helpers
# ---------------------------------------------------------------------------

def _normalize(name: str) -> str:
    """Strip accents, replace hyphens with space, remove non-alpha."""
    name = unicodedata.normalize("NFD", name)
    name = "".join(c for c in name if unicodedata.category(c) != "Mn")
    name = name.replace("-", " ")
    return re.sub(r"[^a-z\s]", "", name.lower()).strip()


def _clean(name: str) -> str:
    """Normalize + strip titles/suffixes."""
    tokens = _normalize(name).split()
    if tokens and tokens[0] in _TITLES:
        tokens = tokens[1:]
    if tokens and tokens[-1] in _SUFFIXES:
        tokens = tokens[:-1]
    return " ".join(tokens)


def _tokens(name: str) -> list:
    return _clean(name).split()


def _tokenset(name: str) -> set:
    return set(_tokens(name))


# ---------------------------------------------------------------------------
# Soundex
# ---------------------------------------------------------------------------

def _soundex(word: str) -> str:
    word = re.sub(r"[^a-z]", "", word.lower())
    if not word:
        return "0000"
    _codes = {"bfpv": "1", "cgjkqsxyz": "2", "dt": "3", "l": "4", "mn": "5", "r": "6"}

    def _c(ch):
        return next((v for k, v in _codes.items() if ch in k), "0")

    result = [word[0].upper()]
    prev = _c(word[0])
    for ch in word[1:]:
        c = _c(ch)
        if c != "0" and c != prev:
            result.append(c)
        prev = c
        if len(result) == 4:
            break
    return "".join(result).ljust(4, "0")


# ---------------------------------------------------------------------------
# Jaro-Winkler (on raw strings, caller normalises if needed)
# ---------------------------------------------------------------------------

def _jaro_winkler(s1: str, s2: str) -> float:
    if s1 == s2:
        return 1.0
    l1, l2 = len(s1), len(s2)
    if not l1 or not l2:
        return 0.0

    md = max(l1, l2) // 2 - 1
    m1 = [False] * l1
    m2 = [False] * l2
    matches = trans = 0

    for i in range(l1):
        lo, hi = max(0, i - md), min(i + md + 1, l2)
        for j in range(lo, hi):
            if m2[j] or s1[i] != s2[j]:
                continue
            m1[i] = m2[j] = True
            matches += 1
            break

    if not matches:
        return 0.0

    k = 0
    for i in range(l1):
        if not m1[i]:
            continue
        while not m2[k]:
            k += 1
        if s1[i] != s2[k]:
            trans += 1
        k += 1

    jaro = (matches / l1 + matches / l2 + (matches - trans / 2) / matches) / 3
    prefix = sum(s1[i] == s2[i] for i in range(min(4, l1, l2)))
    return jaro + prefix * 0.1 * (1 - jaro)


# ---------------------------------------------------------------------------
# Token-level similarity (JW + nickname + initial)
# ---------------------------------------------------------------------------

def _token_sim(t1: str, t2: str) -> float:
    """Best similarity between two individual tokens."""
    if t1 == t2:
        return 1.0

    # Nickname match
    g1 = _NICKNAME_MAP.get(t1)
    if g1 and t2 in g1:
        return 1.0
    g2 = _NICKNAME_MAP.get(t2)
    if g2 and t1 in g2:
        return 1.0

    # Initial match  (e.g. "j" vs "john")
    if len(t1) == 1 and t2.startswith(t1):
        return 0.92
    if len(t2) == 1 and t1.startswith(t2):
        return 0.92

    # Jaro-Winkler
    return _jaro_winkler(t1, t2)


# ---------------------------------------------------------------------------
# Best token pair score
# ---------------------------------------------------------------------------

def _best_token_pair(name1: str, name2: str) -> float:
    """
    For every token in the shorter name find its best match in the longer.
    Returns a length-normalised score with a small penalty for extra tokens.
    """
    t1, t2 = _tokens(name1), _tokens(name2)
    if not t1 or not t2:
        return 0.0

    short, long_ = (t1, t2) if len(t1) <= len(t2) else (t2, t1)
    used = set()
    total = 0.0

    for tok in short:
        best_score, best_idx = 0.0, -1
        for i, u in enumerate(long_):
            if i in used:
                continue
            s = _token_sim(tok, u)
            if s > best_score:
                best_score, best_idx = s, i
        if best_idx >= 0:
            used.add(best_idx)
        total += best_score

    # Slight penalty for unmatched tokens in the longer name
    extra = len(long_) - len(short)
    penalty = extra * 0.05
    return max(0.0, total / len(long_) - penalty)


# ---------------------------------------------------------------------------
# Token-sort Jaro-Winkler (handles name reversal: "Smith, John" vs "John Smith")
# ---------------------------------------------------------------------------

def _token_sort_jw(name1: str, name2: str) -> float:
    s1 = " ".join(sorted(_tokens(name1)))
    s2 = " ".join(sorted(_tokens(name2)))
    return _jaro_winkler(s1, s2)


# ---------------------------------------------------------------------------
# Jaccard token overlap
# ---------------------------------------------------------------------------

def _token_overlap(name1: str, name2: str) -> float:
    s1, s2 = _tokenset(name1), _tokenset(name2)
    union = s1 | s2
    return len(s1 & s2) / len(union) if union else 0.0


# ---------------------------------------------------------------------------
# Nickname-aware overlap
# ---------------------------------------------------------------------------

def _nickname_overlap(name1: str, name2: str) -> float:
    t1, t2 = _tokens(name1), _tokens(name2)
    if not t1 or not t2:
        return 0.0
    m1, m2 = set(), set()
    for i, a in enumerate(t1):
        for j, b in enumerate(t2):
            if j not in m2 and _token_sim(a, b) >= 0.99:
                m1.add(i)
                m2.add(j)
    matched = len(m1)
    union = len(t1) + len(t2) - matched
    return matched / union if union else 0.0


# ---------------------------------------------------------------------------
# Phonetic bonus
# ---------------------------------------------------------------------------

def _phonetic_bonus(name1: str, name2: str) -> bool:
    w1, w2 = _tokens(name1), _tokens(name2)
    return any(
        _soundex(a) == _soundex(b) and _soundex(a) != "0000"
        for a in w1 for b in w2
    )


# ---------------------------------------------------------------------------
# Label
# ---------------------------------------------------------------------------

def _label(score: float) -> str:
    if score >= 0.92:
        return "strong match"
    if score >= 0.78:
        return "likely match"
    if score >= 0.60:
        return "weak match"
    return "no match"


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------

@dataclass
class MatchResult:
    name1: str
    name2: str
    score: float
    label: str
    # component scores (for debugging / explainability)
    best_token_pair: float
    token_sort_jw: float
    token_overlap: float
    nickname_overlap: float
    phonetic_bonus: bool

    def __str__(self) -> str:
        ph = " 🔊" if self.phonetic_bonus else ""
        return (
            f"{self.name1!r:30} vs {self.name2!r:30}"
            f" → {self.label:14} (score={self.score:.4f}){ph}"
        )

    def to_dict(self) -> dict:
        return {
            "name1": self.name1,
            "name2": self.name2,
            "score": self.score,
            "label": self.label,
            "components": {
                "best_token_pair": self.best_token_pair,
                "token_sort_jw": self.token_sort_jw,
                "token_overlap": self.token_overlap,
                "nickname_overlap": self.nickname_overlap,
                "phonetic_bonus": self.phonetic_bonus,
            },
        }


# ---------------------------------------------------------------------------
# Sync computation (runs in executor so it never blocks the event loop)
# ---------------------------------------------------------------------------

def _compute(name1: str, name2: str) -> MatchResult:
    # Fast exact-match path (after cleaning)
    c1, c2 = _clean(name1), _clean(name2)
    if c1 == c2:
        return MatchResult(name1, name2, 1.0, "strong match", 1.0, 1.0, 1.0, 1.0, True)

    btp  = _best_token_pair(name1, name2)
    tsj  = _token_sort_jw(name1, name2)
    tov  = _token_overlap(name1, name2)
    nick = _nickname_overlap(name1, name2)
    phon = _phonetic_bonus(name1, name2)

    # Weighted composite
    # best_token_pair captures typos, initials, nicknames at token level
    # token_sort_jw captures full-string similarity after reordering
    score = btp * 0.50 + tsj * 0.25 + tov * 0.10 + nick * 0.15
    if phon:
        score = min(1.0, score + 0.03)

    # Boost: if both btp and tsj are very high (cross-word typos like Michel Jordon)
    # this handles cases where token_overlap is 0 but both strings are very similar
    if btp >= 0.90 and tsj >= 0.90:
        score = min(1.0, score + 0.08)

    # Boost: all-initials or mixed-initials cases
    # e.g. "R. J. Smith" vs "Robert James Smith"  /  "John A. Smith" vs "John Smith"
    t1_toks, t2_toks = _tokens(name1), _tokens(name2)
    short_toks = t1_toks if len(t1_toks) <= len(t2_toks) else t2_toks
    long_toks  = t2_toks if len(t1_toks) <= len(t2_toks) else t1_toks

    # Count how many short-side tokens are initials that match a long-side token start
    initial_hits = sum(
        1 for t in short_toks
        if len(t) == 1 and any(u.startswith(t) for u in long_toks)
    )
    if short_toks and initial_hits > 0:
        # The more initials that match, the bigger the boost
        init_ratio = initial_hits / len(short_toks)
        score = min(1.0, score + 0.14 * init_ratio)

    return MatchResult(
        name1=name1,
        name2=name2,
        score=round(score, 4),
        label=_label(score),
        best_token_pair=round(btp, 4),
        token_sort_jw=round(tsj, 4),
        token_overlap=round(tov, 4),
        nickname_overlap=round(nick, 4),
        phonetic_bonus=phon,
    )


# ---------------------------------------------------------------------------
# Public async API
# ---------------------------------------------------------------------------

async def match_names(name1: str, name2: str) -> MatchResult:
    """
    Low-level: compare two names, return a MatchResult with score + breakdown.
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _compute, name1, name2)


async def is_same_person(
    name1: str,
    name2: str,
    threshold: float = 0.78,
) -> bool:
    """
    Compare two names → True if they likely refer to the same person.

    Args:
        name1, name2: Name strings to compare.
        threshold:    Score cutoff (default 0.78). Raise to reduce false
                      positives; lower to catch more spelling variations.
    """
    result = await match_names(name1, name2)
    return result.score >= threshold


async def find_matches(
    query: str,
    candidates: List[str],
    threshold: float = 0.78,
    top_n: Optional[int] = None,
    concurrency: int = 50,
) -> List[MatchResult]:
    """
    Find all names in  that match .

    Args:
        query:       The reference name to search for.
        candidates:  List of names to compare against.
        threshold:   Minimum score to include in results (default 0.78).
        top_n:       If set, return only the top N results by score.
        concurrency: Max simultaneous comparisons (default 50).

    Returns:
        List of MatchResult sorted by score descending (best match first).
    """
    sem = asyncio.Semaphore(concurrency)

    async def _bounded(candidate: str) -> MatchResult:
        async with sem:
            return await match_names(query, candidate)

    results = await asyncio.gather(*[_bounded(c) for c in candidates])
    matched = sorted(
        [r for r in results if r.score >= threshold],
        key=lambda r: r.score,
        reverse=True,
    )
    return matched[:top_n] if top_n is not None else matched


async def batch_match(
    pairs: List[Tuple[str, str]],
    concurrency: int = 50,
) -> List[MatchResult]:
    """
    Match many name pairs concurrently.

    Example::

        pairs = [("John S", "John Smith"), ("Liz Taylor", "Elizabeth Taylor")]
        results = await batch_match(pairs)
        for r in results:
            print(r)
    """
    sem = asyncio.Semaphore(concurrency)

    async def _bounded(a: str, b: str) -> MatchResult:
        async with sem:
            return await match_names(a, b)

    return await asyncio.gather(*[_bounded(a, b) for a, b in pairs])