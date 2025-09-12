import json
from copy import deepcopy

def process_file(file_path):
    with open(file_path, "r") as f:
        json_history = json.load(f)

    history = json_history["history"]

    parsed_history = []
    unmodified_action_list = []
    action_list = []

    for item in history:
        model_output = item["model_output"]
        result = item["result"]
        state = item["state"]

        parsed_item = {"model_output": model_output, "result": result, "state": state}

        parsed_history.append(parsed_item)

        # Skip processing if model_output is None
        if model_output is None:
            continue

        for i, action in enumerate(model_output["action"]):
            if len(action_list) > 0 and action == unmodified_action_list[-1]:
                continue
            
            if action.get("input_text", None):
                if state["interacted_element"][i]:
                    unmodified_action_list.append(deepcopy(action))
                    action["input_text"]["xpath"] = state["interacted_element"][i][
                        "xpath"
                    ]
                    action["input_text"]["css_selector"] = state["interacted_element"][i]["css_selector"]
                    if "attributes" in state["interacted_element"][i]:
                        action["input_text"]["attributes"] = state["interacted_element"][i]["attributes"]
                    action_list.append(action)

            elif action.get("click_element_by_index", None):
                if state["interacted_element"][i]:
                    unmodified_action_list.append(deepcopy(action))
                    action["click_element_by_index"]["xpath"] = state[
                        "interacted_element"
                    ][i]["xpath"]
                    action["click_element_by_index"]["css_selector"] = state[
                        "interacted_element"
                    ][i]["css_selector"]
                    if "attributes" in state["interacted_element"][i]:
                        action["click_element_by_index"]["attributes"] = state["interacted_element"][i]["attributes"]
                    action_list.append(action)

            elif action.get("select_dropdown_option", None):
                if state["interacted_element"][i]:
                    unmodified_action_list.append(deepcopy(action))
                    action["select_dropdown_option"]["xpath"] = state[
                        "interacted_element"
                    ][i]["xpath"]
                    action["select_dropdown_option"]["css_selector"] = state[
                        "interacted_element"
                    ][i]["css_selector"]
                    if "attributes" in state["interacted_element"][i]:
                        action["select_dropdown_option"]["attributes"] = state["interacted_element"][i]["attributes"]
                    action_list.append(action)
            else:
                if action.get("wait", None) and action_list[-1].get("wait", None):
                    continue
                else:
                    if action.get("extract_content", None) == None:
                        unmodified_action_list.append(deepcopy(action))
                    action_list.append(action)

    return parsed_history, action_list
