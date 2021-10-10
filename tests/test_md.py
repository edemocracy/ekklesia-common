from ekklesia_common.md import convert

def test_convert():
    markdown = "# Heading"
    html = convert(markdown)
    assert "<h1>Heading</h1>" in html
