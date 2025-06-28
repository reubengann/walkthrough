from dataclasses import dataclass
import re
from bs4 import BeautifulSoup, Tag

from src.parse_document import (
    ChecklistParagraphChild,
    ImageParagraphChild,
    Paragraph,
    SectionHeading,
    Spoiler,
    TextParagraphChild,
    UlParagraphChild,
    UnnumberedList,
    WalkthroughDocument,
    LinkParagraphChild,
    NumberedList,
)


@dataclass
class ChecklistItem:
    content: str
    item_id: str


def generate_safe_html_tag_name(string: str) -> str:
    tag_name = string.replace(" ", "_")
    tag_name = re.sub(r"[^a-zA-Z0-9_]", "", tag_name.lower())
    return tag_name


def make_html_from_doc(doc: WalkthroughDocument) -> str:
    checklist_items: dict[str, list[ChecklistItem]] = {}
    all_checklist_items: list[tuple[str, dict[str, list[ChecklistItem]]]] = []
    store_lines = []

    html = BeautifulSoup()
    head_tag, main_container = make_preamble(html, doc.title)
    dark_mode_control_div = make_dark_mode_controls()
    main_container.append(dark_mode_control_div)
    toc_container = html.new_tag("div")
    toc_header = html.new_tag("h2", attrs={"class": "text-3xl font-bold mt-4"})
    toc_header.append("Table of Contents")
    toc_container.append(toc_header)

    toc_level_1 = html.new_tag("ul", attrs={"class": "space-y-2 ml-4"})
    walkthrough_toc_item = html.new_tag("li")
    toc_level_1.append(walkthrough_toc_item)
    walkthrough_toc_container = html.new_tag("div", attrs={"class": "mt-2"})
    walkthrough_toc_item.append(walkthrough_toc_container)
    walkthrough_toc_ul = html.new_tag("ul", attrs={"class": "space-y-2 ml-4"})
    walkthrough_toc_ul.append(html.new_tag("a", attrs={"name": "top_of_toc"}))
    walkthrough_toc_label = html.new_tag(
        "h3", attrs={"class": "ml-2 font-bold text-2xl"}
    )
    walkthrough_toc_label.append("Walkthrough")
    walkthrough_toc_container.append(walkthrough_toc_label)
    walkthrough_toc_container.append(walkthrough_toc_ul)
    toc_container.append(toc_level_1)
    main_container.append(toc_container)
    section_count = 0
    for csec in doc.checklist_sections:
        for section_item in csec.items:
            match section_item:
                case SectionHeading():
                    section_count += 1
                    section_nice_name = generate_safe_html_tag_name(section_item.title)
                    main_container.append(
                        make_section_heading(
                            html,
                            section_item.title,
                            f"section{section_count}_{section_nice_name}",
                        )
                    )
                    walkthrough_toc_ul.append(
                        make_toc_item(
                            html,
                            f"section{section_count}_{section_nice_name}",
                            section_item.title,
                        )
                    )
                case UnnumberedList():
                    ul_element = html.new_tag(
                        "ul", attrs={"class": "list-disc ml-6 mt-4"}
                    )
                    for actual_list_item in section_item.items:
                        li = html.new_tag("li", attrs={"class": "mb-2"})
                        li.append(actual_list_item)
                        ul_element.append(li)
                    main_container.append(ul_element)
                case NumberedList():
                    ol_element = html.new_tag(
                        "ol", attrs={"class": "list-decimal ml-6 mt-4"}
                    )
                    for actual_list_item in section_item.items:
                        li = html.new_tag("li", attrs={"class": "mb-2"})
                        li.append(actual_list_item)
                        ol_element.append(li)
                    main_container.append(ol_element)
                case Spoiler():
                    spoiler_element = html.new_tag("div")
                    main_container.append(
                        make_collapsible(
                            html, spoiler_element, doc.default_spoiler_title
                        )
                    )
                    for se in section_item.items:
                        match se:
                            case TextParagraphChild():
                                tag = html.new_tag("p")
                                tag.string = se.s
                                spoiler_element.append(tag)
                            case ImageParagraphChild():
                                tag = html.new_tag("img", attrs={"src": se.image_loc})
                                spoiler_element.append(tag)
                            case UlParagraphChild():
                                ul_element = html.new_tag(
                                    "ul", attrs={"class": "list-disc ml-6 mt-4"}
                                )
                                for actual_list_item in se.items:
                                    li = html.new_tag("li", attrs={"class": "mb-2"})
                                    li.append(actual_list_item)
                                    ul_element.append(li)
                                spoiler_element.append(ul_element)
                case Paragraph():
                    element = html.new_tag("p", attrs={"class": "mt-4"})
                    for paragraph_child in section_item.items:
                        element.append(" ")
                        match paragraph_child:
                            case TextParagraphChild():
                                element.append(paragraph_child.s)
                            case LinkParagraphChild():
                                a = html.new_tag(
                                    "a",
                                    attrs={
                                        "href": paragraph_child.url,
                                        "class": "hover:underline",
                                    },
                                )
                                a.append(paragraph_child.url)
                                element.append(a)
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
                                        "id": f"{paragraph_child.item_id}_in_paragraph",
                                        "x-model": paragraph_child.item_id,
                                        "class": "h-4 w-4 rounded focus:ring-indigo-600",
                                        "@change": "storeStatuses()",
                                    },
                                )
                                label_tag.string = paragraph_child.content
                                element.append(" ")
                                element.append(checkbox_tag)
                                element.append(" ")
                                element.append(label_tag)
                                element.append(" ")
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
        if checklist_items:
            section_header = html.new_tag(
                "h3",
                attrs={
                    "class": "text-base border-t pt-4 font-semibold leading-6 mb-2 mt-6 text-xl"
                },
            )
            section_header.append("Checklist")
            main_container.append(section_header)
            checklist_container = make_checklist_container(
                doc, html, checklist_items, "end_of_section"
            )
            main_container.append(checklist_container)
            all_checklist_items.append((csec.name, dict(checklist_items)))
            checklist_items.clear()

    toc_level_1.append(
        make_toc_item(
            html,
            "collectibles_by_section",
            "All collectibles by section",
            additional_class="text-2xl font-bold",
        )
    )
    main_container.append(
        make_section_heading(
            html, "All collectibles by section", "collectibles_by_section"
        )
    )

    for checklist_item_section_name, foo_checklist_items in all_checklist_items:
        if len(foo_checklist_items.keys()) == 0:
            continue
        section_header = html.new_tag(
            "h3",
            attrs={"class": "text-base font-semibold leading-6 mb-2 mt-6 text-xl"},
        )
        section_header.append(checklist_item_section_name)
        main_container.append(section_header)
        checklist_container = make_checklist_container(
            doc, html, foo_checklist_items, "by_section"
        )
        main_container.append(checklist_container)

    add_all_collectibles_by_type(
        doc, all_checklist_items, html, main_container, toc_level_1
    )

    store_script = html.new_tag("script")
    store_script_text = """tailwind.config = {
        darkMode: "class"
      };\n"""
    store_script_text += f'const currentVersion = "{doc.version}";'
    store_script_text += """
    const storedVersion = localStorage.getItem("game_short_name_checked_storage_version");
    console.log("stored version:", storedVersion);
    let shouldInitialize = false;
    if (storedVersion !== currentVersion) {
    localStorage.removeItem('game_short_name_checked_statuses');
    localStorage.setItem('game_short_name_checked_storage_version', currentVersion);
    shouldInitialize = true;
    }
    else {
    console.log("Up to date!")
    }
    let checklistItems;
    if (localStorage.getItem('game_short_name_checked_statuses') == null)
    {
    shouldInitialize = true;
    }
    if (shouldInitialize) {
    checklistItems = {
""".replace(
        "game_short_name", doc.game_short_name
    )
    store_script_text += ",\n".join(store_lines)
    store_script_text += """};
    localStorage.setItem('game_short_name_checked_statuses', JSON.stringify(checklistItems));
    console.log("Initialized storage");
    }
    else {
    checklistItems = JSON.parse(localStorage.getItem('game_short_name_checked_statuses'));
    console.log("Loaded from storage.")
    }

    function storeStatuses() {
    localStorage.setItem('game_short_name_checked_statuses', JSON.stringify(checklistItems));
    }""".replace(
        "game_short_name", doc.game_short_name
    )
    store_script.append(store_script_text)
    head_tag.append(store_script)

    return str(html).replace("val =&gt; localStorage", "val => localStorage")


def add_all_collectibles_by_type(
    doc: WalkthroughDocument,
    all_checklist_items: list[tuple[str, dict[str, list[ChecklistItem]]]],
    html: BeautifulSoup,
    main_container: Tag,
    toc_level_1: Tag,
):
    main_container.append(
        make_section_heading(
            html, "All collectibles by type", "all_collectibles_by_type"
        )
    )

    all_collectibles_by_type_li = make_toc_item(
        html,
        "all_collectibles_by_type",
        "All collectibles by type",
        additional_class="text-2xl font-bold",
    )
    all_collectibles_by_type_div = html.new_tag("div")
    all_collectibles_by_type_li.append(all_collectibles_by_type_div)
    all_collectibles_by_type_ul = html.new_tag("ul", attrs={"class": "ml-4"})
    all_collectibles_by_type_div.append(all_collectibles_by_type_ul)
    toc_level_1.append(all_collectibles_by_type_li)

    all_collectibles_by_type = get_collectibles_by_type(all_checklist_items)
    for item_type, items_of_that_type in all_collectibles_by_type.items():
        main_container.append(
            html.new_tag("a", attrs={"name": f"all_items_list_{item_type}"})
        )
        main_container.append(
            make_rollup_checklist_container(
                html, doc.decl_map[item_type].plural, items_of_that_type
            )
        )
        all_collectibles_by_type_ul_li = html.new_tag("li")
        link_to_section = html.new_tag(
            "a",
            attrs={"href": f"#all_items_list_{item_type}", "class": "hover:underline"},
        )
        link_to_section.append(doc.decl_map[item_type].plural)
        all_collectibles_by_type_ul_li.append(link_to_section)
        all_collectibles_by_type_ul.append(all_collectibles_by_type_ul_li)


def make_toc_item(
    html: BeautifulSoup,
    anchor_name: str,
    title_in_toc: str,
    additional_class: str | None = None,
) -> Tag:
    c = "hover:underline"
    if additional_class:
        c += " " + additional_class
    li = html.new_tag("li")
    a = html.new_tag("a", attrs={"href": f"#{anchor_name}", "class": c})
    a.append(title_in_toc)
    li.append(a)
    return li


def make_section_heading(html: BeautifulSoup, title: str, anchor_name: str):
    h2_tag = html.new_tag("h2")
    h2_tag.attrs["class"] = "mt-8 text-2xl font-bold tracking-tight"
    h2_tag.string = title
    h2_tag.append(html.new_tag("a", attrs={"name": anchor_name}))
    top_link = make_go_to_top_link()
    h2_tag.append(top_link)
    return h2_tag


def make_go_to_top_link(span_class: str = "text-lg font-normal") -> Tag:
    top_link = BeautifulSoup(
        ' <span><a href="#top_of_toc">(Go to top)</a></span>',
        "html.parser",
    )
    span = top_link.find("span")
    if isinstance(span, Tag):
        span["class"] = span_class

    return top_link


def make_dark_mode_controls() -> Tag:
    return BeautifulSoup(
        """
<div class="flex items-center">
    <button type="button" :class="{ 'bg-indigo-600': darkMode, 'bg-gray-200': !darkMode }" @click="darkMode = !darkMode"
    class="relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-indigo-600 focus:ring-offset-2" role="switch" aria-checked="false" aria-labelledby="annual-billing-label">
      <span aria-hidden="true" :class="{ 'translate-x-5' : darkMode, 'translate-x-0': !darkMode }" class="pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out"></span>
    </button>
    <span class="ml-3 text-sm">
      <span class="font-medium">Dark Mode</span>
    </span>
  </div>
""",
        "html.parser",
    )


def make_preamble(html: BeautifulSoup, title: str) -> tuple[Tag, Tag]:
    html_tag = html.new_tag(
        "html",
        attrs={
            "x-data": "{ darkMode: localStorage.getItem('dark') === 'true'}",
            "x-init": "$watch('darkMode', val => localStorage.setItem('dark', val))",
            "x-bind:class": "{ 'dark': darkMode }",
        },
    )
    html.append(html_tag)
    head_tag = html.new_tag("head")
    head_tag.append(html.new_tag("meta", attrs={"charset": "UTF-8"}))
    html_tag.append(head_tag)
    actual_body_tag = html.new_tag(
        "body", attrs={"class": "bg-gray-100 dark:bg-gray-600"}
    )
    main_container = html.new_tag("div", attrs={"x-data": "checklistItems"})
    main_container.attrs["id"] = "main_container"
    main_container.attrs["class"] = "mx-auto max-w-7xl px-6 lg:px-8 dark:text-white"
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

    title_tag.string = title
    h1_tag = html.new_tag("h1")
    h1_tag.string = title
    h1_tag.attrs["class"] = "my-2 text-5xl font-bold tracking-tight sm:text-5xl"
    main_container.append(h1_tag)
    return head_tag, main_container


def get_collectibles_by_type(
    all_checklist_items: list[tuple[str, dict[str, list[ChecklistItem]]]],
) -> dict[str, list[tuple[str, ChecklistItem]]]:
    all_collectibles_by_type: dict[str, list[tuple[str, ChecklistItem]]] = {}
    for checklist_item_section_name, foo_checklist_items in all_checklist_items:
        for item_type, item_list in foo_checklist_items.items():
            for item in item_list:
                all_collectibles_by_type.setdefault(item_type, []).append(
                    (checklist_item_section_name, item)
                )

    return all_collectibles_by_type


def make_checklist_container(
    doc: WalkthroughDocument,
    html: BeautifulSoup,
    checklist_items: dict[str, list[ChecklistItem]],
    loc: str,
):
    checklist_container = html.new_tag("div", attrs={"class": "border-b pb-4"})
    checklist_ul = html.new_tag("ul", attrs={"class": "ml-4"})
    checklist_ul.attrs["class"] = "mt-8 space-y-8"
    for tag_name, tags in checklist_items.items():
        decl = doc.decl_map[tag_name]
        section_ol = html.new_tag("li")
        section_header = html.new_tag(
            "h3",
            attrs={"class": "text-base font-semibold leading-6 mb-2"},
        )
        section_header.append(f"{decl.plural} (")
        section_header.append(
            html.new_tag(
                "span",
                attrs={
                    "x-text": f"[{','.join([t.item_id for t in tags])}].filter(Boolean).length"
                },
            )
        )
        section_header.append(f"/{len(tags)})")
        section_ol.append(section_header)
        section_ul = html.new_tag("ul")

        for ci in checklist_items[tag_name]:
            item_li = html.new_tag("li")
            item_li.append(make_checklist_tag(html, ci.content, ci.item_id, loc))
            section_ul.append(item_li)
        section_ol.append(section_ul)
        checklist_ul.append(section_ol)
    checklist_container.append(checklist_ul)
    return checklist_container


def make_rollup_checklist_container(
    html: BeautifulSoup,
    item_name_plural: str,
    checklist_items: list[tuple[str, ChecklistItem]],
) -> Tag:
    checklist_container = html.new_tag("div")
    checklist_ul = html.new_tag("ul", attrs={"class": "mt-8 space-y-8"})
    section_ol = html.new_tag("li")
    section_header = html.new_tag(
        "h3",
        attrs={"class": "text-base font-semibold leading-6 mb-2"},
    )
    section_header.append(f"{item_name_plural} (")
    section_header.append(
        html.new_tag(
            "span",
            attrs={
                "x-text": f"[{','.join([t[1].item_id for t in checklist_items])}].filter(Boolean).length"
            },
        )
    )
    section_header.append(f"/{len(checklist_items)})")
    section_header.append(make_go_to_top_link("text-md font-normal"))
    section_ol.append(section_header)
    section_ul = html.new_tag("ul")

    for prefix, ci in checklist_items:
        item_li = html.new_tag("li")
        item_li.append(
            make_checklist_tag(html, f"{prefix}: {ci.content}", ci.item_id, "rollup")
        )
        section_ul.append(item_li)
    section_ol.append(section_ul)
    checklist_ul.append(section_ol)
    checklist_container.append(checklist_ul)
    return checklist_container


def create_tag_with_content(html: BeautifulSoup, tagname: str, content: str):
    tag = html.new_tag(tagname)
    tag.string = content
    return tag


def make_checklist_tag(html: BeautifulSoup, s: str, this_id: str, loc: str) -> Tag:
    container = html.new_tag("div", attrs={"class": "relative flex items-start"})
    input_container = html.new_tag("div", attrs={"class": "flex h-6 items-center"})
    input_tag = html.new_tag(
        "input",
        attrs={
            "id": f"{this_id}{loc}",
            "type": "checkbox",
            "x-model": this_id,
            "class": "h-4 w-4 ml-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-600",
            "@change": "storeStatuses()",
        },
    )
    input_container.append(input_tag)
    label_container = html.new_tag("div", attrs={"class": "ml-3 text-md leading-6"})
    label_tag = html.new_tag("label", attrs={"for": this_id, "class": "font-medium"})
    label_tag.string = s
    label_container.append(label_tag)
    container.append(input_container)
    container.append(label_container)
    return container


def make_collapsible(html: BeautifulSoup, content: Tag, collapsed_text: str):
    container_div = html.new_tag("div", attrs={"x-data": "{ open: false }"})
    button = html.new_tag(
        "button",
        attrs={
            "type": "button",
            "class": "flex items-start text-left",
            "@click": "open = !open",
        },
    )
    sp = html.new_tag("span", attrs={"class": "text-base font-semibold leading-7"})
    sp.string = collapsed_text

    container_div.append(button)
    button.append(
        BeautifulSoup(
            """

<span class="flex items-center">
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
    button.append(sp)
    content_div = html.new_tag("div", attrs={"x-show": "open"})
    content_div.append(content)
    container_div.append(content_div)
    return container_div
