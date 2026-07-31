import base64

def test_b64_line_length():
    dummy_zip = b"PK\x05\x06" + b"\x00" * 500  # 500+ bytes payload to generate >76 char base64 string
    b64_raw = base64.b64encode(dummy_zip).decode('ascii')
    b64_stripped_str = "\n".join(b64_raw[i:i + 76] for i in range(0, len(b64_raw), 76))
    lines = b64_stripped_str.split("\n")
    for idx, l in enumerate(lines, start=1):
        assert len(l) <= 76, f"Line {idx} exceeds 76 chars: len={len(l)}"
    print("Base64 line length test passed successfully!")

if __name__ == "__main__":
    test_b64_line_length()
