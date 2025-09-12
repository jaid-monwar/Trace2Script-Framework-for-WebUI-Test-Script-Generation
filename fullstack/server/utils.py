import asyncio

from playwright.async_api import Page


class PlaywrightActionError(Exception):
	pass

async def _try_locate_and_act(page: Page, selector: str, action_type: str, text: str | None = None, step_info: str = '') -> None:
	original_selector = selector
	
	if selector.startswith('xpath='):
		try:
			better_selector = await get_codegen_selector(page, selector)
			print(f'Generated better selector for {repr(selector)}: {repr(better_selector)}')
			
			if better_selector != selector:
				print(f'Attempting {action_type} ({step_info}) using generated selector: {repr(better_selector)}')
				try:
					locator = page.locator(better_selector).first
					if action_type == 'click':
						await locator.click(timeout=10000)
					elif action_type == 'fill' and text is not None:
						await locator.fill(text, timeout=10000)
					else:
						raise PlaywrightActionError(f"Invalid action_type '{action_type}' or missing text for fill. ({step_info})")
					
					print(f"  Action '{action_type}' successful with generated selector: {repr(better_selector)}")
					await page.wait_for_timeout(500)
					return
				except Exception as e:
					print(f"  Warning: Generated selector failed ({repr(better_selector)}): {e}. Falling back to original xpath...")
		except Exception as e:
			print(f"  Warning: get_codegen_selector failed: {e}. Using original selector...")
	
	print(f'Attempting {action_type} ({step_info}) using selector: {repr(selector)}')
	MAX_FALLBACKS = 50
	INITIAL_TIMEOUT = 10000
	FALLBACK_TIMEOUT = 1000

	try:
		locator = page.locator(selector).first
		if action_type == 'click':
			await locator.click(timeout=INITIAL_TIMEOUT)
		elif action_type == 'fill' and text is not None:
			await locator.fill(text, timeout=INITIAL_TIMEOUT)
		else:
			raise PlaywrightActionError(f"Invalid action_type '{action_type}' or missing text for fill. ({step_info})")
		print(f"  Action '{action_type}' successful with original selector.")
		await page.wait_for_timeout(500)
		return
	except Exception as e:
		print(f"  Warning: Action '{action_type}' failed with original selector ({repr(selector)}): {e}. Starting fallback...")

		if not selector.startswith('xpath='):
			raise PlaywrightActionError(
				f"Action '{action_type}' failed. Fallback not possible for non-XPath selector: {repr(selector)}. ({step_info})"
			)

		xpath_parts = selector.split('=', 1)
		if len(xpath_parts) < 2:
			raise PlaywrightActionError(
				f"Action '{action_type}' failed. Could not extract XPath string from selector: {repr(selector)}. ({step_info})"
			)
		xpath = xpath_parts[1]

		segments = [seg for seg in xpath.split('/') if seg]

		for i in range(1, min(MAX_FALLBACKS + 1, len(segments))):
			trimmed_xpath_raw = '/'.join(segments[i:])
			fallback_xpath = f'xpath=//{trimmed_xpath_raw}'

			print(f'    Fallback attempt {i}/{MAX_FALLBACKS}: Trying selector: {repr(fallback_xpath)}')
			try:
				locator = page.locator(fallback_xpath).first
				if action_type == 'click':
					await locator.click(timeout=FALLBACK_TIMEOUT)
				elif action_type == 'fill' and text is not None:
					try:
						await locator.clear(timeout=FALLBACK_TIMEOUT)
						await page.wait_for_timeout(100)
					except Exception as clear_error:
						print(f'    Warning: Failed to clear field during fallback ({step_info}): {clear_error}')
					await locator.fill(text, timeout=FALLBACK_TIMEOUT)

				print(f"    Action '{action_type}' successful with fallback selector: {repr(fallback_xpath)}")
				await page.wait_for_timeout(500)
				return
			except Exception as fallback_e:
				print(f'    Fallback attempt {i} failed: {fallback_e}')
				if i == MAX_FALLBACKS:
					raise PlaywrightActionError(
						f"Action '{action_type}' failed after {MAX_FALLBACKS} fallback attempts. Original selector: {repr(original_selector)}. ({step_info})"
					)

	raise PlaywrightActionError(f"Action '{action_type}' failed unexpectedly for {repr(original_selector)}. ({step_info})")


async def get_codegen_selector(page: Page, xpath: str, action: str = "click") -> str:
    import re

    DEFAULT_TIMEOUT = 10000
    ELEMENT_WAIT_TIMEOUT = 5000
    MAX_TEXT_LENGTH = 200
    MAX_RETRY_ATTEMPTS = 3
    
    async def _safe_execute_async(func, default_value=None, max_attempts=MAX_RETRY_ATTEMPTS):
        for attempt in range(max_attempts):
            try:
                return await func()
            except Exception as e:
                if attempt == max_attempts - 1:
                    print(f"  Warning: Failed after {max_attempts} attempts: {e}")
                    return default_value
                await asyncio.sleep(100)
        return default_value
    
    def _normalize_text(text: str) -> str:
        if not text:
            return ""
        normalized = re.sub(r'\s+', ' ', text.strip())
        return normalized
    
    def _escape_selector_value(value: str) -> str:
        if not value:
            return ""
        return value.replace('\\', '\\\\').replace('"', '\\"')
    
    async def _is_selector_truly_unique(selector: str) -> bool:
        try:
            count = await page.locator(selector).count()
            is_unique = count == 1
            
            if not is_unique:
                print(f"  Selector '{selector}' matches {count} elements (not unique)")
            
            return is_unique
        except Exception as e:
            print(f"  Error checking uniqueness for '{selector}': {e}")
            return False
    
    async def _is_selector_reasonably_unique(selector: str, max_count: int = 3) -> bool:
        try:
            count = await page.locator(selector).count()
            is_reasonable = 0 < count <= max_count
            
            if not is_reasonable:
                print(f"  Selector '{selector}' matches {count} elements (not reasonably unique)")
            
            return is_reasonable
        except Exception as e:
            print(f"  Error checking selector '{selector}': {e}")
            return False
    
    async def _validate_element_state(element):
        try:
            is_attached = await element.evaluate("el => el.isConnected")
            if not is_attached:
                return False
            
            is_visible = await element.is_visible()
            if not is_visible and action in ["click", "hover"]:
                print("  Warning: Element is not visible, selector may not work for interactions")
            
            return True
        except:
            return False
    
    async def _validate_final_selector(candidate_selector: str, require_strict_uniqueness: bool = True) -> bool:
        if require_strict_uniqueness:
            return await _is_selector_truly_unique(candidate_selector)
        else:
            return await _is_selector_reasonably_unique(candidate_selector)
    
    try:
        print(f"  Generating selector for xpath: {xpath}")
        
        element_locator = page.locator(xpath).first
        
        try:
            await element_locator.wait_for(state="attached", timeout=ELEMENT_WAIT_TIMEOUT)
            element = await element_locator.element_handle(timeout=DEFAULT_TIMEOUT)
        except Exception as e:
            print(f"  Warning: Element not found or not ready: {e}")
            return xpath
        
        if not element:
            print("  Warning: Could not get element handle")
            return xpath
        
        if not await _validate_element_state(element):
            print("  Warning: Element is not in valid state")
            return xpath
        
        tag_name = await _safe_execute_async(
            lambda: element.evaluate("el => el.tagName.toLowerCase()"),
            default_value="unknown"
        )
        
        print(f"  Element tag: {tag_name}")
        
        candidate_selectors = []
        
        test_attrs = [
            "data-testid", "data-test-id", "data-test", "data-cy", "data-qa", 
            "data-automation", "test-id", "testid", "data-test-selector",
            "automation-id", "qa-selector", "data-qa-id"
        ]
        
        for test_attr in test_attrs:
            test_id = await _safe_execute_async(
                lambda attr=test_attr: element.get_attribute(attr)
            )
            if test_id and test_id.strip():
                test_id = _escape_selector_value(test_id.strip())
                candidate = f'[{test_attr}="{test_id}"]'
                if await _is_selector_truly_unique(candidate):
                    print(f"  Found unique test ID selector: {candidate}")
                    candidate_selectors.append((candidate, 10, True))
        
        element_id = await _safe_execute_async(
            lambda: element.get_attribute("id")
        )
        
        if element_id and not _is_dynamic_id(element_id):
            escaped_id = _escape_selector_value(element_id)
            candidate = f'#{escaped_id}'
            if await _is_selector_truly_unique(candidate):
                print(f"  Found unique ID selector: {candidate}")
                candidate_selectors.append((candidate, 9, True))
        
        explicit_role = await _safe_execute_async(
            lambda: element.get_attribute("role")
        )
        inferred_role = await _infer_role_from_element(element, tag_name)
        
        role = explicit_role or inferred_role
        
        if role:
            accessible_name = await _get_comprehensive_accessible_name(element, tag_name)
            if accessible_name and len(accessible_name.strip()) > 0:
                clean_name = _normalize_text(accessible_name)
                escaped_name = _escape_selector_value(clean_name)
                
                if len(clean_name) <= MAX_TEXT_LENGTH:
                    candidate = f'role={role}[name="{escaped_name}"]'
                    if await _is_selector_truly_unique(candidate):
                        print(f"  Found unique role with name selector: {candidate}")
                        candidate_selectors.append((candidate, 8, True))
                    elif await _is_selector_reasonably_unique(candidate):
                        print(f"  Found reasonably unique role with name selector: {candidate}")
                        candidate_selectors.append((candidate, 7, False))
        
        if tag_name in ["input", "textarea", "select"]:
            label_text = await _get_associated_label_text(page, element)
            if label_text:
                clean_label = _normalize_text(label_text)
                escaped_label = _escape_selector_value(clean_label)
                candidate = f'label="{escaped_label}"'
                if await _is_selector_truly_unique(candidate):
                    print(f"  Found unique label selector: {candidate}")
                    candidate_selectors.append((candidate, 8, True))
            
            placeholder = await _safe_execute_async(
                lambda: element.get_attribute("placeholder")
            )
            if placeholder and placeholder.strip():
                clean_placeholder = _normalize_text(placeholder)
                escaped_placeholder = _escape_selector_value(clean_placeholder)
                candidate = f'placeholder="{escaped_placeholder}"'
                if await _is_selector_truly_unique(candidate):
                    print(f"  Found unique placeholder selector: {candidate}")
                    candidate_selectors.append((candidate, 7, True))
        
        name_attr = await _safe_execute_async(
            lambda: element.get_attribute("name")
        )
        
        if name_attr and name_attr.strip():
            escaped_name = _escape_selector_value(name_attr.strip())
            candidate = f'[name="{escaped_name}"]'
            if await _is_selector_truly_unique(candidate):
                print(f"  Found unique name selector: {candidate}")
                candidate_selectors.append((candidate, 6, True))
        
        text_content = await _safe_execute_async(
            lambda: element.text_content(),
            default_value=""
        )
        
        if text_content and text_content.strip():
            clean_text = _normalize_text(text_content)
            
            if 0 < len(clean_text) <= MAX_TEXT_LENGTH:
                escaped_text = _escape_selector_value(clean_text)
                
                candidate = f'text="{escaped_text}"'
                if await _is_selector_truly_unique(candidate):
                    print(f"  Found unique text selector: {candidate}")
                    candidate_selectors.append((candidate, 5, True))
        
        important_attrs = ["type", "value", "href", "src", "alt", "title"]
        
        for attr in important_attrs:
            attr_value = await _safe_execute_async(
                lambda a=attr: element.get_attribute(a)
            )
            
            if attr_value and attr_value.strip() and not _is_dynamic_value(attr_value):
                escaped_value = _escape_selector_value(attr_value.strip())
                candidate = f'[{attr}="{escaped_value}"]'
                if await _is_selector_truly_unique(candidate):
                    print(f"  Found unique {attr} selector: {candidate}")
                    candidate_selectors.append((candidate, 4, True))
        
        css_selector = await _generate_stable_css_selector(page, element)
        if css_selector:
            if await _is_selector_truly_unique(css_selector):
                print(f"  Found unique CSS selector: {css_selector}")
                candidate_selectors.append((css_selector, 3, True))
            elif await _is_selector_reasonably_unique(css_selector):
                print(f"  Found reasonably unique CSS selector: {css_selector}")
                candidate_selectors.append((css_selector, 2, False))
        
        try:
            position_selector = await _generate_position_based_selector(page, element, tag_name)
            if position_selector:
                if await _is_selector_truly_unique(position_selector):
                    print(f"  Found unique position-based selector: {position_selector}")
                    candidate_selectors.append((position_selector, 1, True))
                elif await _is_selector_reasonably_unique(position_selector):
                    print(f"  Found reasonably unique position-based selector: {position_selector}")
                    candidate_selectors.append((position_selector, 1, False))
        except Exception as e:
            print(f"  Warning: Position-based selector generation failed: {e}")
        
        if candidate_selectors:
            candidate_selectors.sort(key=lambda x: (x[2], x[1]), reverse=True)
            
            best_selector, priority, is_strict = candidate_selectors[0]
            
            if await _validate_final_selector(best_selector, require_strict_uniqueness=is_strict):
                print(f"  Selected best selector: {best_selector} (priority: {priority}, strict: {is_strict})")
                return best_selector
            else:
                print(f"  Best candidate selector '{best_selector}' failed final validation")
        
        try:
            minimal_xpath = await _generate_minimal_xpath(page, element)
            if minimal_xpath != xpath:
                if await _is_selector_truly_unique(minimal_xpath):
                    print(f"  Generated unique minimal xpath: {minimal_xpath}")
                    return minimal_xpath
                else:
                    print(f"  Generated minimal xpath is not unique: {minimal_xpath}")
        except Exception as e:
            print(f"  Warning: Minimal xpath generation failed: {e}")
        
        print(f"  No unique selector found, using original xpath as fallback: {xpath}")
        return xpath
        
    except Exception as e:
        print(f"  Error in get_codegen_selector: {e}")
        import traceback
        traceback.print_exc()
        return xpath

def _is_dynamic_value(value: str) -> bool:
    import re
    
    if not value:
        return False
    
    dynamic_patterns = [
        r'.*\d{10,}.*',
        r'.*[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}.*',
        r'.*_ngcontent-.*',
        r'.*-\d{4,}$',
        r'^[a-f0-9]{32,}$',
        r'.*react-.*\d+.*',
        r'.*ember\d+.*',
        r'.*_\d{6,}$',
        r'session-.*',
        r'temp-.*',
        r'.*\d{4}-\d{2}-\d{2}.*',
    ]
    
    return any(re.match(pattern, value, re.IGNORECASE) for pattern in dynamic_patterns)

async def _generate_position_based_selector(page: Page, element, tag_name: str) -> str:
    try:
        
        if not parent_info:
            return None
        
        parent_selector = ""
        
        if parent_info.get('parentId') and not _is_dynamic_id(parent_info['parentId']):
            parent_selector = f"#{parent_info['parentId']}"
        elif parent_info.get('parentClass'):
            classes = parent_info['parentClass'].split()
            stable_classes = [cls for cls in classes if not _is_dynamic_class(cls)]
            if stable_classes:
                parent_selector = f"{parent_info['parentTag']}.{'.'.join(stable_classes[:2])}"
        
        if not parent_selector:
            parent_selector = parent_info['parentTag']
        
        if parent_info['sameTagCount'] > 1:
            return f"{parent_selector} > {tag_name}:nth-of-type({parent_info['sameTagPosition']})"
        else:
            return f"{parent_selector} > {tag_name}"
            
    except Exception as e:
        print(f"  Warning: Position-based selector generation failed: {e}")
        return None

async def _infer_role_from_element(element, tag_name: str) -> str:
    try:
        role_mapping = {
            "button": "button",
            "a": "link",
            "textarea": "textbox", 
            "select": "combobox",
            "img": "img",
            "h1": "heading", "h2": "heading", "h3": "heading",
            "h4": "heading", "h5": "heading", "h6": "heading",
            "nav": "navigation",
            "main": "main",
            "header": "banner",
            "footer": "contentinfo",
            "section": "region",
            "article": "article",
            "aside": "complementary",
            "form": "form",
            "table": "table",
            "ul": "list",
            "ol": "list",
            "li": "listitem",
            "dialog": "dialog",
            "menu": "menu",
            "menuitem": "menuitem",
            "tab": "tab",
            "tabpanel": "tabpanel",
            "progressbar": "progressbar",
            "slider": "slider",
            "spinbutton": "spinbutton",
            "searchbox": "searchbox"
        }
        
        if tag_name in role_mapping:
            return role_mapping[tag_name]
        
        if tag_name == "input":
            input_type = await element.get_attribute("type") or "text"
            input_roles = {
                "button": "button",
                "submit": "button",
                "reset": "button", 
                "image": "button",
                "checkbox": "checkbox",
                "radio": "radio",
                "text": "textbox",
                "email": "textbox",
                "password": "textbox",
                "tel": "textbox",
                "url": "textbox",
                "search": "searchbox",
                "number": "spinbutton",
                "range": "slider",
                "color": "textbox",
                "date": "textbox",
                "datetime-local": "textbox",
                "month": "textbox",
                "time": "textbox",
                "week": "textbox",
                "file": "button"
            }
            return input_roles.get(input_type, "textbox")
        
        if tag_name == "div":
            
            if has_click_handler:
                return "button"
            
    except Exception as e:
        print(f"  Warning: Role inference failed: {e}")
    
    return None

async def _get_comprehensive_accessible_name(element, tag_name: str) -> str:
    try:
        aria_label = await element.get_attribute("aria-label")
        if aria_label and aria_label.strip():
            return aria_label.strip()
        
        aria_labelledby = await element.get_attribute("aria-labelledby")
        if aria_labelledby:
            try:
                if labelledby_text and labelledby_text.strip():
                    return labelledby_text.strip()
            except Exception as e:
                print(f"  Warning: aria-labelledby resolution failed: {e}")
        
        if tag_name in ["input", "textarea", "select"]:
            label_text = await _get_associated_label_text(None, element)
            if label_text:
                return label_text
        
        if tag_name in ["a", "button"]:
            inner_text = await element.inner_text()
            if inner_text and inner_text.strip():
                return inner_text.strip()
        
        if tag_name == "input":
            value = await element.get_attribute("value")
            if value and value.strip():
                return value.strip()
        
        if tag_name == "img":
            alt = await element.get_attribute("alt")
            if alt and alt.strip():
                return alt.strip()
        
        title = await element.get_attribute("title")
        if title and title.strip():
            return title.strip()
        
        if tag_name in ["input", "textarea"]:
            placeholder = await element.get_attribute("placeholder")
            if placeholder and placeholder.strip():
                return placeholder.strip()
        
        text_content = await element.text_content()
        if text_content and text_content.strip():
            clean_text = ' '.join(text_content.strip().split())
            if len(clean_text) <= 100:
                return clean_text
        
    except Exception as e:
        print(f"  Warning: Accessible name calculation failed: {e}")
    
    return ""

async def _get_associated_label_text(page: Page, element) -> str:
    try:
        element_id = await element.get_attribute("id")
        if element_id and page:
            try:
                label_locator = page.locator(f'label[for="{element_id}"]').first
                label_text = await label_locator.text_content(timeout=1000)
                if label_text and label_text.strip():
                    return label_text.strip()
            except:
                pass
        
        
        if parent_label and parent_label.strip():
            return parent_label.strip()
        
        aria_describedby = await element.get_attribute("aria-describedby")
        if aria_describedby:
            try:
                if describedby_text and describedby_text.strip():
                    return describedby_text.strip()
            except:
                pass
        
        
        if preceding_text and preceding_text.strip():
            return preceding_text.strip()
            
    except Exception as e:
        print(f"  Warning: Label text discovery failed: {e}")
    
    return None

def _is_dynamic_id(id_value: str) -> bool:
    import re
    
    dynamic_patterns = [
        r'.*\d{10,}.*',
        r'.*[a-f0-9]{8}-[a-f0-9]{4}-.*',
        r'.*_ngcontent-.*',
        r'^[a-f0-9]{32}$',
        r'.*-\d{4,}$'
    ]
    
    return any(re.match(pattern, id_value, re.IGNORECASE) for pattern in dynamic_patterns)

async def _generate_stable_css_selector(page: Page, element) -> str:
    try:
        class_list = await element.get_attribute("class")
        if not class_list:
            return None
            
        classes = class_list.split()
        
        stable_classes = []
        for cls in classes:
            if not _is_dynamic_class(cls):
                stable_classes.append(cls)
        
        if not stable_classes:
            return None
        
        tag_name = await element.evaluate("el => el.tagName.toLowerCase()")
        selector = tag_name + "." + ".".join(stable_classes)
        
        count = await page.locator(selector).count()
        if count == 1:
            return selector
        elif count < 5:
            return selector
            
    except:
        pass
    
    return None

def _is_dynamic_class(class_name: str) -> bool:
    import re
    
    dynamic_patterns = [
        r'.*\d{8,}.*',
        r'.*[a-f0-9]{6,}.*',
        r'.*_[a-f0-9]+$',
        r'.*-\d{4,}$',
        r'^css-[a-z0-9]+',
        r'.*_ngcontent-.*',
        r'.*__[a-f0-9]{5,}$',
    ]
    
    return any(re.match(pattern, class_name, re.IGNORECASE) for pattern in dynamic_patterns)

async def _generate_minimal_xpath(page: Page, element) -> str:
    try:
        
        return f"xpath={xpath}"
        
    except:
        return "xpath=//body"
    

async def execute_action_with_codegen_selector(page: Page, xpath: str, action: str, text: str = None, step_info: str = ''):
    ret = await get_codegen_selector(page, xpath)
    print(f"Generated selector for {step_info}: {ret}")
    
    try:
        if ret.startswith('role='):
            if '[name=' in ret:
                role_part = ret.split('[')[0].replace('role=', '')
                name_part = ret.split('[name="')[1].split('"]')[0]
                print(f"Length of role_part: {await page.get_by_role(role_part, name=name_part, exact=True).count()}")
                locator = page.get_by_role(role_part, name=name_part, exact=True).first
            else:
                role_part = ret.replace('role=', '')
                print(f"Length of role_part: {await page.get_by_role(role_part,  exact=True).count()}")
                locator = page.get_by_role(role_part, exact=True).first
        elif ret.startswith('[data-testid='):
            test_id = ret.split('="')[1].split('"]')[0]
            print(f"Length of test_id: {await page.get_by_test_id(test_id, exact=True).count()}")
            locator = page.get_by_test_id(test_id, exact=True).first
        elif ret.startswith('placeholder='):
            placeholder = ret.split('="')[1].split('"]')[0]
            print(f"Length of placeholder: {await page.get_by_placeholder(placeholder, exact=True).count()}")
            locator = page.get_by_placeholder(placeholder, exact=True).first
        elif ret.startswith('text='):
            text_content = ret.split('="')[1].split('"]')[0]
            print(f"Length of text: {await page.get_by_text(text_content, exact=True).count()}")
            locator = page.get_by_text(text_content, exact=True).first
        elif ret.startswith('label='):
            label = ret.split('="')[1].split('"]')[0]
            print(f"Length of label: {await page.get_by_label(label, exact=True).count()}")
            locator = page.get_by_label(label, exact=True).first
        else:
            print(f"Length of ret: {await page.locator(ret).count()}")
            locator = page.locator(ret).first
        
        if action == "click":
            await locator.click()
        elif action == "fill":
            await locator.fill(text)
        
        print(f"  Action '{action}' successful with generated selector")
        
    except Exception as e:
        print(f"  Warning: Generated selector failed: {e}. Falling back to xpath...")
        await _try_locate_and_act(page, xpath, action, text, step_info)