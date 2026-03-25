def mask_national_id(nid) -> str:
    """Return a masked version of a national ID suitable for display.

    Shows first 4 and last 4 digits; everything in between is replaced with
    asterisks.  Short IDs (< 8 chars) are returned unchanged.

    Args:
        nid: The national ID value.  Accepts str, int, or None.

    Returns:
        A masked string, or an empty string if `nid` is None / empty.
    """
    if nid is None:
        return ""
    nid = str(nid).strip()
    if len(nid) < 8:
        return nid
    hidden = "*" * (len(nid) - 8)
    return nid[:4] + hidden + nid[-4:]
