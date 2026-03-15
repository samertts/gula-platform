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


def hash_national_id(national_id: str) -> str:
    """Hash a national ID for secure storage."""
    cleaned = re.sub(r"[^\d]", "", national_id)
    return hashlib.sha256(cleaned.encode()).hexdigest()
