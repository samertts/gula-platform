
def mask_national_id(nid):

    if len(nid)<8:

        return nid

    return nid[:4]+"********"+nid[-4:]

