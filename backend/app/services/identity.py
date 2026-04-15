"""Arabic and multilingual name normalization for patient identity matching."""
import re
import hashlib


# Arabic character normalization map
ARABIC_NORMALIZE = {
    "أ": "ا", "إ": "ا", "آ": "ا",  # Alef variants → plain Alef
    "ة": "ه",  # Ta Marbuta → Ha
    "ى": "ي",  # Alef Maksura → Ya
    "ؤ": "و",  # Waw Hamza → Waw
    "ئ": "ي",  # Ya Hamza → Ya
}

# Common Arabic diacritics to remove
ARABIC_DIACRITICS = re.compile(r"[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06DC\u06DF-\u06E4\u06E7\u06E8\u06EA-\u06ED]")

# English transliteration variants
NAME_ALIASES = {
    "mohammed": ["mohammad", "mohamed", "muhammed", "muhamad", "mohamad"],
    "ahmed": ["ahmad", "ahmet"],
    "ali": ["aly"],
    "hussein": ["husain", "husein", "hussain", "hossein"],
    "hassan": ["hasan", "hasen"],
    "abdullah": ["abdallah", "abd allah", "abdulla"],
    "abdulrahman": ["abdulrahman", "abd al-rahman", "abdalrahman"],
    "omar": ["umar", "omer"],
    "othman": ["osman", "uthman"],
    "khalid": ["khaled"],
    "karim": ["kareem"],
    "jamal": ["gamal"],
    "saleh": ["salih", "salah"],
    "youssef": ["yousef", "yusuf", "yosef", "yusef"],
    "mustafa": ["mostafa", "mustpha"],
    "ibrahim": ["ibraheem", "abraham"],
    "ismail": ["ismael", "esmail"],
}

# Build reverse lookup
_ALIAS_MAP = {}
for canonical, variants in NAME_ALIASES.items():
    _ALIAS_MAP[canonical] = canonical
    for v in variants:
        _ALIAS_MAP[v] = canonical


def normalize_arabic(text: str) -> str:
    """Normalize Arabic text for consistent matching."""
    # Remove diacritics (tashkeel)
    text = ARABIC_DIACRITICS.sub("", text)
    # Normalize character variants
    for old, new in ARABIC_NORMALIZE.items():
        text = text.replace(old, new)
    return text


def normalize_name(name: str) -> str:
    """Normalize a name (Arabic or English) for matching.

    Returns a consistent lowercase form suitable for comparison.
    """
    if not name:
        return ""

    name = name.strip()

    # Remove extra whitespace
    name = re.sub(r"\s+", " ", name)

    # Normalize Arabic characters
    name = normalize_arabic(name)

    # Lowercase for English
    name = name.lower()

    # Normalize English name variants
    parts = name.split()
    normalized_parts = []
    for part in parts:
        canonical = _ALIAS_MAP.get(part, part)
        normalized_parts.append(canonical)

    return " ".join(normalized_parts)


def match_score(p1_name: str, p1_phone: str, p1_birth: str,
                p2_name: str, p2_phone: str, p2_birth: str,
                p1_national_id_hash: str = None, p2_national_id_hash: str = None) -> float:
    """Calculate match score between two patient records.

    Returns a score from 0.0 to 1.0 indicating likelihood of same patient.
    """
    score = 0.0

    # National ID hash is the strongest signal
    if p1_national_id_hash and p2_national_id_hash:
        if p1_national_id_hash == p2_national_id_hash:
            return 1.0  # Definite match

    # Name matching (normalized)
    n1 = normalize_name(p1_name)
    n2 = normalize_name(p2_name)
    if n1 and n2:
        if n1 == n2:
            score += 0.45
        elif _name_similarity(n1, n2) > 0.8:
            score += 0.30

    # Phone matching
    if p1_phone and p2_phone:
        phone1 = re.sub(r"[^\d]", "", p1_phone)[-10:]  # last 10 digits
        phone2 = re.sub(r"[^\d]", "", p2_phone)[-10:]
        if phone1 and phone2 and phone1 == phone2:
            score += 0.35

    # Birth date matching
    if p1_birth and p2_birth:
        if str(p1_birth) == str(p2_birth):
            score += 0.20

    return min(score, 1.0)


def _name_similarity(name1: str, name2: str) -> float:
    """Simple token-based name similarity (Jaccard coefficient)."""
    tokens1 = set(name1.split())
    tokens2 = set(name2.split())
    if not tokens1 or not tokens2:
        return 0.0
    intersection = tokens1 & tokens2
    union = tokens1 | tokens2
    return len(intersection) / len(union)


def jaro_similarity(s1: str, s2: str) -> float:
    """Jaro similarity — character-level fuzzy match in [0, 1].

    Used by the MPI matcher. Robust to transpositions and small typos.
    """
    if s1 == s2:
        return 1.0
    len1, len2 = len(s1), len(s2)
    if len1 == 0 or len2 == 0:
        return 0.0

    match_distance = max(len1, len2) // 2 - 1
    if match_distance < 0:
        match_distance = 0

    s1_matches = [False] * len1
    s2_matches = [False] * len2
    matches = 0
    transpositions = 0

    for i in range(len1):
        start = max(0, i - match_distance)
        end = min(i + match_distance + 1, len2)
        for j in range(start, end):
            if s2_matches[j]:
                continue
            if s1[i] != s2[j]:
                continue
            s1_matches[i] = True
            s2_matches[j] = True
            matches += 1
            break

    if matches == 0:
        return 0.0

    k = 0
    for i in range(len1):
        if not s1_matches[i]:
            continue
        while not s2_matches[k]:
            k += 1
        if s1[i] != s2[k]:
            transpositions += 1
        k += 1

    t = transpositions / 2
    return (matches / len1 + matches / len2 + (matches - t) / matches) / 3


def jaro_winkler(s1: str, s2: str, prefix_weight: float = 0.1, max_prefix: int = 4) -> float:
    """Jaro-Winkler similarity — Jaro boosted for matching prefixes.

    Returns a score in [0, 1]. Standard Winkler defaults: p=0.1, ℓ≤4.
    Names sharing a common prefix (very common in Arabic patronymics)
    score noticeably higher.
    """
    jaro = jaro_similarity(s1, s2)
    if jaro < 0.7:  # Winkler: only apply prefix bonus for reasonably similar strings
        return jaro
    prefix_len = 0
    for a, b in zip(s1, s2):
        if a == b and prefix_len < max_prefix:
            prefix_len += 1
        else:
            break
    return jaro + prefix_len * prefix_weight * (1 - jaro)


def hash_national_id(national_id: str) -> str:
    """Hash a national ID for secure storage using HMAC-SHA256 with a stable key.

    Uses NID_HMAC_KEY (not SECRET_KEY) so hashes survive secret rotation.
    """
    import hmac
    from ..config import NID_HMAC_KEY
    cleaned = re.sub(r"[^\d]", "", national_id)
    if not cleaned:
        return ""
    return hmac.new(NID_HMAC_KEY.encode(), cleaned.encode(), hashlib.sha256).hexdigest()


def hash_family_id(family_id: str) -> str:
    """Hash a civil-registry family number for secure storage.

    Uses the same HMAC key as national IDs but prefixes the input with "fam:"
    to prevent hash collisions with national IDs that share the same digit sequence.
    """
    import hmac
    from ..config import NID_HMAC_KEY
    cleaned = re.sub(r"[^\d]", "", family_id)
    if not cleaned:
        return ""
    return hmac.new(NID_HMAC_KEY.encode(), f"fam:{cleaned}".encode(), hashlib.sha256).hexdigest()
