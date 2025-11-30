import streamlit as st
import json
import os
import re
from streamlit_ace import st_ace
from openai import OpenAI

from streamlit.components.v1 import html as components_html
from pygments import highlight
from pygments import lexers
from pygments import formatters
st.set_page_config(layout="wide")

# 定义存储工具配置的文件路径
config_file = "config/tools_config.json"
client = OpenAI(api_key='sk-ZfjYtt6PJWcXNJmp17071dE24dE145D3Ac0c2b9d02D73793', base_url='https://api.ai-gaochao.cn/v1')

def show_scrollable_code(code: str, language: str = "python", height: int = 420):
    """Scrollable, fixed-height code block with devtools-like font and matching backgrounds."""
    # pick lexer
    try:
        lexer = lexers.get_lexer_by_name(language, stripall=False)
    except Exception:
        try:
            lexer = lexers.guess_lexer(code)
        except Exception:
            lexer = lexers.get_lexer_by_name("text")

    # light theme
    formatter = formatters.HtmlFormatter(noclasses=True, style="friendly", linenos=False)
    highlighted = highlight(code, lexer, formatter)

    # remove any inline Pygments background so inner == outer
    highlighted = re.sub(r"background:\s*#[0-9a-fA-F]{3,6}", "background: transparent", highlighted)
    highlighted = highlighted.replace("background-color:", "background:")  # normalize

    outer_bg = "#f6f8fa"  # same for inner via CSS override
    css = f"""
    <style>
      .codebox {{
        height: {height}px;
        overflow: auto;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        background: {outer_bg};
        padding: 12px 16px;
        box-sizing: border-box;
      }}
      /* force font + colors; unify backgrounds */
      .codebox, .codebox pre, .codebox code, .codebox span, .codebox div {{
        background: transparent !important;
        color: #1a1a1a;
        font-family: 'JetBrains Mono','Fira Code','SFMono-Regular','Consolas','Menlo','Monaco','Ubuntu Mono','Courier New',monospace !important;
        font-size: 13px !important;
        line-height: 1.55;
      }}
    </style>
    """

    html_block = f"""{css}
    <div class="codebox">{highlighted}</div>
    """

    # fixed outer height equals container height (no extra blank area)
    components_html(html_block, height=height, scrolling=False)



def generate_tool_json(func_name, description):
    completion = client.chat.completions.create(
        model="o4-mini-2025-04-16",
        messages=[
                {
                    "role": "system",
                    "content": """You are a tool configuration generator. Your task is to generate a **JSON configuration** for a function based on the provided user description, only output a json data, no other word especially "```json  ```". The description will include the function's parameters, types, and their relationships, as well as any constraints on the values.

    For each function described, you must generate the following **JSON structure**:
    1. **type**: The type of the tool, which should always be "function" in this case.
    2. **function**: This section will contain details about the function being described:
        - **name**: The name of the function (e.g., "create_optimization_task").
        - **description**: A brief description of what the function does.
        - **parameters**: This will include an object where each key represents a parameter name, and the value describes the parameter's structure. Each parameter will have:
            - **type**: The data type of the parameter (e.g., "string", "number", "array", "object").
            - **properties**: The internal properties for complex data types (e.g., arrays or objects). If the parameter is an array, you will specify the type of the items inside it.
            - **description**: A description of the parameter and its role in the function.
            - **required**: A list of required parameters. These are the parameters that must be provided when calling the function.

    ### **Generalized Steps for Generating the JSON Configuration**:
    1. Identify the function's **name** and **description** based on the provided details.
    2. For each **parameter**:
       - Describe its **type** (e.g., string, number, array, object).
       - If the parameter is an **array** or **object**, describe its **items** or **properties** with further detail.
       - Provide a **description** of the parameter and its purpose in the function. Must not abbreviate the detailed description provided by the user.
       - Specify the **required** parameters if any."""
                },
                {
                    "role": "user",
                    "content": f"tool name: {func_name}, comment:{description}"}])
    res = completion.choices[0].message.content
    return json.loads(res)


# def save_tool(tool_data):
#     """保存工具配置到本地文件。"""
#     try:
#         if os.path.exists(config_file):
#             with open(config_file, "r") as file:
#                 all_tools = json.load(file)
#         else:
#             all_tools = []
#         tool_data["gen_json"] = generate_tool_json(tool_data["func_name"], tool_data["description"])
#         all_tools.append(tool_data)
#         with open(config_file, "w") as file:
#             json.dump(all_tools, file, indent=4)
#         st.success("Tool saved successfully!")
#     except Exception as e:
#         st.error(f"Error saving tool: {e}")

def save_tool(tool_data):
    """保存工具配置到本地文件。"""
    try:
        if os.path.exists(config_file):
            with open(config_file, "r") as file:
                all_tools = json.load(file)
        else:
            all_tools = []
        all_tools.append(tool_data)   # 注意：不再这里生成 JSON
        with open(config_file, "w") as file:
            json.dump(all_tools, file, indent=4)
        st.success("Tool saved successfully!")
    except Exception as e:
        st.error(f"Error saving tool: {e}")


def load_tools():
    """从本地文件加载工具配置。"""
    if os.path.exists(config_file):
        with open(config_file, "r") as file:
            return json.load(file)
    return []

def delete_tool(index):
    """删除指定索引的工具配置。"""
    try:
        tools = load_tools()
        del tools[index]
        with open(config_file, "w") as file:
            json.dump(tools, file, indent=4)
        st.success("Tool deleted successfully!")
    except Exception as e:
        st.error(f"Error deleting tool: {e}")


st.title("🧰 Tools Box")
st.caption("Manage or create callable tools for your agents. Use this page to view existing tools or define new ones by writing function code and comments — the system will auto-generate a structured JSON schema for LLM integration.")

# st.subheader("Existing Tools")


#
# # 2. 在侧边栏显示一个选择框
# if tools:
#     tool_names = [tool['func_name'] for tool in tools]
#     selected_name = st.sidebar.selectbox("Select Tool", [""] + tool_names)
# else:
#     st.sidebar.warning("No tools found")
#
# # 3. “Add Tool” 按钮保持在侧边栏底部
# with st.sidebar:
#     st.markdown("---")
#     if st.button("Add Tool"):
#         st.session_state.form_visible = True
#         st.session_state.edit_tool_idx = None
#         st.session_state.func_name = ""
#         st.session_state.description_input = ""
#         st.session_state.code_input = ""
#     if st.button("Load Tools"):
#         # 重新读取
#         tools = load_tools()
#
# # 4. 主区根据选中的名字展示内容
# if selected_name:
#     # 找到对应的工具
#     tool = next((t for t in tools if t['func_name'] == selected_name), None)
#     if tool:
#         st.subheader(f"{tool['func_name']}")
#         st.write("**Description:**")
#         st.text_area("", tool['description'], height=200, label_visibility="hidden", disabled=True)
#         st.write("**Code:**")
#         st.code(tool['code'], language="python")
#         st.write("**JSON Representation:**")
#         st.json(tool['gen_json'])
#
#         # 删除按钮
#         if st.button(f"Delete {tool['func_name']}"):
#             idx = tools.index(tool)
#             delete_tool(idx)
#             st.experimental_rerun()
# else:
#     if not tools:
#         st.warning("No tools found.")
#     else:
#         st.info("Please select a tool from the sidebar to view its details.")
#
# # 5. 添加 / 编辑 表单
# if st.session_state.get("form_visible"):
#     st.markdown("---")
#     if st.session_state.edit_tool_idx is None:
#         st.subheader("Add New Tool")
#     else:
#         st.subheader("Edit Tool")
#     with st.form("tool_form"):
#         func_name = st.text_input("Name", value=st.session_state.get("func_name", ""))
#         code_input = st_ace(
#             height=300,
#             key="code_input",
#             language="python",
#             theme="github",
#             placeholder="Enter your function code here"
#         )
#         description_input = st.text_area(
#             "Enter your comments here",
#             height=200,
#             key="description_input"
#         )
#         submit_button = st.form_submit_button("Save Tool")
#         if submit_button:
#             if func_name and code_input and description_input:
#                 tool_data = {
#                     "func_name": func_name,
#                     "code": code_input,
#                     "description": description_input
#                 }
#                 save_tool(tool_data)
#                 st.session_state.form_visible = False
#             else:
#                 st.error("Please fill in all fields.")
# st.title("Tools Box")

# tools = load_tools()

# 创建两个标签页
tab1, tab2 = st.tabs(["Existing Tools", "Add Tool"])

# -------- Tab 1: Existing Tools --------
with tab1:
    tools = load_tools()
    if tools:
        # 下拉框移到这里
        tool_names = [tool['func_name'] for tool in tools]
        selected_name = st.selectbox("Select Tool", [""] + tool_names)

        if selected_name:
            tool = next((t for t in tools if t['func_name'] == selected_name), None)
            if tool:
                st.subheader(tool['func_name'])
                st.write("**Description:**")
                st.code(tool['description'], language=None)
                # st.text_area("", tool['description'], height=200, label_visibility="hidden", disabled=True)
                st.write("**Code:**")
                show_scrollable_code(tool["code"], language="python", height=420)
                # st.code(tool['code'], language="python")
                st.write("**JSON Representation:**")
                st.json(tool['gen_json'])

                if st.button(f"Delete {tool['func_name']}"):
                    idx = tools.index(tool)
                    delete_tool(idx)
    else:
        st.warning("No tools found.")

# -------- Tab 2: Add / Edit Tool --------
with tab2:
    st.subheader("Add New Tool")


    with st.form("tool_form", clear_on_submit=False):
        func_name = st.text_input("Name", value=st.session_state.get("func_name", ""))
        code_input = st_ace(
            height=300,
            key="code_input",
            language="python",
            theme="github",
            placeholder="Enter your function code here"
        )
        st.caption("""
                Your comments should include:
        - **Function description** – one or two sentences explaining what the tool does and when it should be used.  
        - **Parameters** – list all inputs with type hints (`str`, `int`, `float`, `list`, `dict`, etc.) and clear explanations of their meanings, accepted formats, and roles.  
        - **Expected outputs** – describe what the function returns or produces, including its data type and purpose. (Optional)  
        - **Usage context** – optionally, mention what kind of task or agent would call this tool.""")
        description_input = st.text_area(
            "Enter your comments here",
            height=200,
            key="description_input"
        )

        # Step 1: 生成 JSON
        generate_btn = st.form_submit_button("Generate JSON")
        if generate_btn:
            if func_name and description_input:
                try:
                    gen_json = generate_tool_json(func_name, description_input)
                    st.session_state["pending_tool"] = {
                        "func_name": func_name,
                        "code": code_input,
                        "description": description_input,
                        "gen_json": gen_json
                    }
                    st.success("JSON generated successfully! Please review below.")
                except Exception as e:
                    st.error(f"Error generating JSON: {e}")
            else:
                st.error("Name and description are required to generate JSON.")

    # Step 2: 如果已生成，显示并提供保存按钮
    if "pending_tool" in st.session_state:
        st.markdown("### Generated JSON (check carefully)")
        st.json(st.session_state["pending_tool"]["gen_json"])

        if st.button("Save Tool"):
            save_tool(st.session_state["pending_tool"])
            # 保存后清理 session_state，避免重复保存
            del st.session_state["pending_tool"]