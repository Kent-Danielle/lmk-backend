import re
from better_profanity import profanity as _profanity

_profanity.load_censor_words()


def sanitize(text: str, max_len: int) -> str:
    text = re.sub(r'[\r\n]+', ' ', text).strip()
    text = _profanity.censor(text)
    return text[:max_len]
