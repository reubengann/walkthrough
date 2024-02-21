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

    checklist_items: dict[str, list[ChecklistItem]] = {}
    all_checklist_items: list[tuple[str, dict[str, list[ChecklistItem]]]] = []
    store_lines = []
    title_tag.string = doc.title
    h1_tag = html.new_tag("h1")
    h1_tag.string = doc.title
    h1_tag.attrs["class"] = "my-2 text-3xl font-bold tracking-tight sm:text-4xl"
    main_container.append(h1_tag)
    dark_mode_control_div = BeautifulSoup(
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
    main_container.append(dark_mode_control_div)
    for csec in doc.checklist_sections:
        for section_item in csec.items:
            match section_item:
                case SectionHeading():
                    h2_tag = html.new_tag("h2")
                    h2_tag.attrs["class"] = "mt-8 text-2xl font-bold tracking-tight"
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
        section_header = html.new_tag(
            "h3",
            attrs={"class": "text-base font-semibold leading-6 mb-2 mt-6 text-xl"},
        )
        section_header.append("Checklist")
        main_container.append(section_header)
        checklist_container = make_checklist_container(doc, html, checklist_items)
        main_container.append(checklist_container)
        all_checklist_items.append((csec.name, dict(checklist_items)))
        checklist_items.clear()
    all_checklist_h2 = html.new_tag(
        "h2", attrs={"class": "mt-8 text-2xl font-bold tracking-tight"}
    )
    all_checklist_h2.string = "All collectibles by section"
    main_container.append(all_checklist_h2)

    for checklist_item_section_name, foo_checklist_items in all_checklist_items:
        if len(foo_checklist_items.keys()) == 0:
            continue
        section_header = html.new_tag(
            "h3",
            attrs={"class": "text-base font-semibold leading-6 mb-2 mt-6 text-xl"},
        )
        section_header.append(checklist_item_section_name)
        main_container.append(section_header)
        checklist_container = make_checklist_container(doc, html, foo_checklist_items)
        main_container.append(checklist_container)
    all_checklist_h2 = html.new_tag(
        "h2", attrs={"class": "mt-8 text-2xl font-bold tracking-tight"}
    )
    all_checklist_h2.string = "All collectibles by type"
    main_container.append(all_checklist_h2)

    all_collectibles_by_type = get_collectibles_by_type(all_checklist_items)
    for item_type, items_of_that_type in all_collectibles_by_type.items():
        main_container.append(
            make_rollup_checklist_container(
                html, doc.decl_map[item_type].plural, items_of_that_type
            )
        )

    store_script = html.new_tag("script")
    store_script_text = """tailwind.config = {
        darkMode: "class"
      };\n"""
    store_script_text += f'const currentVersion = "{doc.version}";'
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
    }"""
    store_script.append(store_script_text)
    head_tag.append(store_script)

    return str(html).replace("val =&gt; localStorage", "val => localStorage")


def get_collectibles_by_type(
    all_checklist_items: list[tuple[str, dict[str, list[ChecklistItem]]]]
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
):
    checklist_container = html.new_tag("div")
    checklist_ul = html.new_tag("ul")
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
            item_li.append(make_checklist_tag(html, ci.content, ci.item_id))
            section_ul.append(item_li)
        section_ol.append(section_ul)
        checklist_ul.append(section_ol)
    checklist_container.append(checklist_ul)
    return checklist_container


def make_rollup_checklist_container(
    html: BeautifulSoup,
    item_name_plural: str,
    checklist_items: list[tuple[str, ChecklistItem]],
):
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
    section_ol.append(section_header)
    section_ul = html.new_tag("ul")

    for prefix, ci in checklist_items:
        item_li = html.new_tag("li")
        item_li.append(make_checklist_tag(html, f"{prefix}: {ci.content}", ci.item_id))
        section_ul.append(item_li)
    section_ol.append(section_ul)
    checklist_ul.append(section_ol)
    checklist_container.append(checklist_ul)
    return checklist_container


def create_tag_with_content(html: BeautifulSoup, tagname: str, content: str):
    tag = html.new_tag(tagname)
    tag.string = content
    return tag


def make_checklist_tag(html: BeautifulSoup, s: str, this_id: str) -> Tag:
    container = html.new_tag("div", attrs={"class": "relative flex items-start"})
    input_container = html.new_tag("div", attrs={"class": "flex h-6 items-center"})
    input_tag = html.new_tag(
        "input",
        attrs={
            "id": this_id,
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


def make_collapsible(html: BeautifulSoup, content: Tag):
    container_div = html.new_tag("div", attrs={"x-data": "{ open: false }"})
    button = html.new_tag(
        "button",
        attrs={
            "type": "button",
            "class": "flex w-full items-start justify-between text-left",
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
    content_div = html.new_tag("div", attrs={"x-show": "open"})
    content_div.append(content)
    container_div.append(content_div)
    return container_div
