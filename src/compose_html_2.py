from dataclasses import dataclass
from bs4 import BeautifulSoup, Tag

from src.parse_document import (
    ChecklistParagraphChild,
    Paragraph,
    SectionHeading,
    Spoiler,
    TextParagraphChild,
    UnnumberedList,
    WalkthroughDocument,
)


@dataclass
class ChecklistItem:
    content: str
    item_id: str


def make_html_from_doc(doc: WalkthroughDocument) -> str:
    html = BeautifulSoup()
    html_tag = html.new_tag("html")
    html.append(html_tag)
    head_tag = html.new_tag("head")
    html_tag.append(head_tag)
    actual_body_tag = html.new_tag("body")
    main_container = html.new_tag("div", attrs={"x-data": "checklistItems"})
    main_container.attrs["id"] = "main_container"
    main_container.attrs["class"] = "mx-auto max-w-7xl px-6 lg:px-8"
    html_tag.append(actual_body_tag)
    actual_body_tag.append(main_container)

    title_tag = html.new_tag("title")
    title_tag.string = "Sample HTML File"
    head_tag.append(title_tag)
    head_tag.append(
        html.new_tag("script", attrs={"src": "https://cdn.tailwindcss.com"})
    )
    head_tag.append(
        html.new_tag(
            "script", attrs={"src": "https://unpkg.com/alpinejs", "defer": "defer"}
        )
    )

    checklist_items: dict[str, list[ChecklistItem]] = {}
    store_lines = []
    title_tag.string = doc.title
    h1_tag = html.new_tag("h1")
    h1_tag.string = doc.title
    h1_tag.attrs["class"] = (
        "mt-2 text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl"
    )
    main_container.append(h1_tag)

    for csec in doc.checklist_sections:
        for section_item in csec.items:
            match section_item:
                case SectionHeading():
                    h2_tag = html.new_tag("h2")
                    h2_tag.attrs["class"] = (
                        "mt-8 text-2xl font-bold tracking-tight text-gray-900"
                    )
                    h2_tag.string = section_item.title
                    main_container.append(h2_tag)
                case UnnumberedList():
                    ul_element = html.new_tag("ul", attrs={"class": "list-disc ml-6"})
                    for actual_list_item in section_item.items:
                        li = html.new_tag("li", attrs={"class": "mb-2"})
                        li.append(actual_list_item)
                        ul_element.append(li)
                    main_container.append(ul_element)
                case Spoiler():
                    spoiler_element = html.new_tag("div")
                    main_container.append(make_collapsible(html, spoiler_element))
                    for se in section_item.items:
                        tag = html.new_tag("p")
                        tag.string = se.s
                        spoiler_element.append(tag)
                case Paragraph():
                    element = html.new_tag("p", attrs={"class": "mt-4"})
                    for paragraph_child in section_item.items:
                        match paragraph_child:
                            case TextParagraphChild():
                                element.append(paragraph_child.s)
                            case ChecklistParagraphChild():
                                if paragraph_child.tag_name not in doc.decl_map:
                                    print(
                                        f"Invalid collectible {paragraph_child.tag_name}"
                                    )
                                    continue
                                label_tag = html.new_tag(
                                    "label", attrs={"for": paragraph_child.item_id}
                                )
                                checkbox_tag = html.new_tag(
                                    "input",
                                    type="checkbox",
                                    attrs={
                                        "id": paragraph_child.item_id,
                                        "x-model": paragraph_child.item_id,
                                        "@change": "storeStatuses()",
                                    },
                                )
                                label_tag.string = paragraph_child.content
                                element.append(checkbox_tag)
                                element.append(label_tag)
                                store_lines.append(
                                    f"'{paragraph_child.item_id}': false"
                                )
                                citem = ChecklistItem(
                                    paragraph_child.list_content,
                                    paragraph_child.item_id,
                                )
                                checklist_items.setdefault(
                                    paragraph_child.tag_name, []
                                ).append(citem)
                    main_container.append(element)
        # Append checklist
        checklist_container = html.new_tag("div")
        checklist_ul = html.new_tag("ul")
        checklist_ul.attrs["class"] = "mt-8 space-y-8 text-gray-600"
        for tag_name in checklist_items:
            decl = doc.decl_map[tag_name]
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
                item_li.append(make_checklist_tag(html, ci.content, ci.item_id))
                section_ul.append(item_li)
            section_ol.append(section_ul)
            checklist_ul.append(section_ol)
        checklist_container.append(checklist_ul)
        main_container.append(checklist_container)
        checklist_items.clear()

    store_script = html.new_tag("script")
    store_script_text = f'const currentVersion = "{doc.version}";'
    store_script_text += """
    const storedVersion = localStorage.getItem("alan_wake_2_checked_storage_version");
    console.log("stored version:", storedVersion);
    let shouldInitialize = false;
    if (storedVersion !== currentVersion) {
    localStorage.removeItem('alan_wake_2_checked_statuses');
    localStorage.setItem('alan_wake_2_checked_storage_version', currentVersion);
    shouldInitialize = true;
    }
    else {
    console.log("Up to date!")
    }
    let checklistItems;
    if (localStorage.getItem('alan_wake_2_checked_statuses') == null)
    {
    shouldInitialize = true;
    }
    if (shouldInitialize) {
    checklistItems = {
"""
    store_script_text += ",\n".join(store_lines)
    store_script_text += """};
    localStorage.setItem('alan_wake_2_checked_statuses', JSON.stringify(checklistItems));
    console.log("Initialized storage");
    }
    else {
    checklistItems = JSON.parse(localStorage.getItem('alan_wake_2_checked_statuses'));
    console.log("Loaded from storage.")
    }

    function storeStatuses() {
    localStorage.setItem('alan_wake_2_checked_statuses', JSON.stringify(checklistItems));
    console.log("saved");
    }"""
    store_script.append(store_script_text)
    head_tag.append(store_script)
    return html.prettify()


# class LinePart:
#     part_type: PartType
#     part: str
#     tag_name: str | None
#     rollup_name: str | None

#     def __init__(
#         self,
#         part_type: PartType,
#         part: str,
#         rollup_name: str | None = None,
#         tag_name: str | None = None,
#     ) -> None:
#         self.part_type = part_type
#         self.part = part
#         self.rollup_name = rollup_name
#         self.tag_name = tag_name


# def parse_line(line: str, line_no: int) -> list[LinePart]:
#     parts: list[LinePart] = []
#     line = line.strip()
#     remainder = line
#     while "[" in remainder:
#         part, remainder = remainder.split("[", maxsplit=1)
#         parts.append(LinePart(PartType.TEXT, part.strip()))
#         if "]" in remainder:
#             part, remainder = remainder.split("]", maxsplit=1)
#             lp = parse_checklist_item(part, line_no)
#             if lp is None:
#                 continue
#             if remainder.startswith("."):
#                 lp.part += "."
#                 remainder = remainder[1:]
#             parts.append(lp)
#     parts.append(LinePart(PartType.TEXT, remainder.strip()))
#     return parts


# def read_between_braces(line: str) -> str | None:
#     pattern = r"\{(.+?)\}"
#     matches = re.findall(pattern, line)
#     if matches:
#         return matches[0]
#     return None


# def parse_declaration(line: str, line_no: int) -> Declaration | None:
#     parts = []
#     remainder = line
#     for _ in range(3):
#         if "{" not in remainder:
#             print(f"Malformed declaration on line {line_no}")
#             return None
#         _, remainder = remainder.split("{", 1)
#         if "}" not in remainder:
#             print(f"Malformed declaration on line {line_no}")
#             return None
#         name, remainder = remainder.split("}", 1)
#         parts.append(name)
#     return Declaration(*parts)


# def parse_checklist_item(s: str, line_no: int) -> LinePart | None:
#     if "|" not in s:
#         print(f"Invalid collectible {s} on line {line_no}")
#         return None
#     tag_name, content = s.split("|", 1)
#     tag_name = tag_name.strip()
#     content = content.strip()
#     list_content = None
#     if "|" in content:
#         content, list_content = content.split("|", 1)
#     else:
#         list_content = content

#     return LinePart(PartType.CHECK_ITEM, content, list_content, tag_name)


def make_checklist_tag(html: BeautifulSoup, s: str, this_id: str) -> Tag:
    container = html.new_tag("div", attrs={"class": "relative flex items-start"})
    input_container = html.new_tag("div", attrs={"class": "flex h-6 items-center"})
    input_tag = html.new_tag(
        "input",
        attrs={
            "id": this_id,
            "type": "checkbox",
            "x-model": this_id,
            "class": "h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-600",
            "@change": "storeStatuses()",
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


def make_collapsible(html: BeautifulSoup, content: Tag):
    container_div = html.new_tag("div", attrs={"x-data": "{ open: false }"})
    button = html.new_tag(
        "button",
        attrs={
            "type": "button",
            "class": "flex w-full items-start justify-between text-left text-gray-900",
            "@click": "open = !open",
        },
    )
    sp = html.new_tag("span", attrs={"class": "text-base font-semibold leading-7"})
    sp.string = "Click to show solution"
    button.append(sp)
    container_div.append(button)
    button.append(
        BeautifulSoup(
            """

<span class="ml-6 flex h-7 items-center">
          <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" aria-hidden="true" x-bind:class="{ 'hidden': open }">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 6v12m6-6H6" />
          </svg>
          <svg class="hidden h-6 w-6" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" aria-hidden="true" x-bind:class="{ 'hidden': !open }">
            <path stroke-linecap="round" stroke-linejoin="round" d="M18 12H6" />
          </svg>
        </span>
""",
            "html.parser",
        )
    )
    content_div = html.new_tag(
        "div", attrs={"x-show": "open", "class": "text-gray-900"}
    )
    content_div.append(content)
    container_div.append(content_div)
    return container_div
