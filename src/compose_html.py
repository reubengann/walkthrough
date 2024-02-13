from dataclasses import dataclass
from enum import Enum
import re
from bs4 import BeautifulSoup


class PartType(Enum):
    NONE = 0
    TEXT = 1
    CHECK_ITEM = 2


@dataclass
class Declaration:
    name: str
    title_name: str
    plural: str


def make_html_from_lines(input_contents: str) -> str:
    html = BeautifulSoup()
    html_tag = html.new_tag("html")
    html.append(html_tag)
    head_tag = html.new_tag("head")
    html_tag.append(head_tag)

    body_tag = html.new_tag("body")
    html_tag.append(body_tag)

    # Add some content

    title_tag = html.new_tag("title")
    title_tag.string = "Sample HTML File"
    head_tag.append(title_tag)
    lines = input_contents.split("\n")
    line_no = 0
    decl_map: dict[str, Declaration] = {}
    checklist_items: dict[str, list[str]] = {}
    for line in lines:
        line_no += 1
        if line.strip() == "":
            continue
        if line.startswith(R"\title"):
            title = read_between_braces(line)
            if title is not None:
                title_tag.string = title
                h1_tag = html.new_tag("h1")
                h1_tag.string = title
                body_tag.append(h1_tag)
        elif line.startswith(R"\section"):
            section_title = read_between_braces(line)
            if section_title is not None:
                h2_tag = html.new_tag("h2")
                h2_tag.string = section_title
                body_tag.append(h2_tag)
        elif line.startswith(R"\declare"):
            decl = parse_declaration(line, line_no)
            if decl is not None:
                decl_map[decl.name] = decl
        elif line.startswith(R"\checklist"):
            checklist_ul = html.new_tag("ul")
            for tag_name in checklist_items:
                decl = decl_map[tag_name]
                section_ol = html.new_tag("li")
                section_header = html.new_tag("h3")
                section_header.string = decl.plural
                section_ol.append(section_header)
                section_ul = html.new_tag("ul")

                for ci in checklist_items[tag_name]:
                    item_li = html.new_tag("li")
                    item_li.append(html.new_tag("input", type="checkbox"))
                    item_li.append(ci)
                    section_ul.append(item_li)
                section_ol.append(section_ul)
                checklist_ul.append(section_ol)
            body_tag.append(checklist_ul)
            checklist_items.clear()
        else:
            p = html.new_tag("p")
            for part in parse_line(line):
                if part.part_type == PartType.TEXT:
                    p.append(part.part)
                elif part.part_type == PartType.CHECK_ITEM:
                    if "|" not in part.part:
                        print(f"Invalid collectible {part.part} on line {line_no}")
                        label_tag = html.new_tag("label")
                        checkbox_tag = html.new_tag("input", type="checkbox")
                        label_tag.string = part.part
                        p.append(checkbox_tag)
                        p.append(label_tag)
                    else:
                        tag_name, content = part.part.split("|", 1)
                        tag_name = tag_name.strip()
                        content = content.strip()
                        list_content = None
                        if "|" in content:
                            content, list_content = content.split("|", 1)
                        if tag_name not in decl_map:
                            print(f"Invalid collectible {tag_name} on line {line_no}")
                        else:
                            label_tag = html.new_tag("label")
                            checkbox_tag = html.new_tag("input", type="checkbox")
                            label_tag.string = content
                            p.append(checkbox_tag)
                            p.append(label_tag)
                            checklist_items.setdefault(tag_name, []).append(
                                list_content or content
                            )
            body_tag.append(p)
    return html.prettify()


class LinePart:
    part_type: PartType
    part: str

    def __init__(self, part_type: PartType, part: str) -> None:
        self.part_type = part_type
        self.part = part


def parse_line(line: str) -> list[LinePart]:
    parts: list[LinePart] = []
    line = line.strip()
    remainder = line
    while "[" in remainder:
        part, remainder = remainder.split("[", maxsplit=1)
        parts.append(LinePart(PartType.TEXT, part.strip()))
        if "]" in remainder:
            part, remainder = remainder.split("]", maxsplit=1)
            parts.append(LinePart(PartType.CHECK_ITEM, part.strip()))
    parts.append(LinePart(PartType.TEXT, remainder.strip()))
    return parts


def read_between_braces(line: str) -> str | None:
    pattern = r"\{(.+?)\}"
    matches = re.findall(pattern, line)
    if matches:
        return matches[0]
    return None


def parse_declaration(line: str, line_no: int) -> Declaration | None:
    parts = []
    remainder = line
    for _ in range(3):
        if "{" not in remainder:
            print(f"Malformed declaration on line {line_no}")
            return None
        _, remainder = remainder.split("{", 1)
        if "}" not in remainder:
            print(f"Malformed declaration on line {line_no}")
            return None
        name, remainder = remainder.split("}", 1)
        parts.append(name)
    return Declaration(*parts)
