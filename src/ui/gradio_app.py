import gradio as gr
import json
import datetime
from functools import partial  # For creating event handlers with arguments

# --- Filter Definitions (This would be extensive, loaded from config) ---
ALL_POSSIBLE_FILTERS_CONFIG = {
    "marital_status": {
        "display_name": "Marital Status",
        "control_type": "CHECKBOX",
        "options": ["Single", "Married", "Divorced", "Widowed"],
        "default_value": []
    },
    "last_contact_date": {
        "display_name": "Min Last Contact Date",
        "control_type": "DATE",
        "default_value": None
    },
    "account_balance": {
        "display_name": "Min Account Balance",
        "control_type": "NUMBER",
        "default_value": None
    },
    "client_name": {
        "display_name": "Client Name (Starts With)",
        "control_type": "TEXTBOX",
        "default_value": ""
    }
}


# --- Mock Backend Logic ---
def call_flask_backend_mock(user_query: str, current_applied_filters_from_ui: dict) -> dict:
    print(f"Mock Backend: Query: '{user_query}'")
    print(f"Mock Backend: Current UI Filters: {current_applied_filters_from_ui}")

    newly_applied_filters_for_ui = []

    def get_filter_config_for_ui(filter_name, value):
        base_config = ALL_POSSIBLE_FILTERS_CONFIG.get(filter_name)
        if not base_config: return None
        return {
            "filter_name": filter_name,
            "display_name": base_config["display_name"],
            "control_type": base_config["control_type"],
            "options": base_config.get("options"),
            "value": value
        }

    processed_filter_names_from_query = set()
    chat_message_parts = [f"Processed: '{user_query}'."]

    if "single" in user_query.lower():
        cfg = get_filter_config_for_ui("marital_status", ["Single"])
        if cfg: newly_applied_filters_for_ui.append(cfg)
        processed_filter_names_from_query.add("marital_status")
        chat_message_parts.append("Set Marital Status to Single.")
    elif "married" in user_query.lower():
        cfg = get_filter_config_for_ui("marital_status", ["Married"])
        if cfg: newly_applied_filters_for_ui.append(cfg)
        processed_filter_names_from_query.add("marital_status")
        chat_message_parts.append("Set Marital Status to Married.")

    if "balance over 5000" in user_query.lower():
        cfg = get_filter_config_for_ui("account_balance", 5000.0)
        if cfg: newly_applied_filters_for_ui.append(cfg)
        processed_filter_names_from_query.add("account_balance")
        chat_message_parts.append("Set Min Account Balance to 5000.")
    elif "balance over 10000" in user_query.lower():
        cfg = get_filter_config_for_ui("account_balance", 10000.0)
        if cfg: newly_applied_filters_for_ui.append(cfg)
        processed_filter_names_from_query.add("account_balance")
        chat_message_parts.append("Set Min Account Balance to 10000.")

    if "contacted this year" in user_query.lower():
        today = datetime.date.today()
        cfg = get_filter_config_for_ui("last_contact_date", f"{today.year}-01-01")
        if cfg: newly_applied_filters_for_ui.append(cfg)
        processed_filter_names_from_query.add("last_contact_date")
        chat_message_parts.append("Set Min Last Contact Date to start of this year.")

    if "client john" in user_query.lower():
        cfg = get_filter_config_for_ui("client_name", "John")
        if cfg: newly_applied_filters_for_ui.append(cfg)
        processed_filter_names_from_query.add("client_name")
        chat_message_parts.append("Set Client Name to start with 'John'.")

    if "reset all filters" in user_query.lower() or "clear filters" in user_query.lower():
        newly_applied_filters_for_ui = []
        processed_filter_names_from_query.update(current_applied_filters_from_ui.keys())
        chat_message_parts = ["All filters have been reset."]

    if not ("reset all filters" in user_query.lower() or "clear filters" in user_query.lower()):
        for fname, fvalue in current_applied_filters_from_ui.items():
            if fname not in processed_filter_names_from_query:
                if fname in ALL_POSSIBLE_FILTERS_CONFIG:
                    cfg = get_filter_config_for_ui(fname, fvalue)
                    if cfg: newly_applied_filters_for_ui.append(cfg)

    final_chat_message = " ".join(chat_message_parts)
    if len(chat_message_parts) == 1 and user_query and not ("reset all" in user_query or "clear filters" in user_query):
        final_chat_message = f"I received '{user_query}', but didn't identify specific filters to add/change. Current filters (if any) from UI are preserved."

    response = {
        "chat_message_to_user": final_chat_message,
        "applied_filters_ui_config": newly_applied_filters_for_ui,
        "suggestions_for_user": []
    }
    print(f"Mock Backend: Sending response: {response}")
    return response


# --- Gradio UI and Logic ---

def regenerate_filter_ui_elements_and_bind_events(
        active_filter_data: dict,
        active_filter_data_state_component: gr.State
):
    """
    Dynamically creates UI elements for active filters inside a NEW gr.Column
    and binds their events. Returns this new gr.Column.
    """
    print(f"UI Regeneration: Active Filter Data: {active_filter_data}")

    # Create a list of components that will go inside the new column
    components_for_new_column = []

    if not active_filter_data:
        components_for_new_column.append(gr.Markdown("No active filters."))
    else:
        for filter_name, current_value in active_filter_data.items():
            config = ALL_POSSIBLE_FILTERS_CONFIG.get(filter_name)
            if not config:
                print(
                    f"Warning: Filter '{filter_name}' in active_filter_data not found in ALL_POSSIBLE_FILTERS_CONFIG.")
                continue

            # Use a gr.Group or gr.Row to group filter + drop button nicely
            with gr.Group():  # Or gr.Row(variant="compact")
                filter_component = None
                label = config["display_name"]

                if config["control_type"] == "CHECKBOX":
                    filter_component = gr.CheckboxGroup(
                        label=label, choices=config["options"], value=current_value, interactive=True, scale=4
                    )
                elif config["control_type"] == "DATE":
                    filter_component = gr.Date(
                        label=label, value=current_value, interactive=True, scale=4
                    )
                elif config["control_type"] == "NUMBER":
                    filter_component = gr.Number(
                        label=label, value=current_value, interactive=True, scale=4
                    )
                elif config["control_type"] == "TEXTBOX":
                    filter_component = gr.Textbox(
                        label=label, value=current_value, interactive=True, scale=4
                    )

                if filter_component:
                    on_change_handler = partial(handle_individual_filter_value_change, filter_name=filter_name)
                    filter_component.change(
                        fn=on_change_handler,
                        inputs=[filter_component, active_filter_data_state_component],
                        outputs=[active_filter_data_state_component]
                    )
                    components_for_new_column.append(filter_component)  # Add to list

                drop_button = gr.Button("Drop", min_width=10, scale=1, variant="stop")
                on_drop_handler = partial(handle_drop_filter_button_click, filter_name_to_drop=filter_name)
                drop_button.click(
                    fn=on_drop_handler,
                    inputs=[active_filter_data_state_component],
                    outputs=[active_filter_data_state_component]
                )
                components_for_new_column.append(drop_button)  # Add to list

    if not components_for_new_column and active_filter_data:
        components_for_new_column.append(gr.Markdown("Error generating filter UI elements."))

    # CRITICAL CHANGE: Return a *new* gr.Column containing the dynamically generated components
    return gr.Column(children=components_for_new_column)  # This will replace the filters_pane_container


def handle_individual_filter_value_change(
        new_value_for_specific_filter,
        current_active_filter_data: dict,
        *,
        filter_name: str
):
    print(f"UI Value Change: Filter '{filter_name}' new value: {new_value_for_specific_filter}")
    if current_active_filter_data is None: current_active_filter_data = {}

    current_active_filter_data[filter_name] = new_value_for_specific_filter
    return current_active_filter_data


def handle_drop_filter_button_click(
        current_active_filter_data: dict,
        *,
        filter_name_to_drop: str
):
    print(f"UI Drop Click: Filter '{filter_name_to_drop}'")
    if current_active_filter_data is None: return {}

    if filter_name_to_drop in current_active_filter_data:
        del current_active_filter_data[filter_name_to_drop]

    return current_active_filter_data


def handle_chat_submit(
        user_message: str,
        chat_history: list,
        current_active_filter_data_from_state: dict
):
    if current_active_filter_data_from_state is None:
        current_active_filter_data_from_state = {}

    backend_response = call_flask_backend_mock(user_message, current_active_filter_data_from_state)

    chat_history.append((user_message, None))
    assistant_response_message = backend_response.get("chat_message_to_user", "Sorry, an error occurred.")
    chat_history.append((None, assistant_response_message))

    new_active_filter_data_for_state = {}
    backend_ui_configs = backend_response.get("applied_filters_ui_config", [])
    for filt_conf in backend_ui_configs:
        new_active_filter_data_for_state[filt_conf["filter_name"]] = filt_conf.get("value")

    return (
        chat_history,
        new_active_filter_data_for_state,
        ""
    )


theme = gr.themes.Soft(
    primary_hue=gr.themes.colors.sky,
    secondary_hue=gr.themes.colors.blue,
    neutral_hue=gr.themes.colors.slate
)

with gr.Blocks(theme=theme) as demo:
    active_filter_data_state = gr.State({})

    gr.Markdown("# LLM Filter Assistant")
    gr.Markdown(
        "Interact via chat to apply/modify filters. "
        "You can also directly edit or drop filters in the right pane. "
        "These manual changes will be considered on your next chat message."
    )

    with gr.Row():
        with gr.Column(scale=3):
            chatbot = gr.Chatbot(label="Chat Assistant", height=650, bubble_full_width=False)
            chat_input = gr.Textbox(
                label="Your Message",
                placeholder="e.g., 'single clients', 'balance over 5000', 'reset all filters'"
            )
            chat_submit_btn = gr.Button("Send Message", variant="primary")

        with gr.Column(scale=2):
            gr.Markdown("## Current Active Filters")
            filters_pane_container = gr.Column(elem_id="dynamic-filters-pane")

    active_filter_data_state.change(
        fn=regenerate_filter_ui_elements_and_bind_events,
        inputs=[active_filter_data_state, active_filter_data_state],
        outputs=[filters_pane_container]
    )


    def initial_render(initial_state_value):
        return regenerate_filter_ui_elements_and_bind_events(initial_state_value, active_filter_data_state)


    demo.load(
        fn=initial_render,
        inputs=[active_filter_data_state],
        outputs=[filters_pane_container]
    )

    chat_submit_btn.click(
        fn=handle_chat_submit,
        inputs=[chat_input, chatbot, active_filter_data_state],
        outputs=[chatbot, active_filter_data_state, chat_input]
    )
    chat_input.submit(
        fn=handle_chat_submit,
        inputs=[chat_input, chatbot, active_filter_data_state],
        outputs=[chatbot, active_filter_data_state, chat_input]
    )

if __name__ == "__main__":
    demo.launch(debug=True)