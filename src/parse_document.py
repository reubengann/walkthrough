from dataclasses import dataclass
import re


class DocumentItem:
    pass


class LineItem:
    pass


class SectionHeadingItem(LineItem):
    def __init__(self, title: str) -> None:
        self.title = title

    def __repr__(self) -> str:
        return f"Section Header (title = {self.title})"


class RegularLineItem(LineItem):
    items: list[DocumentItem]

    def __init__(self) -> None:
        self.items = []


class ULLineItem(LineItem):
    items: list[str]

    def __init__(self) -> None:
        self.items = []

    def __repr__(self) -> str:
        return f"Unnumbered list: [{', '.join(self.items)}]"


class SpoilerLineItem(LineItem):
    items: list[str]

    def __init__(self) -> None:
        self.items = []

    def __repr__(self) -> str:
        return f"Unnumbered list: [{', '.join(self.items)}]"


class ChecklistSection:
    items: list[RegularLineItem]

    def __init__(self) -> None:
        self.items = []

    def append(self, item):
        self.items.append(item)


class WalkthroughDocument:
    def __init__(self) -> None:
        self.version = "1"
        self.title = "no title"
        self.checklist_sections = [ChecklistSection()]

    def start_new_checklist_section(self):
        self.checklist_sections.append(ChecklistSection())


@dataclass
class Declaration:
    name: str
    title_name: str
    plural: str


@dataclass
class ChecklistItem:
    content: str
    item_id: str


class WalkthroughParser:

    lines: list[str]

    def __init__(self, doc: str) -> None:
        self.input_text = doc
        self.line_no = 0

    def parse(self) -> WalkthroughDocument:
        doc = WalkthroughDocument()
        self.lines = self.input_text.split("\n")
        decl_map: dict[str, Declaration] = {}
        checklist_counters: dict[str, int] = {}
        checklist_items: dict[str, list[ChecklistItem]] = {}
        store_lines = []
        reading_ul = False
        ul_element = None
        reading_spoiler = False
        spoiler_element = None
        while self.line_no < len(self.lines):
            line = self.lines[self.line_no]
            self.line_no += 1
            if line.strip() == "":  # skip blank lines
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
            if line.startswith(R"\section"):
                section_title = read_between_braces(line)
                if section_title is None:
                    print(f"Invalid section on line {self.line_no}")
                else:
                    item = SectionHeadingItem(section_title)
                    doc.checklist_sections[-1].append(item)
                continue
            if line.startswith(R"\declare"):
                decl = self.parse_declaration(line)
                if decl is not None:
                    decl_map[decl.name] = decl
                continue
            if line.startswith(R"\checklist"):
                doc.start_new_checklist_section()
                continue
            if line.startswith(R"\begin{ul}"):
                ul = self.read_ul()
                doc.checklist_sections[-1].append(ul)
                continue
            if line.startswith(R"\begin{spoiler}"):
                spoiler = self.read_spoiler()
                if spoiler is not None:
                    doc.checklist_sections[-1].append(spoiler)
                continue
        return doc

    def read_spoiler(self) -> SpoilerLineItem | None:
        item = SpoilerLineItem()
        line = self.lines[self.line_no]
        started = self.line_no
        while not line.startswith(R"\end{spoiler}"):
            if line.strip() != "":
                item.items.append(line)
            self.line_no += 1
            if self.line_no == len(self.lines):
                print(
                    f"Error: Spoiler started on line {started} has no terminating \\end{{spoiler}}"
                )
                return None
            line = self.lines[self.line_no]
        return item

    def read_ul(self) -> ULLineItem:
        item = ULLineItem()
        line = self.lines[self.line_no]
        while not line.startswith(R"\end{ul}"):
            if not line.strip().startswith(R"\item"):
                print(f"Warning: on line {self.line_no}, while parsing ul, no item")
            else:
                item.items.append(line.split(R"\item")[1])
            self.line_no += 1
            line = self.lines[self.line_no]
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


def read_between_braces(line: str) -> str | None:
    pattern = r"\{(.+?)\}"
    matches = re.findall(pattern, line)
    if matches:
        return matches[0]
    return None


def parse_document(input_text: str):
    p = WalkthroughParser(input_text)
    doc = p.parse()
    print(doc.version)
    print(doc.title)
    i = 0
    for check_sec in doc.checklist_sections:
        i += 1
        print(f"---checklist section {i}---")
        for x in check_sec.items:
            print(x)
