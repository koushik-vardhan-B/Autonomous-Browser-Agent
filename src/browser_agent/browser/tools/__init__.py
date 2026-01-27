
from .base import SOM_STATE, get_som_state, set_som_state
from .vision import enable_vision_overlay, find_element_ids, get_interactive_elements, get_accessibility_tree
from .extraction import get_page_text, extract_text_from_selector, extract_attribute_from_selector, get_visible_input_fields
from .interaction import (
    click_id, fill_id, click_element, fill_element, 
    press_key, upload_file_by_id, hover_element,
    select_dropdown_option, open_dropdown_and_select, select_native_select_option
)
from .navigation import scroll_one_screen, scroll_to_bottom

# All tools in one list - useful for passing to an agent
ALL_TOOLS = [
    enable_vision_overlay,
    find_element_ids,
    get_interactive_elements,
    get_accessibility_tree,
    get_page_text,
    extract_text_from_selector,
    extract_attribute_from_selector,
    get_visible_input_fields,
    click_id, 
    fill_id,
    click_element,
    fill_element,
    press_key,
    upload_file_by_id,
    hover_element,
    select_dropdown_option,
    open_dropdown_and_select,
    select_native_select_option,
    scroll_one_screen,
    scroll_to_bottom,
]