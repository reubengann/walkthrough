from src.compose_html import parse_line


def test_parse_line():
    s = "a b c [ d e f ] g h i [j k l] m n o"
    result = parse_line(s)
    assert len(result) == 5
    assert result[0].part == "a b c"
    assert result[0].part_type == "text"
    assert result[1].part == "d e f"
    assert result[1].part_type == "check_item"
    assert result[2].part == "g h i"
    assert result[3].part == "j k l"
    assert result[4].part == "m n o"
