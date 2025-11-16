OBT_TYPE_STRING = 0

OBJ_ENCODING_RAW = 0
OBJ_ENCODING_INT = 1
OBJ_ENCODING_EMBSTR = 8


def getObjTypeEncoding(value):
    if type(value) == int:
        return OBT_TYPE_STRING, OBJ_ENCODING_INT
    elif type(value) == str and len(value) <= 44:
        return OBT_TYPE_STRING, OBJ_ENCODING_EMBSTR 
    else:
        return OBT_TYPE_STRING, OBJ_ENCODING_RAW


def getEncoding(typeEncoding):
    return typeEncoding & 0b00001111

def getType(typeEncoding):
    return typeEncoding >> 4


def assertEncoding(typeEncoding, expectedEncoding):
    if getEncoding(typeEncoding) != expectedEncoding:
        return False
    return True

def assertType(typeEncoding, expectedType):
    if getType(typeEncoding) != expectedType:
        return False
    return True