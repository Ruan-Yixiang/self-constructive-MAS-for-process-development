# import streamlit as st
# import json
# import os
#
# # Define file path for storing config
# config_file = "config/llm_config.json"
#
#
# def save_config(config_data):
#     """Save configuration to a local file."""
#     try:
#         # Load existing configurations
#         if os.path.exists(config_file):
#             with open(config_file, "r") as file:
#                 all_configs = json.load(file)
#         else:
#             all_configs = []
#
#         # Append the new config
#         all_configs.append(config_data)
#
#         # Save to the file
#         with open(config_file, "w") as file:
#             json.dump(all_configs, file, indent=4)
#
#         st.success("Configuration saved successfully!")
#     except Exception as e:
#         st.error(f"Error saving configuration: {e}")
#
#
# def load_config():
#     """Load configuration from the local file."""
#     if os.path.exists(config_file):
#         with open(config_file, "r") as file:
#             return json.load(file)
#     return []
#
#
# def delete_config(index):
#     """Delete a configuration from the list."""
#     try:
#         all_configs = load_config()
#         del all_configs[index]
#         with open(config_file, "w") as file:
#             json.dump(all_configs, file, indent=4)
#         st.success("Configuration deleted successfully!")
#     except Exception as e:
#         st.error(f"Error deleting configuration: {e}")
#
#
# def update_config(index, new_data):
#     """Edit a configuration in the list."""
#     try:
#         all_configs = load_config()
#         all_configs[index] = new_data
#         with open(config_file, "w") as file:
#             json.dump(all_configs, file, indent=4)
#         st.success("Configuration updated successfully!")
#     except Exception as e:
#         st.error(f"Error updating configuration: {e}")
#
#
# st.title("LLM Configuration Page")
#
# # Display the Existing Configurations
# all_configs = load_config()
# if all_configs:
#     st.subheader("Existing LLMs")
#     for idx, config in enumerate(all_configs):
#         st.markdown(f"### {config['name']}")
#         st.write(f"**API Key:** {config.get('api_key', 'Not provided')}")
#         st.write(f"**Base URL:** {config['base_url']}")
#         st.write(f"**Model:** {config['model']}")
#
#         col1, col2 = st.columns([1, 2])
#         with col1:
#             if st.button(f"Edit {config['name']}", key=f"edit_{idx}"):
#                 st.session_state.edit_config_idx = idx
#                 st.session_state.form_visible = True
#                 st.session_state.name = config['name']
#                 st.session_state.api_key = config.get('api_key', '')
#                 st.session_state.base_url = config['base_url']
#                 st.session_state.model = config['model']
#         with col2:
#             if st.button(f"Delete {config['name']}", key=f"delete_{idx}"):
#                 delete_config(idx)
# else:
#     st.warning("No configurations found.")
#
# # Sidebar buttons
# with st.sidebar:
#     if st.button("Add New LLM"):
#         # Clear the form when adding new LLM
#         st.session_state.form_visible = True
#         st.session_state.edit_config_idx = None  # Clear any previous edit state
#         st.session_state.name = ""
#         st.session_state.api_key = ""
#         st.session_state.base_url = ""
#         st.session_state.model = ""
#
#     if st.button("Load LLMs"):
#         # Load the configurations when clicked
#         all_configs = load_config()
#
#
# # Input fields for the new configuration or editing
# if "form_visible" in st.session_state and st.session_state.form_visible:
#     if st.session_state.edit_config_idx is None:
#         st.subheader("Add New LLM")
#     else:
#         st.subheader("Edit LLM")
#
#     with st.form("config_form"):
#         # Input fields to enter configuration
#         name = st.text_input("Name", value=st.session_state.get("name", ""))
#         api_key = st.text_input("API Key", type="password", value=st.session_state.get("api_key", ""))
#         base_url = st.text_input("Base URL", value=st.session_state.get("base_url", ""))
#         model = st.text_input("Model", value=st.session_state.get("model", ""))
#
#         submit_button = st.form_submit_button(label="Save Configuration")
#
#         if submit_button:
#             if name and base_url and model:
#                 config_data = {
#                     "name": name,
#                     "base_url": base_url,
#                     "model": model
#                 }
#                 if api_key:  # Only add api_key if provided
#                     config_data["api_key"] = api_key
#
#                 if st.session_state.edit_config_idx is not None:
#                     # Update the existing configuration
#                     update_config(st.session_state.edit_config_idx, config_data)
#                 else:
#                     # Save the new configuration
#                     save_config(config_data)
#
#                 # Reset form visibility and clear session state
#                 st.session_state.form_visible = False
#                 st.session_state.edit_config_idx = None
#                 st.session_state.name = ""
#                 st.session_state.api_key = ""
#                 st.session_state.base_url = ""
#                 st.session_state.model = ""
#                 # Reload configurations
#                 all_configs = load_config()
#                 st.success(
#                     f"Configuration for {name} has been {'updated' if st.session_state.edit_config_idx is not None else 'added'}.")



import streamlit as st
import json, os
from pathlib import Path

st.set_page_config(layout="wide")

config_file = Path("config/llm_config.json")
config_file.parent.mkdir(parents=True, exist_ok=True)

# ---------- helpers ----------
def load_config():
    if config_file.exists():
        with open(config_file, "r") as f:
            return json.load(f)
    return []

def save_config(cfg):
    data = load_config()
    data.append(cfg)
    with open(config_file, "w") as f:
        json.dump(data, f, indent=4)
    st.success("Configuration saved.")

def update_config(idx, cfg):
    data = load_config()
    data[idx] = cfg
    with open(config_file, "w") as f:
        json.dump(data, f, indent=4)
    st.success("Configuration updated.")

def delete_config(idx):
    data = load_config()
    del data[idx]
    with open(config_file, "w") as f:
        json.dump(data, f, indent=4)
    st.success("Configuration deleted.")


# ---------- UI ----------
st.title("🧠 LLM Configuration")
st.caption("Add or view your LLM settings here. Use this page to manage model name, API key, base URL, and version.")


tab_manage, tab_load = st.tabs(["Add", "Load"])

# -------- Manage Tab: always show Add form --------
with tab_manage:
    st.subheader("Add New LLM")
    with st.form("add_form"):
        name  = st.text_input("Name")
        api   = st.text_input("API Key", type="password")
        base  = st.text_input("Base URL")
        model = st.text_input("Model")
        if st.form_submit_button("Save"):
            if name and base and model:
                cfg = {"name": name, "base_url": base, "model": model}
                if api:
                    cfg["api_key"] = api
                save_config(cfg)
            else:
                st.error("Name, Base URL and Model are required.")

# -------- Load Tab --------
with tab_load:
    configs = load_config()

    names = [c["name"] for c in configs]
    selected = st.selectbox("Select LLM", names)

    idx = names.index(selected)
    c = configs[idx]

    # ---- Display basic info ----
    st.write(f"**Base URL:** {c['base_url']}")
    st.write(f"**Model:** {c['model']}")
    st.write(f"**API Key:** {c.get('api_key', 'Not provided')}")

    # ---- Inline edit form ----
    st.markdown("---")
    st.subheader("Edit This Configuration")
    with st.form(f"edit_form_{idx}"):
        name  = st.text_input("Name", value=c["name"])
        api   = st.text_input("API Key", type="password",
                              value=c.get("api_key", ""))
        base  = st.text_input("Base URL", value=c["base_url"])
        model = st.text_input("Model", value=c["model"])
        if st.form_submit_button("Update"):
            if name and base and model:
                new_cfg = {"name": name, "base_url": base, "model": model}
                if api:
                    new_cfg["api_key"] = api
                update_config(idx, new_cfg)
                st.experimental_set_query_params()  # refresh view
            else:
                st.error("Name, Base URL and Model are required.")

    # ---- Delete button ----
    st.markdown("---")
    if st.button("Delete This Configuration", type="primary"):
        delete_config(idx)
