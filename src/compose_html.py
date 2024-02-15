from dataclasses import dataclass
from enum import Enum
import re
import uuid
from bs4 import BeautifulSoup, Tag


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
    actual_body_tag = html.new_tag("body")
    main_container = html.new_tag("div")
    main_container.attrs["id"] = "main_container"
    main_container.attrs["class"] = "mx-auto max-w-7xl px-6 lg:px-8"
    html_tag.append(actual_body_tag)
    actual_body_tag.append(main_container)

    # Add some content

    title_tag = html.new_tag("title")
    title_tag.string = "Sample HTML File"
    head_tag.append(title_tag)
    script = html.new_tag("script")
    script.attrs["src"] = "https://cdn.tailwindcss.com"
    head_tag.append(script)
    lines = input_contents.split("\n")
    line_no = 0
    decl_map: dict[str, Declaration] = {}
    checklist_items: dict[str, list[str]] = {}
    reading_ul = False
    ul_element = None
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
                h1_tag.attrs["class"] = (
                    "mt-2 text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl"
                )
                main_container.append(h1_tag)
        elif line.startswith(R"\section"):
            section_title = read_between_braces(line)
            if section_title is not None:
                h2_tag = html.new_tag("h2")
                h2_tag.attrs["class"] = (
                    "mt-8 text-2xl font-bold tracking-tight text-gray-900"
                )
                h2_tag.string = section_title
                main_container.append(h2_tag)
        elif line.startswith(R"\declare"):
            decl = parse_declaration(line, line_no)
            if decl is not None:
                decl_map[decl.name] = decl
        elif line.startswith(R"\checklist"):
            checklist_container = html.new_tag("div")
            checklist_ul = html.new_tag("ul")
            checklist_ul.attrs["class"] = "mt-8 space-y-8 text-gray-600"
            for tag_name in checklist_items:
                decl = decl_map[tag_name]
                section_ol = html.new_tag("li")
                section_header = html.new_tag(
                    "h3",
                    attrs={"class": "text-base font-semibold leading-6 text-gray-900"},
                )
                section_header.string = decl.plural
                section_ol.append(section_header)
                section_ul = html.new_tag("ul")

                for ci in checklist_items[tag_name]:
                    item_li = html.new_tag("li")
                    item_li.append(make_checklist_tag(html, ci))
                    section_ul.append(item_li)
                section_ol.append(section_ul)
                checklist_ul.append(section_ol)
            checklist_container.append(checklist_ul)
            main_container.append(checklist_container)
            checklist_items.clear()
        elif line.startswith(R"\begin{ul}"):
            reading_ul = True
            ul_element = html.new_tag("ul")
        elif line.startswith(R"\end{ul}"):
            reading_ul = False
            assert ul_element is not None
            main_container.append(ul_element)
            ul_element = None
        else:

            if reading_ul:
                assert ul_element is not None
                if not line.strip().startswith(R"\item"):
                    print(f"Warning: on line {line_no}, while parsing ul, no item")
                    continue
                element = ul_element
                li = html.new_tag("li")
                li.append(line.split(R"\item")[1])
                element.append(li)
            else:
                element = html.new_tag("p")
                element.attrs["class"] = "mt-4"
                for part in parse_line(line, line_no):
                    if part.part_type == PartType.TEXT:
                        element.append(part.part)
                    elif part.part_type == PartType.CHECK_ITEM:
                        if part.tag_name not in decl_map:
                            print(
                                f"Invalid collectible {part.tag_name} on line {line_no}"
                            )
                        else:
                            label_tag = html.new_tag("label")
                            checkbox_tag = html.new_tag("input", type="checkbox")
                            label_tag.string = part.part
                            element.append(checkbox_tag)
                            element.append(label_tag)
                            checklist_items.setdefault(part.tag_name, []).append(
                                part.rollup_name or part.part
                            )
                    main_container.append(element)
    return html.prettify()


class LinePart:
    part_type: PartType
    part: str
    tag_name: str | None
    rollup_name: str | None

    def __init__(
        self,
        part_type: PartType,
        part: str,
        rollup_name: str | None = None,
        tag_name: str | None = None,
    ) -> None:
        self.part_type = part_type
        self.part = part
        self.rollup_name = rollup_name
        self.tag_name = tag_name


def parse_line(line: str, line_no: int) -> list[LinePart]:
    parts: list[LinePart] = []
    line = line.strip()
    remainder = line
    while "[" in remainder:
        part, remainder = remainder.split("[", maxsplit=1)
        parts.append(LinePart(PartType.TEXT, part.strip()))
        if "]" in remainder:
            part, remainder = remainder.split("]", maxsplit=1)
            lp = parse_checklist_item(part, line_no)
            if lp is None:
                continue
            if remainder.startswith("."):
                lp.part += "."
                remainder = remainder[1:]
            parts.append(lp)
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


def parse_checklist_item(s: str, line_no: int) -> LinePart | None:
    if "|" not in s:
        print(f"Invalid collectible {s} on line {line_no}")
        return None
    tag_name, content = s.split("|", 1)
    tag_name = tag_name.strip()
    content = content.strip()
    list_content = None
    if "|" in content:
        content, list_content = content.split("|", 1)
    else:
        list_content = content

    return LinePart(PartType.CHECK_ITEM, content, list_content, tag_name)


def make_checklist_tag(html: BeautifulSoup, s: str) -> Tag:
    this_id = str(uuid.uuid4())
    container = html.new_tag("div", attrs={"class": "relative flex items-start"})
    input_container = html.new_tag("div", attrs={"class": "flex h-6 items-center"})
    input_tag = html.new_tag(
        "input",
        attrs={
            "id": this_id,
            "type": "checkbox",
            "class": "h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-600",
        },
    )
    input_container.append(input_tag)
    label_container = html.new_tag("div", attrs={"class": "ml-3 text-md leading-6"})
    label_tag = html.new_tag(
        "label", attrs={"for": this_id, "class": "font-medium text-gray-900"}
    )
    label_tag.string = s
    label_container.append(label_tag)
    container.append(input_container)
    container.append(label_container)
    return container
