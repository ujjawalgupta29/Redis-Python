class ValueObject:
    value = None
    expiresAt = -1

    def __init__(self, value, expiresAt):
        self.value = value
        self.expiresAt = expiresAt