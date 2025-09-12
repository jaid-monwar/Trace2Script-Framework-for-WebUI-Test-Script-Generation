import logging
import re
from typing import Any, Awaitable, Callable, Dict, List, Optional

from playwright.async_api import ElementHandle, Page

#### Logging ####

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
formatter = logging.Formatter("SELECTOR: %(message)s")
console_handler.setFormatter(formatter)

logger.addHandler(console_handler)

#### Constants ####
TEST_ID_ATTRIBUTES: List[str] = [
    "data-testid",
    "data-test-id",
    "data-test",
    "data-cy",
    "test-id",
    "data-slot",
    "aria-haspopup",
]
FORM_TAGS: List[str] = ["input", "textarea", "select"]
MAX_TEXT_SELECTOR_LENGTH: int = 100
PARTIAL_TEXT_MIN_LENGTH: int = 20
PARTIAL_TEXT_SLICE_LENGTH: int = 20
NTH_CHILD_MAX_SIBLINGS: int = 10


# --- Dynamic Value Checkers (keep as before) ---
def _is_dynamic_value(value: str, patterns: List[str]) -> bool:
    if not value:
        return False
    return any(re.match(pattern, value, re.IGNORECASE) for pattern in patterns)


def _is_dynamic_id(id_value: str) -> bool:
    dynamic_id_patterns: List[str] = [
        r".*\d{10,}.*",
        r"[a-f0-9]{8}-[a-f0-9]{4}-",
        r"^[a-f0-9]{20,}$",
        r".*_ngcontent-.*",
        r"^ember\d+$",
        r"^react-.*",
        r"ui-id-\d+",
        r"yui_3_\d+_\d+_\d+_\d+",
    ]
    return _is_dynamic_value(id_value, dynamic_id_patterns)


def _is_dynamic_class(class_name: str) -> bool:
    dynamic_class_patterns: List[str] = [
        r".*\d{8,}.*",
        r".*[a-f0-9]{6,}.*",
        r"^css-[a-z0-9]+$",
        r".*__[a-f0-9]{5,}$",
        r".*_nghost-.*",
        r".*_ngcontent-.*",
        r"^style-\w+$",
        r"^class\d+$",
    ]
    return _is_dynamic_value(class_name, dynamic_class_patterns)


def _is_dynamic_attribute_value(attr_value: str) -> bool:
    dynamic_attr_patterns: List[str] = [
        r".*\d{10,}.*",
        r"[a-f0-9]{16,}",
        r".*uuid.*",
        r".*guid.*",
    ]
    return _is_dynamic_value(attr_value, dynamic_attr_patterns)


# --- Core Uniqueness Check ---
async def _is_selector_unique(page: Page, selector: str) -> bool:
    if not selector:
        logger.debug(f"DEBUG: (_is_selector_unique) Empty selector")
        return False
    try:
        count = await page.locator(selector).count()
        logger.debug(
            f"DEBUG: (_is_selector_unique) Selector: '{selector}', Count: {count}"
        )
        return count == 1
    except Exception as e:
        # The InvalidSelectorError for "exact=true" would be caught here.
        logger.debug(
            f"DEBUG: (_is_selector_unique) Error checking selector uniqueness for '{selector}': {e}"
        )
        return False


# --- Helper Functions for Element Properties (keep _infer_role_from_element, _get_raw_name_for_exact_role_match, _get_comprehensive_accessible_name, _get_associated_label_text as in your last provided code) ---
async def _infer_role_from_element(
    element: ElementHandle, tag_name: str
) -> Optional[str]:
    try:
        explicit_role = await element.get_attribute("role")
        if explicit_role:
            return explicit_role.lower()
        role_mapping: Dict[str, str] = {
            "a": "link",
            "button": "button",
            "select": "combobox",
            "textarea": "textbox",
            "img": "img",
            "nav": "navigation",
            "main": "main",
            "header": "banner",
            "footer": "contentinfo",
            "aside": "complementary",
            "form": "form",
            "article": "article",
            "h1": "heading",
            "h2": "heading",
            "h3": "heading",
            "h4": "heading",
            "h5": "heading",
            "h6": "heading",
            "ul": "list",
            "ol": "list",
            "li": "listitem",
            "table": "table",
            "th": "columnheader",
            "td": "cell",
            "tr": "row",
        }
        if tag_name in role_mapping:
            return role_mapping[tag_name]
        if tag_name == "input":
            input_type = (await element.get_attribute("type") or "text").lower()
            input_roles: Dict[str, str] = {
                "button": "button",
                "submit": "button",
                "reset": "button",
                "checkbox": "checkbox",
                "radio": "radio",
                "search": "searchbox",
                "email": "textbox",
                "number": "spinbutton",
                "tel": "textbox",
                "url": "textbox",
                "text": "textbox",
                "password": "textbox",
                "date": "textbox",
                "time": "textbox",
                "datetime-local": "textbox",
                "month": "textbox",
                "week": "textbox",
            }
            return input_roles.get(input_type, "textbox")
        return None
    except Exception:
        return None


async def _get_raw_name_for_exact_role_match(
    element: ElementHandle, tag_name: str
) -> Optional[str]:
    # Using the version from your last provided code, which seems reasonable.
    aria_label = await element.get_attribute("aria-label")
    if aria_label is not None:
        return aria_label.strip()  # strip() is important

    # If no aria-label, try other sources based on tag/role
    actual_role = await _infer_role_from_element(element, tag_name)

    if actual_role in ["option", "button", "link", "menuitem", "tab", "heading"]:
        text = await element.inner_text()
        if text is not None:
            return text.strip()

    if tag_name == "input":
        input_type = (await element.get_attribute("type") or "").lower()
        if input_type in ["button", "submit", "reset"]:
            value = await element.get_attribute("value")
            if value is not None:
                return value.strip()
    if tag_name == "img":
        alt = await element.get_attribute("alt")
        if alt is not None:
            return alt.strip()

    return None


async def _get_comprehensive_accessible_name(
    element: ElementHandle, tag_name: str
) -> str:
    # Using the version from your last provided code
    name_parts = []
    try:
        # 1. aria-label
        aria_label = await element.get_attribute("aria-label")
        if aria_label and aria_label.strip():
            name_parts.append(aria_label.strip())

        # 2. If no aria-label, use other means
        if not name_parts:
            text_content_source = ""
            actual_role = await _infer_role_from_element(element, tag_name)

            if actual_role in [
                "button",
                "link",
                "heading",
                "option",
                "menuitem",
                "tab",
                "listitem",
                "cell",
                "label",
            ]:
                text_content_source = await element.inner_text()
            elif tag_name == "input":
                input_type = (await element.get_attribute("type") or "").lower()
                if input_type in ["submit", "button", "reset"]:
                    text_content_source = await element.get_attribute("value") or ""
            elif tag_name == "img":
                text_content_source = await element.get_attribute("alt") or ""

            if text_content_source and text_content_source.strip():
                name_parts.append(text_content_source.strip())

        # 3. title attribute (lower priority if others haven't yielded a name)
        if not name_parts:
            title = await element.get_attribute("title")
            if title and title.strip():
                name_parts.append(title.strip())

        if name_parts:
            return " ".join(
                " ".join(part.split()).strip() for part in name_parts if part
            )  # Normalize

    except Exception:
        pass
    return ""


# --- Utility to normalise Playwright evaluate results ----------------------------------
# In some Playwright versions, element.evaluate() may still return a JSHandle when the
# function body itself returns a DOM node or other non-serialisable value.  That handle
# prints as `JSHandle@…`, which causes later string operations (or JSON serialization)
# to break.  This helper converts a possible handle into a real Python value by calling
# its .json_value() method.  If the input is already a plain value it is returned
# unchanged.


async def _ensure_serialisable(value: Any) -> Any:  # type: ignore[override]
    """Return a JSON-serialisable Python value even if *value* is a Playwright JSHandle."""
    # A JSHandle in python has the attribute `json_value`.
    if (
        value is not None
        and not isinstance(value, (str, int, float, bool, dict, list))
        and hasattr(value, "json_value")
    ):
        try:
            return await value.json_value()  # type: ignore[attr-defined]
        except Exception:
            # If conversion fails, just fall through and return the original value
            pass
    return value


# --- Helper to find textual label associated with form elements ------------------------


async def _get_associated_label_text(
    page: Page, element: ElementHandle
) -> Optional[str]:
    """Return the visible text of a <label> bound to *element* (via for="id" or as an ancestor)."""
    try:
        element_id = await element.get_attribute("id")
        if element_id:
            try:
                label_locator = page.locator(f'label[for="{element_id}"]').first
                await label_locator.wait_for(state="attached", timeout=200)
                label_text = await label_locator.text_content()
                if label_text and label_text.strip():
                    return " ".join(label_text.strip().split())
            except Exception:
                pass  # fall through to ancestor search

        # Look for a parent <label> element
        parent_label_text_raw = await element.evaluate(
            "(el) => el.closest('label') ? el.closest('label').textContent.trim() : null"
        )
        parent_label_text = await _ensure_serialisable(parent_label_text_raw)
        if parent_label_text and str(parent_label_text).strip():
            return " ".join(str(parent_label_text).strip().split())
    except Exception:
        pass
    return None


# --- Selector Strategy Functions ---
async def _try_test_id_selectors(page: Page, element: ElementHandle) -> Optional[str]:
    logger.debug(
        f"DEBUG: (_try_test_id_selectors) Checking for test IDs: {TEST_ID_ATTRIBUTES}"
    )
    for attr in TEST_ID_ATTRIBUTES:
        value = await element.get_attribute(attr)
        if value:
            logger.debug(f"DEBUG: (_try_test_id_selectors) Found {attr}='{value}'")
            selector = f'[{attr}="{value}"]'
            count = await page.locator(selector).count()
            logger.debug(
                f"DEBUG: (_try_test_id_selectors) Test ID selector: '{selector}', Count: {count}"
            )
            if count == 1:
                logger.debug(
                    f"DEBUG: (_try_test_id_selectors) Found unique test ID selector"
                )
                return selector
            else:
                logger.debug(
                    f"DEBUG: (_try_test_id_selectors) Test ID selector not unique"
                )
    logger.debug(f"DEBUG: (_try_test_id_selectors) No unique test ID found")
    return None


async def _try_role_selectors(
    page: Page, element: ElementHandle, tag_name: str
) -> Optional[str]:
    role = await _infer_role_from_element(element, tag_name)
    if not role:
        logger.debug(f"(_try_role_selectors) No role inferred for tag '{tag_name}'")
        return None

    # Attempt 1: Role with exact name match (using page.get_by_role for count)
    raw_name_for_exact = await _get_raw_name_for_exact_role_match(element, tag_name)
    # raw_name_for_exact can be an empty string if aria-label="", which is a valid exact name.
    if raw_name_for_exact is not None:  # Check for None, empty string is a valid name
        try:
            # Use page.get_by_role for the uniqueness check with exact=True
            count_exact = await page.get_by_role(
                role, name=raw_name_for_exact, exact=True
            ).count()
            logger.debug(
                f"DEBUG: (_try_role_selectors) Exact match check: role='{role}', name='{raw_name_for_exact}', exact=True, Count: {count_exact}"
            )
            if count_exact == 1:
                # If unique, return the standard role[name=""] selector string.
                # Playwright's locator will use its advanced logic for this string.
                escaped_raw_name = raw_name_for_exact.replace('"', '\\"')
                selector_to_return = f'role={role}[name="{escaped_raw_name}"]'
                logger.debug(
                    f"DEBUG: (_try_role_selectors) Unique with exact match logic. Returning: '{selector_to_return}'"
                )
                return selector_to_return
        except Exception as e:
            # This might catch errors if the role/name combination is problematic for get_by_role itself
            logger.debug(
                f"DEBUG: (_try_role_selectors) Error during get_by_role exact check: {e}"
            )
            pass  # Continue to flexible match

    # Attempt 2: Role with flexible name match (using _is_selector_unique with role=role[name="name"])
    normalized_accessible_name = await _get_comprehensive_accessible_name(
        element, tag_name
    )
    if normalized_accessible_name:  # Ensure there's a name to match
        escaped_normalized_name = normalized_accessible_name.replace('"', '\\"')
        selector_flexible_name = f'role={role}[name="{escaped_normalized_name}"]'
        logger.debug(
            f"DEBUG: (_try_role_selectors) Flexible match check: '{selector_flexible_name}'"
        )
        if await _is_selector_unique(
            page, selector_flexible_name
        ):  # This uses page.locator()
            logger.debug(f"DEBUG: (_try_role_selectors) Unique with flexible")
            return selector_flexible_name

    # Attempt 3: Role only
    selector_role_only = f"role={role}"
    logger.debug(
        f"DEBUG: (_try_role_selectors) Role only check: '{selector_role_only}'"
    )
    if await _is_selector_unique(page, selector_role_only):  # This uses page.locator()
        logger.debug(
            f"DEBUG: (_try_role_selectors) Unique with role only. Returning: '{selector_role_only}'"
        )
        return selector_role_only

    return None


# ... (other _try_... and _generate_... functions remain the same as your last provided code) ...
async def _try_form_specific_selectors(
    page: Page, element: ElementHandle, tag_name: str
) -> Optional[str]:
    if tag_name not in FORM_TAGS:
        return None
    label_text = await _get_associated_label_text(page, element)
    if label_text:
        escaped_label = label_text.replace('"', '\\"')
        label_selector = f'label="{escaped_label}"'
        if await _is_selector_unique(page, label_selector):
            return label_selector
    placeholder = await element.get_attribute("placeholder")
    if placeholder and placeholder.strip():
        clean_placeholder = " ".join(placeholder.strip().split())
        escaped_placeholder = clean_placeholder.replace('"', '\\"')
        placeholder_selector = f'[placeholder="{escaped_placeholder}"]'
        count = await page.locator(placeholder_selector).count()
        logger.debug(f"DEBUG: (_try_form_specific_selectors) Trying placeholder selector: '{placeholder_selector}', Count: {count}")
        if count == 1:
            return placeholder_selector
        
        # Try with tag name
        tag_placeholder_selector = f'{tag_name}[placeholder="{escaped_placeholder}"]'
        count = await page.locator(tag_placeholder_selector).count()
        logger.debug(f"DEBUG: (_try_form_specific_selectors) Trying tag+placeholder selector: '{tag_placeholder_selector}', Count: {count}")
        if count == 1:
            return tag_placeholder_selector
        
        # Try with type attribute if input
        if tag_name == "input":
            input_type = await element.get_attribute("type")
            if input_type:
                type_placeholder_selector = f'input[type="{input_type}"][placeholder="{escaped_placeholder}"]'
                count = await page.locator(type_placeholder_selector).count()
                logger.debug(f"DEBUG: (_try_form_specific_selectors) Trying type+placeholder selector: '{type_placeholder_selector}', Count: {count}")
                if count == 1:
                    return type_placeholder_selector
                
                # If still not unique, try with :visible
                if count > 1:
                    visible_selector = f'{type_placeholder_selector}:visible'
                    visible_count = await page.locator(visible_selector).count()
                    logger.debug(f"DEBUG: (_try_form_specific_selectors) Trying visible selector: '{visible_selector}', Count: {visible_count}")
                    if visible_count == 1:
                        return visible_selector
                    elif visible_count > 1:
                        # Return first visible
                        return f'{visible_selector} >> nth=0'
    return None


async def _try_text_content_selector(
    page: Page, element: ElementHandle
) -> Optional[str]:
    text_content = await element.text_content()
    if not text_content:
        return None
    text_content_stripped = text_content.strip()
    if (
        not text_content_stripped
        or len(text_content_stripped) > MAX_TEXT_SELECTOR_LENGTH
    ):
        return None
    clean_full_text = " ".join(text_content_stripped.split())
    escaped_full_text = clean_full_text.replace('"', '\\"')
    full_text_selector = f'text="{escaped_full_text}"'
    if await _is_selector_unique(page, full_text_selector):
        return full_text_selector
    if len(clean_full_text) > PARTIAL_TEXT_MIN_LENGTH:
        partial_text = clean_full_text[:PARTIAL_TEXT_SLICE_LENGTH].strip()
        if partial_text:
            escaped_partial_text = partial_text.replace('"', '\\"')
            partial_text_selector = f'text="{escaped_partial_text}"'
            if await _is_selector_unique(page, partial_text_selector):
                return partial_text_selector
    return None


async def _try_id_selector(page: Page, element: ElementHandle) -> Optional[str]:
    element_id = await element.get_attribute("id")
    if not element_id:
        logger.debug(f"DEBUG: (_try_id_selector) No ID attribute found")
        return None

    logger.debug(
        f"DEBUG: (_try_id_selector) Element ID: '{element_id}', IsDynamic: {_is_dynamic_id(element_id)}"
    )

    if _is_dynamic_id(element_id):
        logger.debug(f"DEBUG: (_try_id_selector) ID appears to be dynamic, skipping")
        return None

    id_selector = f"#{element_id}"
    count = await page.locator(id_selector).count()
    logger.debug(
        f"DEBUG: (_try_id_selector) ID selector: '{id_selector}', Count: {count}"
    )

    if count == 1:
        logger.debug(
            f"DEBUG: (_try_id_selector) Found unique ID selector: '{id_selector}'"
        )
        return id_selector
    else:
        logger.debug(f"DEBUG: (_try_id_selector) ID selector not unique")

    return None


async def _try_name_attribute_selector(
    page: Page, element: ElementHandle
) -> Optional[str]:
    name_attr = await element.get_attribute("name")
    if name_attr and not _is_dynamic_attribute_value(name_attr):
        selector = f'[name="{name_attr}"]'
        if await _is_selector_unique(page, selector):
            return selector
    return None


async def _try_aria_label_selector(
    page: Page, element: ElementHandle, tag_name: str
) -> Optional[str]:
    """Try to use aria-label attribute as a selector."""
    aria_label = await element.get_attribute("aria-label")
    if not aria_label:
        return None
    
    # Try aria-label alone
    selector = f'[aria-label="{aria_label}"]'
    count = await page.locator(selector).count()
    logger.debug(f"DEBUG: (_try_aria_label_selector) Trying selector: '{selector}', Count: {count}")
    
    if count == 1:
        logger.debug(f"DEBUG: (_try_aria_label_selector) Found unique aria-label selector")
        return selector
    
    # Try tag + aria-label
    tag_aria_selector = f'{tag_name}[aria-label="{aria_label}"]'
    count = await page.locator(tag_aria_selector).count()
    logger.debug(f"DEBUG: (_try_aria_label_selector) Trying selector: '{tag_aria_selector}', Count: {count}")
    
    if count == 1:
        logger.debug(f"DEBUG: (_try_aria_label_selector) Found unique tag+aria-label selector")
        return tag_aria_selector
    
    # If still not unique, try with type attribute for buttons/inputs
    if tag_name in ["button", "input"]:
        type_attr = await element.get_attribute("type")
        if type_attr:
            type_aria_selector = f'{tag_name}[type="{type_attr}"][aria-label="{aria_label}"]'
            count = await page.locator(type_aria_selector).count()
            logger.debug(f"DEBUG: (_try_aria_label_selector) Trying selector: '{type_aria_selector}', Count: {count}")
            
            if count == 1:
                logger.debug(f"DEBUG: (_try_aria_label_selector) Found unique tag+type+aria-label selector")
                return type_aria_selector
    
    # Try with parent context if still not unique
    if count > 1:
        parent_info = await element.evaluate("""
            (el) => {
                const parent = el.parentElement;
                if (!parent) return null;
                
                // Look for form parent
                const form = el.closest('form');
                if (form) {
                    return {
                        type: 'form',
                        formClass: form.className || '',
                        formId: form.id || ''
                    };
                }
                
                // Look for div parent with meaningful class
                const div = el.closest('div[class]');
                if (div) {
                    return {
                        type: 'div',
                        divClass: div.className || ''
                    };
                }
                
                return null;
            }
        """)
        
        parent_info = await _ensure_serialisable(parent_info)
        
        if parent_info:
            if parent_info.get('type') == 'form':
                # Try form context
                if parent_info.get('formClass'):
                    stable_classes = [
                        cls for cls in parent_info['formClass'].split() 
                        if not _is_dynamic_class(cls)
                    ]
                    if stable_classes:
                        form_selector = f'form.{stable_classes[0]} {tag_name}[aria-label="{aria_label}"]'
                        count = await page.locator(form_selector).count()
                        logger.debug(f"DEBUG: (_try_aria_label_selector) Trying selector: '{form_selector}', Count: {count}")
                        
                        if count == 1:
                            logger.debug(f"DEBUG: (_try_aria_label_selector) Found unique form context selector")
                            return form_selector
            
            # Try with visible pseudo-selector
            visible_selector = f'{tag_name}[aria-label="{aria_label}"]:visible'
            visible_count = await page.locator(visible_selector).count()
            logger.debug(f"DEBUG: (_try_aria_label_selector) Trying visible selector: '{visible_selector}', Count: {visible_count}")
            
            if visible_count == 1:
                logger.debug(f"DEBUG: (_try_aria_label_selector) Found unique visible selector")
                return visible_selector
            elif visible_count > 1:
                # Use nth=0 for first visible
                return f'{visible_selector} >> nth=0'
    
    return None


async def _try_value_attribute_selector(
    page: Page, element: ElementHandle, tag_name: str
) -> Optional[str]:
    """Try to use the value attribute as a selector, particularly useful for buttons with product IDs."""
    # Only try this for buttons and inputs
    if tag_name not in ["button", "input"]:
        return None
    
    value_attr = await element.get_attribute("value")
    if not value_attr:
        return None
    
    # Check if value looks like a product ID or other stable identifier
    # Product IDs are often numeric and relatively short
    if value_attr.isdigit() and 3 <= len(value_attr) <= 10:
        # Try value attribute alone first
        selector = f'[value="{value_attr}"]'
        count = await page.locator(selector).count()
        logger.debug(f"DEBUG: (_try_value_attribute_selector) Trying selector: '{selector}', Count: {count}")
        
        if count == 1:
            logger.debug(f"DEBUG: (_try_value_attribute_selector) Found unique value selector")
            return selector
        
        # If not unique by value alone, combine with tag
        tag_value_selector = f'{tag_name}[value="{value_attr}"]'
        count = await page.locator(tag_value_selector).count()
        logger.debug(f"DEBUG: (_try_value_attribute_selector) Trying selector: '{tag_value_selector}', Count: {count}")
        
        if count == 1:
            logger.debug(f"DEBUG: (_try_value_attribute_selector) Found unique tag+value selector")
            return tag_value_selector
        
        # If still not unique, try combining with name attribute if present
        name_attr = await element.get_attribute("name")
        if name_attr:
            combined_selector = f'{tag_name}[name="{name_attr}"][value="{value_attr}"]'
            count = await page.locator(combined_selector).count()
            logger.debug(f"DEBUG: (_try_value_attribute_selector) Trying selector: '{combined_selector}', Count: {count}")
            
            if count == 1:
                logger.debug(f"DEBUG: (_try_value_attribute_selector) Found unique tag+name+value selector")
                return combined_selector
            
            # If still multiple, try with :visible pseudo-selector
            if count > 1:
                visible_selector = f'{combined_selector}:visible'
                visible_count = await page.locator(visible_selector).count()
                logger.debug(f"DEBUG: (_try_value_attribute_selector) Trying visible selector: '{visible_selector}', Count: {visible_count}")
                
                if visible_count == 1:
                    logger.debug(f"DEBUG: (_try_value_attribute_selector) Found unique visible selector")
                    return visible_selector
                elif visible_count > 1:
                    # If still multiple visible, try to use the first visible one
                    return f'{visible_selector} >> nth=0'
    
    return None


async def _try_form_scoped_selector(
    page: Page, element: ElementHandle, tag_name: str
) -> Optional[str]:
    """Try to create a selector scoped to the parent form, useful for e-commerce add-to-cart buttons."""
    try:
        # Check if element is within a form
        form_info = await element.evaluate("""
            (el) => {
                const form = el.closest('form');
                if (!form) return null;
                
                return {
                    hasForm: true,
                    formClass: form.className || '',
                    formId: form.id || '',
                    formAction: form.action || '',
                    formRole: form.getAttribute('role') || ''
                };
            }
        """)
        
        form_info = await _ensure_serialisable(form_info)
        
        if not form_info or not form_info.get('hasForm'):
            return None
        
        # Build form selector
        form_selectors = []
        
        if form_info.get('formId'):
            form_selectors.append(f"form#{form_info['formId']}")
        
        if form_info.get('formClass'):
            stable_form_classes = [
                cls for cls in form_info['formClass'].split() 
                if not _is_dynamic_class(cls)
            ]
            if stable_form_classes:
                form_selectors.append(f"form.{stable_form_classes[0]}")
        
        if form_info.get('formRole'):
            form_selectors.append(f"form[role=\"{form_info['formRole']}\"]")
        
        if not form_selectors:
            form_selectors.append('form')
        
        # Try different combinations with the form scope
        for form_selector in form_selectors:
            # First try with descendant selector (space) instead of direct child (>)
            # This handles cases where button is nested deeper in the form
            
            # Try form descendant tag
            selector = f"{form_selector} {tag_name}"
            count = await page.locator(selector).count()
            logger.debug(f"DEBUG: (_try_form_scoped_selector) Trying: '{selector}', Count: {count}")
            
            if count == 1:
                logger.debug(f"DEBUG: (_try_form_scoped_selector) Found unique form descendant tag selector")
                return selector
            
            # Try with element attributes
            name_attr = await element.get_attribute("name")
            if name_attr:
                selector = f"{form_selector} {tag_name}[name=\"{name_attr}\"]"
                count = await page.locator(selector).count()
                logger.debug(f"DEBUG: (_try_form_scoped_selector) Trying: '{selector}', Count: {count}")
                
                if count == 1:
                    logger.debug(f"DEBUG: (_try_form_scoped_selector) Found unique form descendant tag[name] selector")
                    return selector
            
            # Try with aria-label for buttons
            if tag_name in ["button", "input"]:
                aria_label = await element.get_attribute("aria-label")
                if aria_label:
                    selector = f"{form_selector} {tag_name}[aria-label=\"{aria_label}\"]"
                    count = await page.locator(selector).count()
                    logger.debug(f"DEBUG: (_try_form_scoped_selector) Trying: '{selector}', Count: {count}")
                    
                    if count == 1:
                        logger.debug(f"DEBUG: (_try_form_scoped_selector) Found unique form descendant tag[aria-label] selector")
                        return selector
                    
                    # Try with type attribute as well
                    type_attr = await element.get_attribute("type")
                    if type_attr:
                        selector = f"{form_selector} {tag_name}[type=\"{type_attr}\"][aria-label=\"{aria_label}\"]"
                        count = await page.locator(selector).count()
                        logger.debug(f"DEBUG: (_try_form_scoped_selector) Trying: '{selector}', Count: {count}")
                        
                        if count == 1:
                            logger.debug(f"DEBUG: (_try_form_scoped_selector) Found unique form descendant tag[type][aria-label] selector")
                            return selector
                    
                    # Try with :visible if still multiple
                    if count > 1:
                        visible_selector = f"{form_selector} {tag_name}[aria-label=\"{aria_label}\"]:visible"
                        visible_count = await page.locator(visible_selector).count()
                        logger.debug(f"DEBUG: (_try_form_scoped_selector) Trying: '{visible_selector}', Count: {visible_count}")
                        
                        if visible_count == 1:
                            logger.debug(f"DEBUG: (_try_form_scoped_selector) Found unique form descendant tag[aria-label]:visible selector")
                            return visible_selector
                        elif visible_count > 1:
                            # Use the first visible one
                            return f"{visible_selector} >> nth=0"
            
            # Try with value attribute for buttons
            if tag_name in ["button", "input"]:
                value_attr = await element.get_attribute("value")
                if value_attr:
                    selector = f"{form_selector} {tag_name}[value=\"{value_attr}\"]"
                    count = await page.locator(selector).count()
                    logger.debug(f"DEBUG: (_try_form_scoped_selector) Trying: '{selector}', Count: {count}")
                    
                    if count == 1:
                        logger.debug(f"DEBUG: (_try_form_scoped_selector) Found unique form tag[value] selector")
                        return selector
                    
                    # Try with both name and value
                    if name_attr:
                        selector = f"{form_selector} {tag_name}[name=\"{name_attr}\"][value=\"{value_attr}\"]"
                        count = await page.locator(selector).count()
                        logger.debug(f"DEBUG: (_try_form_scoped_selector) Trying: '{selector}', Count: {count}")
                        
                        if count == 1:
                            logger.debug(f"DEBUG: (_try_form_scoped_selector) Found unique form tag[name][value] selector")
                            return selector
            
            # Try with text content
            text_content = await element.text_content()
            if text_content and len(text_content.strip()) <= MAX_TEXT_SELECTOR_LENGTH:
                clean_text = " ".join(text_content.strip().split())
                escaped_text = clean_text.replace('"', '\\"')
                selector = f"{form_selector} {tag_name}:has-text(\"{escaped_text}\")"
                count = await page.locator(selector).count()
                logger.debug(f"DEBUG: (_try_form_scoped_selector) Trying: '{selector}', Count: {count}")
                
                if count == 1:
                    logger.debug(f"DEBUG: (_try_form_scoped_selector) Found unique form tag:has-text selector")
                    return selector
            
            # Try with class if available
            class_attr = await element.get_attribute("class")
            if class_attr:
                stable_classes = [
                    cls for cls in class_attr.split() 
                    if not _is_dynamic_class(cls)
                ]
                if stable_classes:
                    selector = f"{form_selector} {tag_name}.{stable_classes[0]}"
                    count = await page.locator(selector).count()
                    logger.debug(f"DEBUG: (_try_form_scoped_selector) Trying: '{selector}', Count: {count}")
                    
                    if count == 1:
                        logger.debug(f"DEBUG: (_try_form_scoped_selector) Found unique form tag.class selector")
                        return selector
                    
                    # Try with :visible
                    visible_selector = f"{selector}:visible"
                    visible_count = await page.locator(visible_selector).count()
                    logger.debug(f"DEBUG: (_try_form_scoped_selector) Trying: '{visible_selector}', Count: {visible_count}")
                    
                    if visible_count == 1:
                        logger.debug(f"DEBUG: (_try_form_scoped_selector) Found unique form tag.class:visible selector")
                        return visible_selector
                    elif visible_count > 1:
                        # Use the first visible one
                        return f"{visible_selector} >> nth=0"
        
    except Exception as e:
        logger.debug(f"DEBUG: (_try_form_scoped_selector) Exception: {e}")
    
    return None


async def _try_image_src_selector(
    page: Page, element: ElementHandle, tag_name: str
) -> Optional[str]:
    """Try to use image src attribute as a selector, useful for image galleries."""
    if tag_name != "img":
        return None
    
    try:
        src_attr = await element.get_attribute("src")
        if not src_attr:
            return None
        
        # For images with query parameters, we might want to match just the base URL
        # or the full URL depending on uniqueness
        
        # First try the full src
        escaped_src = src_attr.replace('"', '\\"')
        full_selector = f'img[src="{escaped_src}"]'
        count = await page.locator(full_selector).count()
        logger.debug(f"DEBUG: (_try_image_src_selector) Trying full src selector: '{full_selector}', Count: {count}")
        
        if count == 1:
            logger.debug(f"DEBUG: (_try_image_src_selector) Found unique full src selector")
            return full_selector
        
        # If full src has query params and isn't unique, try base URL
        if "?" in src_attr and count != 1:
            base_src = src_attr.split("?")[0]
            escaped_base = base_src.replace('"', '\\"')
            
            # Try starts-with selector for base URL
            starts_with_selector = f'img[src^="{escaped_base}"]'
            count = await page.locator(starts_with_selector).count()
            logger.debug(f"DEBUG: (_try_image_src_selector) Trying starts-with selector: '{starts_with_selector}', Count: {count}")
            
            if count == 1:
                logger.debug(f"DEBUG: (_try_image_src_selector) Found unique starts-with selector")
                return starts_with_selector
        
        # Try combining with alt text if available
        alt_attr = await element.get_attribute("alt")
        if alt_attr:  # Even empty alt text can be useful
            escaped_alt = alt_attr.replace('"', '\\"')
            combined_selector = f'img[src="{escaped_src}"][alt="{escaped_alt}"]'
            count = await page.locator(combined_selector).count()
            logger.debug(f"DEBUG: (_try_image_src_selector) Trying src+alt selector: '{combined_selector}', Count: {count}")
            
            if count == 1:
                logger.debug(f"DEBUG: (_try_image_src_selector) Found unique src+alt selector")
                return combined_selector
        
        # If still not unique, try with parent context
        parent_info = await element.evaluate("""
            (el) => {
                const parent = el.parentElement;
                if (!parent) return null;
                return {
                    tag: parent.tagName.toLowerCase(),
                    classes: parent.className || '',
                    href: parent.getAttribute('href') || ''
                };
            }
        """)
        
        parent_info = await _ensure_serialisable(parent_info)
        
        if parent_info and parent_info.get('tag') == 'a' and parent_info.get('href'):
            # Image is inside a link, use that for context
            escaped_href = parent_info['href'].replace('"', '\\"')
            parent_selector = f'a[href="{escaped_href}"] > img'
            count = await page.locator(parent_selector).count()
            logger.debug(f"DEBUG: (_try_image_src_selector) Trying parent link selector: '{parent_selector}', Count: {count}")
            
            if count == 1:
                logger.debug(f"DEBUG: (_try_image_src_selector) Found unique parent link > img selector")
                return parent_selector
            
            # Try with src as well
            parent_src_selector = f'a[href="{escaped_href}"] > img[src="{escaped_src}"]'
            count = await page.locator(parent_src_selector).count()
            logger.debug(f"DEBUG: (_try_image_src_selector) Trying parent link + src selector: '{parent_src_selector}', Count: {count}")
            
            if count == 1:
                logger.debug(f"DEBUG: (_try_image_src_selector) Found unique parent link > img[src] selector")
                return parent_src_selector
        
    except Exception as e:
        logger.debug(f"DEBUG: (_try_image_src_selector) Exception: {e}")
    
    return None


async def _generate_unique_stable_css_selector(
    page: Page, element: ElementHandle, tag_name: str
) -> Optional[str]:
    try:
        class_attr = await element.get_attribute("class")
        if not class_attr:
            logger.debug(
                f"DEBUG: (_generate_unique_stable_css_selector) No class attribute found"
            )
            return None

        all_classes = class_attr.split()
        logger.debug(
            f"DEBUG: (_generate_unique_stable_css_selector) All classes: {all_classes}"
        )

        stable_classes = [cls for cls in all_classes if not _is_dynamic_class(cls)]
        if not stable_classes:
            logger.debug(
                f"DEBUG: (_generate_unique_stable_css_selector) No stable classes found"
            )
            return None

        logger.debug(
            f"DEBUG: (_generate_unique_stable_css_selector) Stable classes: {stable_classes}"
        )

        for i in range(1, min(len(stable_classes) + 1, 4)):
            current_classes_subset = stable_classes[:i]
            selector = f"{tag_name}.{'.'.join(current_classes_subset)}"
            count = await page.locator(selector).count()
            logger.debug(
                f"DEBUG: (_generate_unique_stable_css_selector) Trying selector with {i} classes: '{selector}', Count: {count}"
            )
            if count == 1:
                logger.debug(
                    f"DEBUG: (_generate_unique_stable_css_selector) Found unique CSS selector"
                )
                return selector

        logger.debug(
            f"DEBUG: (_generate_unique_stable_css_selector) No unique CSS selector found"
        )
    except Exception as e:
        logger.debug(f"DEBUG: (_generate_unique_stable_css_selector) Exception: {e}")
    return None


async def _generate_unique_combined_selector(
    page: Page, element: ElementHandle, tag_name: str
) -> Optional[str]:
    try:
        # -----------------------------------------------
        # Always have text_content available so later checks never fail
        # -----------------------------------------------
        raw_text_content = await element.text_content()
        text_content = raw_text_content.strip() if raw_text_content else ""

        parts = [tag_name]
        class_attr = await element.get_attribute("class")
        if class_attr:
            stable_classes = [
                cls for cls in class_attr.split() if not _is_dynamic_class(cls)
            ]
            if stable_classes:
                parts.append("." + ".".join(stable_classes[:2]))
                logger.debug(
                    f"DEBUG: (_generate_unique_combined_selector) Found stable classes: {stable_classes[:2]}"
                )
            else:
                logger.debug(
                    f"DEBUG: (_generate_unique_combined_selector) No stable classes found in: '{class_attr}'"
                )
        else:
            logger.debug(
                f"DEBUG: (_generate_unique_combined_selector) No class attribute found"
            )

        if tag_name == "input":
            input_type = await element.get_attribute("type")
            if input_type and not _is_dynamic_attribute_value(input_type):
                parts.append(f'[type="{input_type}"]')
                logger.debug(
                    f"DEBUG: (_generate_unique_combined_selector) Added input type: {input_type}"
                )

        if len(parts) > 1:
            candidate_selector = "".join(parts)
            # 1) Try plain tag+class(+attr) selector first
            count1 = await page.locator(candidate_selector).count()
            logger.debug(
                f"DEBUG: (_generate_unique_combined_selector) Trying selector: '{candidate_selector}', Count: {count1}"
            )
            if count1 == 1:
                logger.debug(
                    f"DEBUG: (_generate_unique_combined_selector) Found unique tag+class selector: '{candidate_selector}'"
                )
                return candidate_selector
            
            # 1.5) Try with placeholder if available
            if tag_name in FORM_TAGS:
                placeholder = await element.get_attribute("placeholder")
                if placeholder:
                    escaped_placeholder = placeholder.replace('"', '\\"')
                    placeholder_selector = f'{candidate_selector}[placeholder="{escaped_placeholder}"]'
                    count_p = await page.locator(placeholder_selector).count()
                    logger.debug(
                        f"DEBUG: (_generate_unique_combined_selector) Trying selector: '{placeholder_selector}', Count: {count_p}"
                    )
                    if count_p == 1:
                        logger.debug(
                            f"DEBUG: (_generate_unique_combined_selector) Found unique tag+class+placeholder selector"
                        )
                        return placeholder_selector
                    
                    # Try with :visible
                    if count_p > 1:
                        visible_placeholder = f'{placeholder_selector}:visible'
                        visible_count = await page.locator(visible_placeholder).count()
                        logger.debug(
                            f"DEBUG: (_generate_unique_combined_selector) Trying visible placeholder selector: '{visible_placeholder}', Count: {visible_count}"
                        )
                        if visible_count == 1:
                            return visible_placeholder
                        elif visible_count > 1:
                            return f'{visible_placeholder} >> nth=0'

            # 2) If that is not unique and element has usable text, try adding :has-text()
            if text_content:
                clean_text = " ".join(text_content.split())
                logger.debug(
                    f"DEBUG: (_generate_unique_combined_selector) Found text content: '{clean_text}'"
                )
                if clean_text and len(clean_text) <= MAX_TEXT_SELECTOR_LENGTH:
                    escaped_text = clean_text.replace('"', '\\"')
                    candidate_with_text = (
                        f'{candidate_selector}:has-text("{escaped_text}")'
                    )
                    count2 = await page.locator(candidate_with_text).count()
                    logger.debug(
                        f"DEBUG: (_generate_unique_combined_selector) Trying selector: '{candidate_with_text}', Count: {count2}"
                    )
                    if count2 == 1:
                        logger.debug(
                            f"DEBUG: (_generate_unique_combined_selector) Found unique tag+class+text selector: '{candidate_with_text}'"
                        )
                        return candidate_with_text
                else:
                    logger.debug(
                        f"DEBUG: (_generate_unique_combined_selector) Text too long ({len(clean_text)}) or empty"
                    )
            else:
                logger.debug(
                    f"DEBUG: (_generate_unique_combined_selector) No text content found"
                )

        # 3) For <a> tags try including href if still not unique
        if tag_name == "a":
            href_attr = await element.get_attribute("href")
            logger.debug(
                f"DEBUG: (_generate_unique_combined_selector) Found href: '{href_attr}'"
            )
            if href_attr and not _is_dynamic_attribute_value(href_attr):
                escaped_href = href_attr.replace('"', '\\"')
                candidate_with_href = f'{parts[0]}[href="{escaped_href}"]'  # tag + href (ignore classes which may be empty)
                count3 = await page.locator(candidate_with_href).count()
                logger.debug(
                    f"DEBUG: (_generate_unique_combined_selector) Trying selector: '{candidate_with_href}', Count: {count3}"
                )

                # Include classes if we had added them earlier
                if len(parts) > 1 and parts[1].startswith("."):
                    candidate_with_href = f'{parts[0]}{parts[1]}[href="{escaped_href}"]'
                    count3b = await page.locator(candidate_with_href).count()
                    logger.debug(
                        f"DEBUG: (_generate_unique_combined_selector) Trying selector with classes: '{candidate_with_href}', Count: {count3b}"
                    )
                    if count3b == 1:
                        logger.debug(
                            f"DEBUG: (_generate_unique_combined_selector) Found unique tag+class+href selector: '{candidate_with_href}'"
                        )
                        return candidate_with_href
                    count3 = count3b  # Use this count for the next check

                if count3 == 1:
                    logger.debug(
                        f"DEBUG: (_generate_unique_combined_selector) Found unique tag+href selector: '{candidate_with_href}'"
                    )
                    return candidate_with_href

                # Finally try href + :has-text()
                if text_content:
                    clean_text = " ".join(text_content.split())
                    if clean_text and len(clean_text) <= MAX_TEXT_SELECTOR_LENGTH:
                        escaped_text = clean_text.replace('"', '\\"')
                        candidate_href_text = (
                            f'{candidate_with_href}:has-text("{escaped_text}")'
                        )
                        count4 = await page.locator(candidate_href_text).count()
                        logger.debug(
                            f"DEBUG: (_generate_unique_combined_selector) Trying selector: '{candidate_href_text}', Count: {count4}"
                        )
                        if count4 == 1:
                            logger.debug(
                                f"DEBUG: (_generate_unique_combined_selector) Found unique tag+href+text selector: '{candidate_href_text}'"
                            )
                            return candidate_href_text

                        # 4b) If duplicates remain, restrict to visible elements only.
                        candidate_href_text_visible = f"{candidate_href_text}:visible"
                        count4_vis = await page.locator(
                            candidate_href_text_visible
                        ).count()
                        logger.debug(
                            f"DEBUG: (_generate_unique_combined_selector) Trying selector (visible): '{candidate_href_text_visible}', Count: {count4_vis}"
                        )
                        # Not doing unique check here as all the tags have same link and same text
                        # if count4_vis == 1:
                        #     logger.debug(
                        #         f"DEBUG: (_generate_unique_combined_selector) Found unique tag+href+text+visible selector: '{candidate_href_text_visible}'"
                        #     )

                        if count4_vis > 0:
                            return candidate_href_text_visible

            else:
                logger.debug(
                    f"DEBUG: (_generate_unique_combined_selector) No href or dynamic href found"
                )

        # 4) For button/input tags, try including value attribute
        if tag_name in ["button", "input"]:
            value_attr = await element.get_attribute("value")
            logger.debug(
                f"DEBUG: (_generate_unique_combined_selector) Found value: '{value_attr}'"
            )
            if value_attr and not _is_dynamic_attribute_value(value_attr):
                escaped_value = value_attr.replace('"', '\\"')
                
                # Try tag + value
                candidate_with_value = f'{tag_name}[value="{escaped_value}"]'
                count_value = await page.locator(candidate_with_value).count()
                logger.debug(
                    f"DEBUG: (_generate_unique_combined_selector) Trying selector: '{candidate_with_value}', Count: {count_value}"
                )
                if count_value == 1:
                    logger.debug(
                        f"DEBUG: (_generate_unique_combined_selector) Found unique tag+value selector: '{candidate_with_value}'"
                    )
                    return candidate_with_value
                
                # Try tag + classes + value
                if len(parts) > 1:
                    candidate_with_classes_value = f'{"".join(parts)}[value="{escaped_value}"]'
                    count_cv = await page.locator(candidate_with_classes_value).count()
                    logger.debug(
                        f"DEBUG: (_generate_unique_combined_selector) Trying selector: '{candidate_with_classes_value}', Count: {count_cv}"
                    )
                    if count_cv == 1:
                        logger.debug(
                            f"DEBUG: (_generate_unique_combined_selector) Found unique tag+classes+value selector: '{candidate_with_classes_value}'"
                        )
                        return candidate_with_classes_value
                
                # Try tag + value + text
                if text_content:
                    clean_text = " ".join(text_content.split())
                    if clean_text and len(clean_text) <= MAX_TEXT_SELECTOR_LENGTH:
                        escaped_text = clean_text.replace('"', '\\"')
                        candidate_value_text = f'{candidate_with_value}:has-text("{escaped_text}")'
                        count_vt = await page.locator(candidate_value_text).count()
                        logger.debug(
                            f"DEBUG: (_generate_unique_combined_selector) Trying selector: '{candidate_value_text}', Count: {count_vt}"
                        )
                        if count_vt == 1:
                            logger.debug(
                                f"DEBUG: (_generate_unique_combined_selector) Found unique tag+value+text selector: '{candidate_value_text}'"
                            )
                            return candidate_value_text
                        
                        # If still not unique, try with :visible
                        if count_vt > 1:
                            candidate_visible = f'{candidate_value_text}:visible'
                            count_visible = await page.locator(candidate_visible).count()
                            logger.debug(
                                f"DEBUG: (_generate_unique_combined_selector) Trying visible selector: '{candidate_visible}', Count: {count_visible}"
                            )
                            if count_visible == 1:
                                logger.debug(
                                    f"DEBUG: (_generate_unique_combined_selector) Found unique tag+value+text+visible selector"
                                )
                                return candidate_visible
                            elif count_visible > 1:
                                # Use the first visible one
                                return f'{candidate_visible} >> nth=0'
                
                # Try just value + visible if text didn't work
                candidate_value_visible = f'{candidate_with_value}:visible'
                count_vv = await page.locator(candidate_value_visible).count()
                logger.debug(
                    f"DEBUG: (_generate_unique_combined_selector) Trying selector: '{candidate_value_visible}', Count: {count_vv}"
                )
                if count_vv == 1:
                    logger.debug(
                        f"DEBUG: (_generate_unique_combined_selector) Found unique tag+value+visible selector"
                    )
                    return candidate_value_visible
                elif count_vv > 1:
                    # Use the first visible one
                    return f'{candidate_value_visible} >> nth=0'
            
            # Try with aria-label if available
            aria_label = await element.get_attribute("aria-label")
            if aria_label:
                # Try tag + aria-label
                escaped_aria = aria_label.replace('"', '\\"')
                candidate_aria = f'{tag_name}[aria-label="{escaped_aria}"]'
                count_aria = await page.locator(candidate_aria).count()
                logger.debug(
                    f"DEBUG: (_generate_unique_combined_selector) Trying selector: '{candidate_aria}', Count: {count_aria}"
                )
                
                if count_aria == 1:
                    logger.debug(
                        f"DEBUG: (_generate_unique_combined_selector) Found unique tag+aria-label selector"
                    )
                    return candidate_aria
                
                # Try tag + classes + aria-label
                if len(parts) > 1:
                    candidate_classes_aria = f'{"".join(parts)}[aria-label="{escaped_aria}"]'
                    count_ca = await page.locator(candidate_classes_aria).count()
                    logger.debug(
                        f"DEBUG: (_generate_unique_combined_selector) Trying selector: '{candidate_classes_aria}', Count: {count_ca}"
                    )
                    
                    if count_ca == 1:
                        logger.debug(
                            f"DEBUG: (_generate_unique_combined_selector) Found unique tag+classes+aria-label selector"
                        )
                        return candidate_classes_aria
                
                # Try with type attribute if available
                type_attr = await element.get_attribute("type")
                if type_attr:
                    candidate_type_aria = f'{tag_name}[type="{type_attr}"][aria-label="{escaped_aria}"]'
                    count_ta = await page.locator(candidate_type_aria).count()
                    logger.debug(
                        f"DEBUG: (_generate_unique_combined_selector) Trying selector: '{candidate_type_aria}', Count: {count_ta}"
                    )
                    
                    if count_ta == 1:
                        logger.debug(
                            f"DEBUG: (_generate_unique_combined_selector) Found unique tag+type+aria-label selector"
                        )
                        return candidate_type_aria
                    
                    # Try with classes as well
                    if len(parts) > 1:
                        candidate_all = f'{"".join(parts)}[type="{type_attr}"][aria-label="{escaped_aria}"]'
                        count_all = await page.locator(candidate_all).count()
                        logger.debug(
                            f"DEBUG: (_generate_unique_combined_selector) Trying selector: '{candidate_all}', Count: {count_all}"
                        )
                        
                        if count_all == 1:
                            logger.debug(
                                f"DEBUG: (_generate_unique_combined_selector) Found unique tag+classes+type+aria-label selector"
                            )
                            return candidate_all
                
                # Try with :visible
                candidate_aria_visible = f'{candidate_aria}:visible'
                count_av = await page.locator(candidate_aria_visible).count()
                logger.debug(
                    f"DEBUG: (_generate_unique_combined_selector) Trying selector: '{candidate_aria_visible}', Count: {count_av}"
                )
                
                if count_av == 1:
                    logger.debug(
                        f"DEBUG: (_generate_unique_combined_selector) Found unique tag+aria-label+visible selector"
                    )
                    return candidate_aria_visible
                elif count_av > 1:
                    # Use the first visible one
                    return f'{candidate_aria_visible} >> nth=0'

        # 5) For img tags, try using src attribute
        if tag_name == "img":
            src_attr = await element.get_attribute("src")
            logger.debug(
                f"DEBUG: (_generate_unique_combined_selector) Found src: '{src_attr}'"
            )
            if src_attr:
                escaped_src = src_attr.replace('"', '\\"')
                
                # Try tag + src
                candidate_with_src = f'img[src="{escaped_src}"]'
                count_src = await page.locator(candidate_with_src).count()
                logger.debug(
                    f"DEBUG: (_generate_unique_combined_selector) Trying selector: '{candidate_with_src}', Count: {count_src}"
                )
                if count_src == 1:
                    logger.debug(
                        f"DEBUG: (_generate_unique_combined_selector) Found unique img[src] selector: '{candidate_with_src}'"
                    )
                    return candidate_with_src
                
                # If src has query params, try without them
                if "?" in src_attr and count_src != 1:
                    base_src = src_attr.split("?")[0]
                    escaped_base = base_src.replace('"', '\\"')
                    candidate_base_src = f'img[src^="{escaped_base}"]'
                    count_base = await page.locator(candidate_base_src).count()
                    logger.debug(
                        f"DEBUG: (_generate_unique_combined_selector) Trying selector: '{candidate_base_src}', Count: {count_base}"
                    )
                    if count_base == 1:
                        logger.debug(
                            f"DEBUG: (_generate_unique_combined_selector) Found unique img[src^=] selector: '{candidate_base_src}'"
                        )
                        return candidate_base_src

        logger.debug(
            f"DEBUG: (_generate_unique_combined_selector) No unique selector found for {tag_name}"
        )
    except Exception as e:
        logger.debug(f"DEBUG: (_generate_unique_combined_selector) Exception: {e}")
    return None


async def _generate_unique_nth_child_selector(
    page: Page, element: ElementHandle
) -> Optional[str]:
    try:
        parent_info = await element.evaluate(
            """
            (el) => {
                const parent = el.parentElement;
                if (!parent) {
                    return null;
                }
                const children = Array.from(parent.children);
                const childIndex = children.indexOf(el) + 1; // 1-based index for :nth-child()

                return {
                    parentTag: parent.tagName.toLowerCase(),
                    parentClass: parent.className || "",
                    childTag: el.tagName.toLowerCase(),
                    childIndex,
                };
            }
            """
        )

        # If Playwright ever returns a JSHandle instead of a plain dict, convert it.
        if (
            parent_info
            and not isinstance(parent_info, dict)
            and hasattr(parent_info, "json_value")
        ):
            try:
                parent_info = await parent_info.json_value()  # type: ignore[attr-defined]
            except Exception:
                parent_info = None

        if not parent_info:
            logger.debug(
                f"DEBUG: (_generate_unique_nth_child_selector) No parent info found"
            )
            return None

        parent_tag: str = parent_info["parentTag"]
        child_index: int = parent_info["childIndex"]
        child_tag: str = parent_info["childTag"]
        logger.debug(
            f"DEBUG: (_generate_unique_nth_child_selector) Parent: {parent_tag}, Child: {child_tag}, Index: {child_index}"
        )

        selector1 = f"{parent_tag} > {child_tag}:nth-child({child_index})"
        count1 = await page.locator(selector1).count()
        logger.debug(
            f"DEBUG: (_generate_unique_nth_child_selector) Trying selector: '{selector1}', Count: {count1}"
        )
        if count1 == 1:
            logger.debug(
                f"DEBUG: (_generate_unique_nth_child_selector) Found unique basic nth-child selector"
            )
            return selector1

        parent_class_str: str = parent_info.get("parentClass", "")
        if parent_class_str:
            stable_parent_classes = [
                cls for cls in parent_class_str.split() if not _is_dynamic_class(cls)
            ]
            if stable_parent_classes:
                logger.debug(
                    f"DEBUG: (_generate_unique_nth_child_selector) Found stable parent classes: {stable_parent_classes[0]}"
                )
                selector2 = f"{parent_tag}.{stable_parent_classes[0]} > {child_tag}:nth-child({child_index})"
                count2 = await page.locator(selector2).count()
                logger.debug(
                    f"DEBUG: (_generate_unique_nth_child_selector) Trying selector with parent class: '{selector2}', Count: {count2}"
                )
                if count2 == 1:
                    logger.debug(
                        f"DEBUG: (_generate_unique_nth_child_selector) Found unique nth-child selector with parent class"
                    )
                    return selector2
            else:
                logger.debug(
                    f"DEBUG: (_generate_unique_nth_child_selector) No stable parent classes found in: '{parent_class_str}'"
                )
        else:
            logger.debug(
                f"DEBUG: (_generate_unique_nth_child_selector) No parent class attribute found"
            )

        logger.debug(
            f"DEBUG: (_generate_unique_nth_child_selector) No unique nth-child selector found"
        )
    except Exception as e:
        logger.debug(f"DEBUG: (_generate_unique_nth_child_selector) Exception: {e}")
    return None


async def _try_parent_context_selector(
    page: Page, element: ElementHandle, tag_name: str
) -> Optional[str]:
    """Try to create a selector using parent context when other methods fail."""
    try:
        parent_info = await element.evaluate("""
            (el) => {
                const parent = el.parentElement;
                if (!parent) return null;
                
                // Get grandparent info too
                const grandparent = parent.parentElement;
                
                return {
                    parentTag: parent.tagName.toLowerCase(),
                    parentClass: parent.className || '',
                    parentId: parent.id || '',
                    grandparentTag: grandparent ? grandparent.tagName.toLowerCase() : '',
                    grandparentClass: grandparent ? grandparent.className || '' : '',
                    // Check if element is visible
                    isVisible: el.offsetParent !== null || window.getComputedStyle(el).display !== 'none'
                };
            }
        """)
        
        parent_info = await _ensure_serialisable(parent_info)
        
        if not parent_info:
            return None
        
        # Build selectors using parent context
        parent_tag = parent_info.get('parentTag', '')
        parent_classes = parent_info.get('parentClass', '').split()
        stable_parent_classes = [cls for cls in parent_classes if not _is_dynamic_class(cls)]
        
        if stable_parent_classes:
            # Try parent.class > tag
            parent_selector = f"{parent_tag}.{stable_parent_classes[0]} > {tag_name}"
            count = await page.locator(parent_selector).count()
            logger.debug(f"DEBUG: (_try_parent_context_selector) Trying: '{parent_selector}', Count: {count}")
            
            if count == 1:
                logger.debug(f"DEBUG: (_try_parent_context_selector) Found unique parent.class > tag selector")
                return parent_selector
            
            # Add element attributes
            attrs = []
            
            # Type attribute
            if tag_name == "input":
                type_attr = await element.get_attribute("type")
                if type_attr:
                    attrs.append(f'[type="{type_attr}"]')
            
            # Placeholder
            placeholder = await element.get_attribute("placeholder")
            if placeholder:
                attrs.append(f'[placeholder="{placeholder.replace('"', '\\"')}"]')
            
            # Class
            class_attr = await element.get_attribute("class")
            if class_attr:
                element_classes = [cls for cls in class_attr.split() if not _is_dynamic_class(cls)]
                if element_classes:
                    attrs.append(f".{element_classes[0]}")
            
            if attrs:
                attr_string = "".join(attrs)
                parent_attr_selector = f"{parent_tag}.{stable_parent_classes[0]} > {tag_name}{attr_string}"
                count = await page.locator(parent_attr_selector).count()
                logger.debug(f"DEBUG: (_try_parent_context_selector) Trying: '{parent_attr_selector}', Count: {count}")
                
                if count == 1:
                    logger.debug(f"DEBUG: (_try_parent_context_selector) Found unique parent > tag+attrs selector")
                    return parent_attr_selector
        
        # Try using grandparent context if available
        grandparent_tag = parent_info.get('grandparentTag', '')
        grandparent_classes = parent_info.get('grandparentClass', '').split()
        stable_gp_classes = [cls for cls in grandparent_classes if not _is_dynamic_class(cls)]
        
        if stable_gp_classes and parent_tag:
            # Build grandparent > parent > tag selector
            gp_selector = f"{grandparent_tag}.{stable_gp_classes[0]} {parent_tag} > {tag_name}"
            count = await page.locator(gp_selector).count()
            logger.debug(f"DEBUG: (_try_parent_context_selector) Trying: '{gp_selector}', Count: {count}")
            
            if count == 1:
                logger.debug(f"DEBUG: (_try_parent_context_selector) Found unique grandparent context selector")
                return gp_selector
            
            # Add placeholder if available
            if placeholder:
                gp_placeholder_selector = f'{gp_selector}[placeholder="{placeholder.replace('"', '\\"')}"]'
                count = await page.locator(gp_placeholder_selector).count()
                logger.debug(f"DEBUG: (_try_parent_context_selector) Trying: '{gp_placeholder_selector}', Count: {count}")
                
                if count == 1:
                    logger.debug(f"DEBUG: (_try_parent_context_selector) Found unique grandparent+placeholder selector")
                    return gp_placeholder_selector
        
        # Last resort: use visibility
        if parent_info.get('isVisible'):
            # Try with just visible pseudo-selector
            if tag_name == "input" and placeholder:
                visible_selector = f'{tag_name}[placeholder="{placeholder.replace('"', '\\"')}"]:visible'
                count = await page.locator(visible_selector).count()
                logger.debug(f"DEBUG: (_try_parent_context_selector) Trying: '{visible_selector}', Count: {count}")
                
                if count == 1:
                    logger.debug(f"DEBUG: (_try_parent_context_selector) Found unique visible selector")
                    return visible_selector
                elif count > 1:
                    return f'{visible_selector} >> nth=0'
        
    except Exception as e:
        logger.debug(f"DEBUG: (_try_parent_context_selector) Exception: {e}")
    
    return None


async def _try_attributes_fallback_selector(
    page: Page, element: ElementHandle, tag_name: str, attributes: Optional[Dict[str, str]] = None
) -> Optional[str]:
    """Try to create a selector using provided attributes when all other strategies fail."""
    try:
        if not attributes:
            logger.debug(f"DEBUG: (_try_attributes_fallback_selector) No attributes available")
            return None
        
        logger.debug(f"DEBUG: (_try_attributes_fallback_selector) Available attributes: {list(attributes.keys())}")
        
        # Priority order for attributes to try
        priority_attrs = [
            'data-testid', 'data-test-id', 'data-test', 'data-cy', 'test-id', 'data-slot',  # Test IDs
            'id',  # ID attribute
            'name',  # Name attribute
            'aria-label',  # Aria label
            'placeholder',  # Placeholder
            'value',  # Value attribute
            'type',  # Type attribute
            'href',  # Href for links
            'src',  # Src for images
            'alt',  # Alt for images
            'title',  # Title attribute
            'class'  # Class attribute (last resort)
        ]
        
        # Try each priority attribute
        for attr_name in priority_attrs:
            if attr_name not in attributes:
                continue
                
            attr_value = attributes[attr_name]
            if not attr_value or _is_dynamic_attribute_value(attr_value):
                continue
            
            # Skip dynamic classes
            if attr_name == 'class' and _is_dynamic_class(attr_value):
                continue
            
            # Skip dynamic IDs
            if attr_name == 'id' and _is_dynamic_id(attr_value):
                continue
            
            # Build selector based on attribute type
            if attr_name == 'class':
                # For class, try stable classes only
                stable_classes = [cls for cls in attr_value.split() if not _is_dynamic_class(cls)]
                if not stable_classes:
                    continue
                
                # Try with first stable class
                selector = f"{tag_name}.{stable_classes[0]}"
                count = await page.locator(selector).count()
                logger.debug(f"DEBUG: (_try_attributes_fallback_selector) Trying class selector: '{selector}', Count: {count}")
                
                if count == 1:
                    logger.debug(f"DEBUG: (_try_attributes_fallback_selector) Found unique class selector")
                    return selector
                
                # Try with multiple stable classes
                if len(stable_classes) > 1:
                    multi_class_selector = f"{tag_name}.{'.'.join(stable_classes[:2])}"
                    count = await page.locator(multi_class_selector).count()
                    logger.debug(f"DEBUG: (_try_attributes_fallback_selector) Trying multi-class selector: '{multi_class_selector}', Count: {count}")
                    
                    if count == 1:
                        logger.debug(f"DEBUG: (_try_attributes_fallback_selector) Found unique multi-class selector")
                        return multi_class_selector
                
                # Try with :visible if multiple matches
                if count > 1:
                    visible_selector = f"{selector}:visible"
                    visible_count = await page.locator(visible_selector).count()
                    logger.debug(f"DEBUG: (_try_attributes_fallback_selector) Trying visible class selector: '{visible_selector}', Count: {visible_count}")
                    
                    if visible_count == 1:
                        logger.debug(f"DEBUG: (_try_attributes_fallback_selector) Found unique visible class selector")
                        return visible_selector
                    elif visible_count > 1:
                        return f"{visible_selector} >> nth=0"
            
            elif attr_name == 'id':
                # For ID, use # syntax
                selector = f"#{attr_value}"
                count = await page.locator(selector).count()
                logger.debug(f"DEBUG: (_try_attributes_fallback_selector) Trying ID selector: '{selector}', Count: {count}")
                
                if count == 1:
                    logger.debug(f"DEBUG: (_try_attributes_fallback_selector) Found unique ID selector")
                    return selector
            
            else:
                # For other attributes, use [attr="value"] syntax
                escaped_value = attr_value.replace('"', '\\"')
                selector = f"{tag_name}[{attr_name}=\"{escaped_value}\"]"
                count = await page.locator(selector).count()
                logger.debug(f"DEBUG: (_try_attributes_fallback_selector) Trying attribute selector: '{selector}', Count: {count}")
                
                if count == 1:
                    logger.debug(f"DEBUG: (_try_attributes_fallback_selector) Found unique attribute selector")
                    return selector
                
                # Try without tag name
                attr_only_selector = f"[{attr_name}=\"{escaped_value}\"]"
                count = await page.locator(attr_only_selector).count()
                logger.debug(f"DEBUG: (_try_attributes_fallback_selector) Trying attr-only selector: '{attr_only_selector}', Count: {count}")
                
                if count == 1:
                    logger.debug(f"DEBUG: (_try_attributes_fallback_selector) Found unique attr-only selector")
                    return attr_only_selector
                
                # Try with :visible if multiple matches
                if count > 1:
                    visible_selector = f"{selector}:visible"
                    visible_count = await page.locator(visible_selector).count()
                    logger.debug(f"DEBUG: (_try_attributes_fallback_selector) Trying visible attribute selector: '{visible_selector}', Count: {visible_count}")
                    
                    if visible_count == 1:
                        logger.debug(f"DEBUG: (_try_attributes_fallback_selector) Found unique visible attribute selector")
                        return visible_selector
                    elif visible_count > 1:
                        return f"{visible_selector} >> nth=0"
        
        # Try combining multiple attributes
        stable_attrs = {}
        for attr_name, attr_value in attributes.items():
            if not attr_value:
                continue
            
            # Skip dynamic values
            if attr_name in ['id'] and _is_dynamic_id(attr_value):
                continue
            if attr_name == 'class' and _is_dynamic_class(attr_value):
                continue
            if _is_dynamic_attribute_value(attr_value):
                continue
            
            stable_attrs[attr_name] = attr_value
        
        # Try combinations of stable attributes
        if len(stable_attrs) > 1:
            # Try type + name combination (common for form elements)
            if 'type' in stable_attrs and 'name' in stable_attrs:
                type_val = stable_attrs['type']
                name_val = stable_attrs['name']
                combined_selector = f"{tag_name}[type=\"{type_val}\"][name=\"{name_val}\"]"
                count = await page.locator(combined_selector).count()
                logger.debug(f"DEBUG: (_try_attributes_fallback_selector) Trying type+name selector: '{combined_selector}', Count: {count}")
                
                if count == 1:
                    logger.debug(f"DEBUG: (_try_attributes_fallback_selector) Found unique type+name selector")
                    return combined_selector
            
            # Try placeholder + type combination
            if 'placeholder' in stable_attrs and 'type' in stable_attrs:
                placeholder_val = stable_attrs['placeholder'].replace('"', '\\"')
                type_val = stable_attrs['type']
                combined_selector = f"{tag_name}[placeholder=\"{placeholder_val}\"][type=\"{type_val}\"]"
                count = await page.locator(combined_selector).count()
                logger.debug(f"DEBUG: (_try_attributes_fallback_selector) Trying placeholder+type selector: '{combined_selector}', Count: {count}")
                
                if count == 1:
                    logger.debug(f"DEBUG: (_try_attributes_fallback_selector) Found unique placeholder+type selector")
                    return combined_selector
        
        logger.debug(f"DEBUG: (_try_attributes_fallback_selector) No unique selector found using attributes")
        
    except Exception as e:
        logger.debug(f"DEBUG: (_try_attributes_fallback_selector) Exception: {e}")
    
    return None


# --- Main Orchestrator Function ---
async def get_selector(page: Page, xpath: str, action: str = "click", attributes: Optional[Dict[str, str]] = None) -> tuple[str, str]:
    try:
        element_locator = page.locator(xpath).first
        await element_locator.wait_for(state="attached", timeout=3000)
        element = await element_locator.element_handle()

        html = await element.evaluate("el => el.outerHTML")

        logger.debug(f"DEBUG: (get_selector) HTML: {html}")

        if not element:
            logger.debug(f"DEBUG: (get_selector) Element not found for XPath: {xpath}")
            return xpath, "fallback"

        tag_eval_result = await element.evaluate("(el) => el.tagName.toLowerCase()")
        tag_eval_result = await _ensure_serialisable(tag_eval_result)
        tag_name = str(tag_eval_result).lower()
        logger.debug(
            f"DEBUG: (get_codegen_selector) For xpath='{xpath}', tag='{tag_name}'"
        )

        selector_strategy_lambdas: List[Callable[[], Awaitable[Optional[str]]]] = [
            lambda: _try_test_id_selectors(page, element),
            lambda: _try_role_selectors(page, element, tag_name),
            lambda: _try_aria_label_selector(page, element, tag_name),
            lambda: _try_form_specific_selectors(page, element, tag_name),
            lambda: _try_text_content_selector(page, element),
            lambda: _try_id_selector(page, element),
            lambda: _try_name_attribute_selector(page, element),
            lambda: _try_value_attribute_selector(page, element, tag_name),
            lambda: _try_form_scoped_selector(page, element, tag_name),
            lambda: _try_image_src_selector(page, element, tag_name),
            lambda: _generate_unique_stable_css_selector(page, element, tag_name),
            lambda: _generate_unique_combined_selector(page, element, tag_name),
            lambda: _try_parent_context_selector(page, element, tag_name),
            lambda: _generate_unique_nth_child_selector(page, element),
        ]

        # Strategy names for tracking
        strategy_names = [
            "test_id", "role", "aria_label", "form_specific", "text_content", 
            "id", "name_attribute", "value_attribute", "form_scoped", "image_src", 
            "css_selector", "combined", "parent_context", "nth_child", "attributes_fallback"
        ]
        
        for i, strategy_lambda in enumerate(selector_strategy_lambdas):
            strategy_name = strategy_names[i]
            logger.debug(f"DEBUG: (get_codegen_selector) Trying strategy: {strategy_name}")
            potential_selector = await strategy_lambda()
            if potential_selector:
                logger.debug(
                    f"DEBUG: (get_codegen_selector) Strategy '{strategy_name}' yielded: '{potential_selector}' for xpath '{xpath}'"
                )
                return potential_selector, strategy_name
            else:
                logger.debug(
                    f"DEBUG: (get_codegen_selector) Strategy '{strategy_name}' yielded None for xpath '{xpath}'"
                )

        logger.debug(
            f"DEBUG: (get_codegen_selector) All strategies failed for xpath '{xpath}', falling back."
        )
        return xpath, "fallback"

    except Exception as e:
        logger.debug(
            f"DEBUG: (get_codegen_selector) Error in get_codegen_selector for xpath '{xpath}': {e}"
        )
        # If we have attributes and the element wasn't found, try attributes fallback
        if attributes:
            logger.debug(f"DEBUG: (get_selector) Element not found, trying attributes fallback strategy")

            tag_name = "div"
            if "/" in xpath:
                parts = xpath.split("/")
                for part in reversed(parts):
                    if part and not part.startswith("html") and not part.startswith("body"):
                        if "[" in part:
                            tag_name = part.split("[")[0]
                        else:
                            tag_name = part
                        break
            
            # Try attributes fallback strategy
            fallback_selector = await _try_attributes_fallback_selector(page, None, tag_name, attributes)
            if fallback_selector:
                logger.debug(f"DEBUG: (get_selector) Attributes fallback strategy succeeded: {fallback_selector}")
                return fallback_selector, "attributes_fallback"
        
        return xpath, "error"
