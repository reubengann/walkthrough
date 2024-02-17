from dataclasses import dataclass


class WalkthroughDocument:
    pass


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
    def __init__(self, doc: str) -> None:
        self.doc = doc
        self.line_no = 0

    def parse(self) -> WalkthroughDocument:
        doc = self.doc
        lines = doc.split("\n")
        decl_map: dict[str, Declaration] = {}
        checklist_counters: dict[str, int] = {}
        checklist_items: dict[str, list[ChecklistItem]] = {}
        store_lines = []
        reading_ul = False
        ul_element = None
        reading_spoiler = False
        spoiler_element = None
        version = "1"
        return WalkthroughDocument()


def parse_document(doc: str):
    p = WalkthroughParser(doc)
    p.parse()
