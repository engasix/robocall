# Honorifics/prefixes common in Pakistani names that are NOT the actual calling name
PAKISTANI_HONORIFICS = {
    # Variants of Muhammad
    "muhammad", "mohammad", "mohammed", "muhammed",
    "muhamad", "mohamad", "mahammad", "mehmed",

    # Syed / Sayyid lineage titles
    "syed", "sayyid", "sayyed", "seyed", "syeda",

    # Abdul / compound God-servant prefixes
    "abdul", "abdur", "abdu", "abdus", "abdal",
    "ghulam",

    # Religious scholarly titles
    "hafiz", "hafez",
    "haji", "hajji", "haj",
    "sheikh", "shaikh", "shiekh", "shaykh",
    "maulana", "maulvi", "molvi", "mullah", "mulla",
    "qazi", "qari", "qadi",
    "pir", "imam", "allama", "allamah",
    "mufti", "maulvi",

    # Clan / tribal / feudal titles
    "chaudhry", "chaudhary", "chaudry", "choudhry", "choudhary",
    "malik",
    "mian", "miyan",
    "rana",
    "raja",
    "khan",
    "sardar",
    "nawab",
    "mir",
    "agha", "aqa",
    "baig", "beg", "baig",
    "khawaja", "khwaja", "khaja", "khvaja",
    "mirza",
    "wali",
    "nawabzada",
    "lala",
    "seth",
    "subedar",
    "jemadar",
}


def extract_first_name(full_name: str) -> str:
    """
    Extract the actual calling name from a full name.

    Examples:
        "Mohammad Asif"       → "Asif"
        "Syed Farish Hussain" → "Farish"
        "Abdul Rahman Khan"   → "Rahman"
        "Hafiz Ahmad"         → "Ahmad"
        "Sara Khan"           → "Sara"
        "Ali"                 → "Ali"
    """
    full_name = full_name.strip()
    if not full_name:
        return full_name

    parts = full_name.split()

    # Walk through name parts and return the first one that is not an honorific
    for part in parts:
        if part.lower() not in PAKISTANI_HONORIFICS:
            return part.strip()

    # Fallback: if every part is an honorific (unlikely), return the last part
    return parts[-1]
