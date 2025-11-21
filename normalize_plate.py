import re


def normalize_plate(text):
    if not text:
        return None


    text = re.sub(r'[^A-Za-z0-9]', '', text).upper()


    text = (text.replace('I', '1')
            .replace('O', '0')
            .replace('Z', '2')
            .replace('S', '5')
            .replace('B', '8'))


    pattern = r'([A-Z]{2})(\d{2})([A-Z]{1,2})(\d{4})'
    match = re.search(pattern, text)
    if match:
        return "".join(match.groups())


    letters = ''.join(re.findall(r'[A-Z]', text))
    digits = ''.join(re.findall(r'\d', text))


    if len(letters) >= 3 and len(digits) >= 6:

        candidates = [
            letters[:2] + digits[:2] + letters[2:4] + digits[2:],
            letters[:2] + digits[:2] + letters[2:] + digits[2:],
            digits[:2] + letters[:2] + digits[2:4] + letters[2:],  #
        ]
        for cand in candidates:
            if re.match(r'^[A-Z]{2}\d{2}[A-Z]{1,2}\d{4}$', cand):
                return cand


    return None
