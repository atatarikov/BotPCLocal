# utils/helpers.py

import random
import string


def generate_unique_code(length=10):
    chars = string.ascii_letters + string.digits
    return "".join(random.choice(chars) for _ in range(length))
