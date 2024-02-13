from src.compose_html import PartType, parse_line


def test_parse_line():
    s = "a b c [coll|d e f ] g h i [coll|j k l] m n o"
    result = parse_line(s, 1)
    assert len(result) == 5
    assert result[0].part == "a b c"
    assert result[0].part_type == PartType.TEXT
    assert result[1].part == "d e f"
    assert result[1].part_type == PartType.CHECK_ITEM
    assert result[2].part == "g h i"
    assert result[3].part == "j k l"
    assert result[4].part == "m n o"
