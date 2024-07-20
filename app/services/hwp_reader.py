import olefile

def read_hwp(filepath: str):
    with olefile.OleFileIO(filepath) as f:
        encoded_text = f.openstream('BodyText/Section0').read()
    return encoded_text.decode('utf-16')
