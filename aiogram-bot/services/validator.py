import re

def is_valid_phone(phone: str) -> bool:
    pattern = r'^(\+7|8)\d{10}$'
    return bool(re.match(pattern, phone))
