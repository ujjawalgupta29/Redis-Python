class ValueObject:
    def __init__(self, value, expiresAt, typeEncoding):
        self.value = value
        self.expiresAt = expiresAt
        self.typeEncoding = typeEncoding