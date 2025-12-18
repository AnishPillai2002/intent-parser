import hashlib

def make_id(intent_id, source, text):
    raw = f"{intent_id}:{source}:{text}"
    return hashlib.md5(raw.encode()).hexdigest()