from app.models.short_url import generate_code


def test_generate_code_default_length():
    code = generate_code()
    assert len(code) == 6


def test_generate_code_custom_length():
    code = generate_code(10)
    assert len(code) == 10


def test_generate_code_is_alphanumeric():
    code = generate_code()
    assert code.isalnum()


def test_generate_code_returns_string():
    code = generate_code()
    assert isinstance(code, str)