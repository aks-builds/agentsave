import tiktoken

_ENCODING = tiktoken.get_encoding("cl100k_base")


def count_tokens(text: object) -> int:
    if not isinstance(text, str) or not text:
        return 0
    return len(_ENCODING.encode(text))
