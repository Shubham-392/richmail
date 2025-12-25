def extractComments(header_value: str) -> tuple[list, str]:
    """
    Extract all comments from an RFC 2045 header field value.
    Returns a list of comment strings (without the parentheses).
    and version as per Client
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


def extractMediaTypes(header_value: str):
    """
    Extract media type, subtype, and attributes from Content-Type header.
    Returns: (Type, SubType, list_of_attributes)
    Each attribute is a dict with 'name' and 'value' keys.
    """
    rawType = []
    rawSubType = []
    i = 0

    # Extract type (before '/')
    while i < len(header_value):
        if header_value[i] == "/":
            i += 1
            break
        rawType.append(header_value[i])
        i += 1

    # Extract subtype (before ';' or end of string)
    while i < len(header_value):
        if header_value[i] == ";":
            # Found attributes - extract all of them
            attributeString = header_value[i+1:]

            Type = "".join(rawType).strip()
            SubType = "".join(rawSubType).strip()

            attributes = extractAttributes(attributeString)

            return Type, SubType, attributes

        rawSubType.append(header_value[i])
        i += 1

    # No attributes found
    Type = "".join(rawType).strip()
    SubType = "".join(rawSubType).strip()
    return Type, SubType, []


def extractAttributes(attributeString: str) -> list:
    """
    Extract all attributes from a parameter string.
    Attributes are separated by semicolons.
    Returns a list of dicts, each with 'name' and 'value' keys.
    """
    attributes = []

    # Split by semicolons to get individual attributes
    parts = attributeString.split(';')

    for part in parts:
        part = part.strip()
        if not part:
            continue

        # Split by '=' to separate name and value
        if '=' not in part:
            continue

        name, value = part.split('=', 1)
        name = name.strip()
        value = value.strip()

        # Remove quotes if present
        if value.startswith('"') and value.endswith('"'):
            value = value[1:-1]
        if name and value:
            attributes.append({
                'name': name,
                'value': value
            })

    return attributes


def extractAttribute(attributeClaim: str) -> tuple[bool, str, str]:
    """
    DEPRECATED: Use extractAttributes() instead for multiple attributes.

    Extract attribute `name` and `value` from parameter string.
    Returns: (CORRUPTED, variable, value)
    """
    cleanAttributeClaim = attributeClaim.strip()
    CORRUPTED = False
    rawVariable = []
    rawValue = []
    index = 0

    # Extract variable name (before '=')
    while index < len(cleanAttributeClaim):
        char = cleanAttributeClaim[index]

        if char == "=":
            index += 1
            break
        elif char == " ":
            # Space found before '=' - this is invalid
            CORRUPTED = True
            return CORRUPTED, "", ""
        else:
            rawVariable.append(char)
            index += 1

    # If we didn't find '=', it's corrupted
    if index >= len(cleanAttributeClaim):
        return True, "", ""

    # Extract value (after '=')
    for idx in range(index, len(cleanAttributeClaim)):
        char = cleanAttributeClaim[idx]
        if char == '"':
            # Skip quote characters
            continue
        elif char == " " and not rawValue:
            # Skip leading spaces after '='
            continue
        else:
            rawValue.append(char)

    variable = ''.join(rawVariable)
    value = ''.join(rawValue)

    return CORRUPTED, variable, value


def getBoundary(MIMEInfo: dict):
    for key in MIMEInfo['headers']['top']['Content-Type'].keys():
        if key == 'attributes':
            attributes = MIMEInfo['headers']['top']['Content-Type']['attributes']
            break
        else:
            return None

    if attributes :
        for attribute in attributes:
            if attribute['name'].lower() == 'boundary':
                return attribute['value']
            else:
                return None  # no boundary defined on top level treat it as plain text
    else:
        return None


def setBoundary():
    ...
