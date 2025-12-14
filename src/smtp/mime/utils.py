
def extractComments(header_value:str):
    """
    Extract all comments from an RFC 2045 header field value.
    Returns a list of comment strings (without the parentheses).
    """
    comments = []
    rawVersion = []
    i = 0

    while i < len(header_value):
        if header_value[i] == '(':
            # Start of comment - find the matching closing parenthesis
            comment_start = i + 1
            depth = 1
            i += 1

            while i < len(header_value) and depth > 0:
                if header_value[i] == '\\':
                    # Skip escaped character
                    i += 2
                    continue
                elif header_value[i] == '(':
                    depth += 1
                elif header_value[i] == ')':
                    depth -= 1
                    if depth == 0:
                        # Found matching closing paren
                        comments.append(header_value[comment_start:i])
                i += 1
        else:
            if header_value[i] != "":
                rawVersion.append(header_value[i])
            i += 1

    version = "".join(rawVersion)
    return comments, version


def extractMediaTypes(header_value:str):
    rawType = []
    rawSubType = []
    i=0
    while i < len(header_value):
        if header_value[i] == "/":
            i += 1
            break
        rawType.append(header_value[i])
        i += 1

    while i < len(header_value):
        if header_value[i] == ";":
            break
        rawSubType.append(header_value[i])
        i += 1

    Type, SubType = "".join(rawType), "".join(rawSubType)
    return Type, SubType
