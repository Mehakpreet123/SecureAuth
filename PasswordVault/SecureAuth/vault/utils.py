import random, string

def generate_password(length=16, upper=True, digits=True, special=True):
    if length < 4:
        raise ValueError("Length too short")
    chars = list(string.ascii_lowercase)
    if upper:   chars += list(string.ascii_uppercase)
    if digits:  chars += list(string.digits)
    if special: chars += list("!@#$%^&*()-_=+[]{};:,<.>/?")
    return "".join(random.SystemRandom().choice(chars) for _ in range(length))
