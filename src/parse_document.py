from dataclasses import dataclass
from enum import Enum
import re


class ParagraphChildType(Enum):
    NONE = 0
    TEXT = 1
    CHECK_ITEM = 2
    IMAGE = 3
    LINK = 4
    UNNUMBEREDLIST = 5


class ParagraphChild:
    part_type: ParagraphChildType


class TextParagraphChild(ParagraphChild):
    def __init__(self, s: str) -> None:
        self.s = s
        self.part_type = ParagraphChildType.TEXT

    def __repr__(self) -> str:
        return f"Text ({self.s})"


class ImageParagraphChild(ParagraphChild):
    def __init__(self, image_loc: str) -> None:
        self.part_type = ParagraphChildType.IMAGE
        self.image_loc = image_loc


class UlParagraphChild(ParagraphChild):
    def __init__(self, items: list[str]) -> None:
        self.part_type = ParagraphChildType.UNNUMBEREDLIST
        self.items = items


class ChecklistParagraphChild(ParagraphChild):
    def __init__(self, content: str, list_content: str, tag_name: str, item_id) -> None:
        self.content = content
        self.list_content = list_content
        self.tag_name = tag_name
        self.part_type = ParagraphChildType.CHECK_ITEM
        self.item_id = item_id

    def __repr__(self) -> str:
        return f"Checklist ({self.content})"


class LinkParagraphChild(ParagraphChild):
    def __init__(self, url: str) -> None:
        self.url = url
        self.part_type = ParagraphChildType.LINK


class DocumentItemType(Enum):
    SECTIONHEADING = 1
    PARAGRAPH = 2
    UNNUMBEREDLIST = 3
    SPOILER = 4
    NUMBEREDLIST = 5


class DocumentItem:
    item_type: DocumentItemType


class SectionHeading(DocumentItem):

    short_name: str | None

    def __init__(self, title: str, short_name: str | None) -> None:
        self.title = title
        self.short_name = None
        self.item_type = DocumentItemType.SECTIONHEADING
        self.short_name = short_name

    def __repr__(self) -> str:
        return f"Section Header (title = {self.title})"


class Paragraph(DocumentItem):
    items: list[ParagraphChild]

    def __init__(self) -> None:
        self.item_type = DocumentItemType.PARAGRAPH
        self.items = []

    def __repr__(self) -> str:
        return f"Paragraph (content = {self.items})"


class UnnumberedList(DocumentItem):
    items: list[str]

    def __init__(self) -> None:
        self.items = []
        self.item_type = DocumentItemType.UNNUMBEREDLIST

    def __repr__(self) -> str:
        return f"Unnumbered list: [{', '.join(self.items)}]"


class NumberedList(DocumentItem):
    items: list[str]

    def __init__(self) -> None:
        self.items = []
        self.item_type = DocumentItemType.NUMBEREDLIST

    def __repr__(self) -> str:
        return f"Numbered list: [{', '.join(self.items)}]"


class Spoiler(DocumentItem):
    items: list[ParagraphChild]

    def __init__(self) -> None:
        self.items = []
        self.item_type = DocumentItemType.SPOILER

    def __repr__(self) -> str:
        return f"Spoiler: [{', '.join(str(i) for i in self.items)}]"


class ChecklistSection:
    items: list[DocumentItem]
    name: str

    def __init__(self) -> None:
        self.items = []
        self.name = "Unnamed section"

    def append_line_item(self, item: DocumentItem):
        self.items.append(item)


class WalkthroughDocument:
    def __init__(self) -> None:
        self.version = "1"
        self.title = "no title"
        self.checklist_sections = [ChecklistSection()]
        self.decl_map: dict[str, Declaration] = {}
        self.images: list[str] = []
        self.game_short_name = "untitled"
        self.default_spoiler_title: str = "Click to show solution"

    def start_new_checklist_section(self):
        self.checklist_sections.append(ChecklistSection())


@dataclass
class Declaration:
    name: str
    title_name: str
    plural: str


class WalkthroughParser:

    lines: list[str]

    def __init__(self, doc: str) -> None:
        self.input_text = doc
        self.line_no = 0
        self.checklist_counters: dict[str, int] = {}
        self.current_section_name = "No section"
        self.images: list[str] = []

    def parse(self) -> WalkthroughDocument:
        doc = WalkthroughDocument()
        self.lines = self.input_text.split("\n")
        while self.line_no < len(self.lines):
            line = self.lines[self.line_no]
            self.line_no += 1
            if line.strip() == "":  # skip blank lines
                continue
            if line.startswith(R"\game_short_name"):
                game_short_name = read_between_braces(line)
                if game_short_name is None:
                    print(f"Invalid game_short_name on line {self.line_no}")
                else:
                    doc.game_short_name = game_short_name
                continue
            if line.startswith(R"\version"):
                version = read_between_braces(line)
                if version is None:
                    print(f"Invalid version on line {self.line_no}")
                else:
                    doc.version = version
                continue
            if line.startswith(R"\title"):
                title = read_between_braces(line)
                if title is None:
                    print(f"Invalid title on line {self.line_no}")
                else:
                    doc.title = title
                continue
            if line.startswith(R"\defaultspoilertitle"):
                default_spoiler_title = read_between_braces(line)
                if default_spoiler_title is None:
                    print(f"Invalid default spoiler title on line {self.line_no}")
                else:
                    doc.default_spoiler_title = default_spoiler_title
                continue
            if line.startswith(R"\section"):
                section_title = read_between_braces(line)
                foo = line.split("}")
                section_short_name = None
                if foo[1] != "":
                    section_short_name = read_between_braces(foo[1] + "}")
                if section_title is None:
                    print(f"Invalid section on line {self.line_no}")
                else:
                    item = SectionHeading(section_title, section_short_name)
                    self.current_section_name = section_short_name or section_title
                    doc.checklist_sections[-1].append_line_item(item)
                continue
            if line.startswith(R"\declare"):
                decl = self.parse_declaration(line)
                if decl is not None:
                    doc.decl_map[decl.name] = decl
                continue
            if line.startswith(R"\checklist"):
                doc.checklist_sections[-1].name = self.current_section_name
                doc.start_new_checklist_section()
                continue
            if line.startswith(R"\begin{ul}"):
                ul = self.read_ul()
                doc.checklist_sections[-1].append_line_item(ul)
                continue
            if line.startswith(R"\begin{ol}"):
                ul = self.read_ol()
                doc.checklist_sections[-1].append_line_item(ul)
                continue
            if line.startswith(R"\begin{spoiler}"):
                spoiler = self.read_spoiler()
                if spoiler is not None:
                    doc.checklist_sections[-1].append_line_item(spoiler)
                continue
            # parse a normal line item
            p = self.parse_line(line, doc.decl_map)
            if p is not None:
                doc.checklist_sections[-1].append_line_item(p)
        doc.images = self.images
        return doc

    def read_spoiler(self) -> Spoiler | None:
        item = Spoiler()
        line = self.lines[self.line_no]
        started = self.line_no
        while not line.startswith(R"\end{spoiler}"):
            if line.startswith("\\begin{ul}"):
                self.line_no += 1
                ul = self.read_ul()
                item.items.append(UlParagraphChild(ul.items))
            elif R"\img" in line:
                image_loc = read_between_braces(line)
                if image_loc is None:
                    print(f"On line {self.line_no}, could not parse img tag")
                else:
                    item.items.append(ImageParagraphChild(image_loc))
                    self.images.append(image_loc)
            elif line.strip() != "":
                item.items.append(TextParagraphChild(line))
            self.line_no += 1
            if self.line_no == len(self.lines):
                print(
                    f"Error: Spoiler started on line {started} has no terminating \\end{{spoiler}}"
                )
                return None
            line = self.lines[self.line_no]
        self.line_no += 1  # skip past the ending tag
        return item

    def read_ul(self) -> UnnumberedList:
        item = UnnumberedList()
        line = self.lines[self.line_no]
        while not line.startswith(R"\end{ul}"):
            if line.strip() == "":
                self.line_no += 1
                line = self.lines[self.line_no]
                continue
            if not line.strip().startswith(R"\item"):
                print(f"Warning: on line {self.line_no}, while parsing ul, no item")
            else:
                item.items.append(line.split(R"\item")[1])
            self.line_no += 1
            line = self.lines[self.line_no]
        self.line_no += 1  # skip past the ending tag
        return item

    def read_ol(self) -> NumberedList:
        item = NumberedList()
        line = self.lines[self.line_no]
        while not line.startswith(R"\end{ol}"):
            if line.strip() == "":
                self.line_no += 1
                line = self.lines[self.line_no]
                continue
            if not line.strip().startswith(R"\item"):
                print(f"Warning: on line {self.line_no}, while parsing ol, no item")
            else:
                item.items.append(line.split(R"\item")[1])
            self.line_no += 1
            line = self.lines[self.line_no]
        self.line_no += 1  # skip past the ending tag
        return item

    def parse_declaration(self, line: str) -> Declaration | None:
        parts = []
        remainder = line
        for _ in range(3):
            if "{" not in remainder:
                print(f"Malformed declaration on line {self.line_no}")
                return None
            _, remainder = remainder.split("{", 1)
            if "}" not in remainder:
                print(f"Malformed declaration on line {self.line_no}")
                return None
            name, remainder = remainder.split("}", 1)
            parts.append(name)
        return Declaration(*parts)

    def parse_line(
        self, line: str, decl_map: dict[str, Declaration]
    ) -> Paragraph | None:
        ret = Paragraph()
        line = line.strip()
        remainder = line

        while next_token := get_next_token(remainder):
            if next_token == "[":
                part, remainder = remainder.split("[", maxsplit=1)
                ret.items.append(TextParagraphChild(part.strip()))
                if "]" not in remainder:
                    print(f"Unclosed checklist item on line {self.line_no}")
                    return None
                part, remainder = remainder.split("]", maxsplit=1)
                lp = self.parse_checklist_item(part)
                if lp is None:
                    return None
                if lp.tag_name not in decl_map:
                    print(f"Unknown tag type {lp.tag_name} on line {self.line_no}")
                    return None
                if remainder.startswith("."):
                    lp.content += "."
                    remainder = remainder[1:]
                ret.items.append(lp)
            else:
                part, remainder = remainder.split(R"\link", maxsplit=1)
                ret.items.append(TextParagraphChild(part.strip()))
                url = read_between_braces(remainder)
                if url is None:
                    print(f"Could not parse link on line {self.line_no}")
                    break
                else:
                    _, remainder = remainder.split("}", maxsplit=1)
                    ret.items.append(LinkParagraphChild(url))
        remainder = remainder.strip()
        if remainder != "":
            ret.items.append(TextParagraphChild(remainder.strip()))
        return ret

    def parse_checklist_item(self, s: str) -> ChecklistParagraphChild | None:
        if "|" not in s:
            print(f"Invalid collectible {s} on line {self.line_no}")
            return None
        tag_name, content = s.split("|", 1)
        tag_name = tag_name.strip()
        content = content.strip()
        list_content = None
        if "|" in content:
            content, list_content = content.split("|", 1)
        else:
            list_content = content
        count = self.checklist_counters.setdefault(tag_name, 0) + 1
        this_id = f"{tag_name}{count}"
        self.checklist_counters[tag_name] += 1
        return ChecklistParagraphChild(content, list_content, tag_name, this_id)


def get_next_token(s: str) -> str | None:
    if "[" in s:
        bracket_loc = s.index("[")
        if R"\link" in s:
            link_loc = s.index(R"\link")
            return "[" if bracket_loc < link_loc else R"\link"
        return "["
    if R"\link" in s:
        return R"\link"
    return None


def read_between_braces(line: str) -> str | None:
    pattern = r"\{(.+?)\}"
    matches = re.findall(pattern, line)
    if matches:
        return matches[0]
    return None


smart_to_ascii = {
    "’": "'",
    "‘": "'",
    "“": '"',
    "”": '"',
    "–": "-",  # en dash
    "—": "-",  # em dash
    "…": "...",
    " ": " ",  # non-breaking space
}


def normalize_text(text: str) -> str:
    for smart, ascii_equiv in smart_to_ascii.items():
        text = text.replace(smart, ascii_equiv)
    return text


def parse_document(input_text: str) -> WalkthroughDocument:
    p = WalkthroughParser(normalize_text(input_text))
    doc = p.parse()
    # print(doc.version)
    # print(doc.title)
    # i = 0
    # for check_sec in doc.checklist_sections:
    #     i += 1
    #     print(f"---checklist section {i}---")
    #     for x in check_sec.items:
    #         print(x)
    return doc
