import time
from platform import system

import streamlit as st
from openai import OpenAI
from graphviz import Digraph
import json
import os
import html as py_html
from streamlit.components.v1 import html as components_html
from pathlib import Path
import re
import urllib.parse  # 新增：用于解析/编码 URL query


# Streamlit app layout

st.set_page_config(layout="wide")
config_file = "config/mas_config.json"


def load_mas():
    if os.path.exists(config_file):
        with open(config_file, "r", encoding='utf-8') as f:
            return json.load(f)
    return []


def modify_mas(new_mas_name, mas_template_name, user_prompt):
    with open("config/tools_config.json", "r", encoding='utf-8') as tools_file:
        tools_config = json.load(tools_file)
    with open("config/mas_config.json", "r", encoding='utf-8') as mas_file:
        mas_config = json.load(mas_file)
    base_template = None
    for item in mas_config:
        if item.get("name") == mas_template_name:
            base_template = {k: v for k, v in item.items() if k != "tools"}
            break
    tools_config_str = "\n".join([f"    - func_name: {tool['func_name']}" for tool in tools_config])

    system_prompt  = f"""\
    You are a professional MAS (Multi-Agent System) configuration editor. 
    Your task is to modify the given MAS configuration **with minimal changes** according to the user’s instructions.
    
    Modification principles:
    - Modify the name of MAS to new name.
    - Apply the **minimal necessary edits**, keeping the overall structure stable.
    - **Update and refine the manager agent’s description** for new needs
    - **If there is an evaluation worker**, review or modify its description for new needs.
    Tool assignment: you may adjust which tools are used by which workers if necessary.
    - The output **must be a valid JSON object only** — do not include explanations, comments, Markdown, or code fences.
  ⚠️ **Do NOT start the output with** ```json **or any triple backticks.**
    """
    content_prompt = f""" 
    New mas Name: {new_mas_name}
    
    USER INSTRUCTIONS:
        {user_prompt}

    MAS TEMPLATE (apply minimal edits to this structure):
        {json.dumps(base_template, ensure_ascii=False, indent=2)}

    AVAILABLE TOOLS (func_name):
    {tools_config_str}"""

    client = OpenAI(api_key='sk-ZfjYtt6PJWcXNJmp17071dE24dE145D3Ac0c2b9d02D73793',
                    base_url='https://api.ai-gaochao.cn/v1')

    completion = client.chat.completions.create(
        model="o4-mini-2025-04-16",
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": content_prompt
            }]
    )
    res = completion.choices[0].message.content
    print('/n', res)
    res = json.loads(res)

    for worker in res["worker"]:
        if "tools" in worker:
            for tool in worker["tools"]:
                tool_details = next((tc for tc in tools_config if tc["func_name"] == tool), None)
                if tool_details:
                    res.setdefault("tools", {})[tool] = tool_details.get("gen_json")

    return res

def tansfer2mas(mas_name, user_prompt):
    # time.sleep(10)
    with open("config/llm_config.json", "r", encoding='utf-8') as llm_file:
        llm_config = json.load(llm_file)

    with open("config/tools_config.json", "r", encoding='utf-8') as tools_file:
        tools_config = json.load(tools_file)

    # Define the basic prompt template
    prompt_template = """
    You are an assistant tasked with generating configurations for multi-agent systems that manage workflows in scientific or experimental tasks. These workflows involve multiple agents, each responsible for specific tasks within a larger optimization or decision-making process.

    For each multi-agent system, you must generate a configuration in JSON format, only output a json data, no other word especially "```json  ```". The configuration must include the following components (the json's key must be the following components name):

    1. **worker**: Each worker is responsible for executing specific tasks within the optimization or experiment workflow. You need to define:
       - **name**: The name of the worker.
       - **description**: A detailed description of the worker's responsibilities. This should include an overview of the worker's role and which tools it utilizes. If the worker is assigned multiple tasks, each task should be explicitly linked to the tool it uses. If the user has provided detailed descriptions of the worker (especially, evaluate worker), generate their description with as much detail as possible, making sure not to shorten the provided principles.
       - **llm**: The llm name this agent based on.
       - **tools**: A list of tools this worker has access to. If not use an tools, don't generate tool key.
       - **max_output**: A number of max output words (default 50). If not use an tools, don't generate tool key, generate max_output key. If use tools, don't generate this key.

    2. **task**: Tasks represent actions within the workflow. You need to define:
       - **name**: The name of the task.
       - **description**: A description of what the task is and what it accomplishes. This should include how the task contributes to the overall optimization or experimental process.
       - **worker**: The worker responsible for performing this task. Each task should be assigned to the appropriate worker based on the tools required to perform the task.

    3. **manager**: The manager oversees the entire workflow and coordinates tasks. You need to define:
       - **name**: The name of the manager.
       - **description**: Write the manager description as a concrete orchestration plan. Describe exactly how the manager sequences and controls tasks in this workflow, including ordering, iterations, and decision branches.
        - **llm**: The llm name this agent based on.
       - **tasks**: A list of tasks the manager oversees, in the order they should be executed. The manager should handle task sequencing to ensure efficient execution and optimal resource allocation.

    4. **llm**: The LLM configuration used for the worker and manager (a list of dict). Define the following attributes for the LLM:
       - **name**: The name of the LLM.
       - **api_key**: The API key used to access the LLM.
       - **base_url**: The base URL for the LLM API.
       - **model**: The model version or name that the LLM uses.

    5. **name**: The name of the MAS.
    
    All the "name" (except mas name) can not have space.
    
    Try your best to merge only similar tasks into the same worker.
    If two or more tools are used for related tasks of the same type (for example, both are extraction tools, both are analysis tools, or both are design tools), they should belong to one worker.
    If the tools are for different purposes (for example, extraction vs generation vs evaluation), they should be assigned to different workers.
    Normally, one worker can contain at most two tasks(tools) — this is the default and strongly preferred setup.
    In the description of any multi-tool worker, clearly write the mapping between each task and the tool it uses, like:
    “When task is <TaskNameA>, use <ToolA>; when task is <TaskNameB>, use <ToolB>.”   
    The goal is to make each worker handle a coherent group of similar tasks, rather than mixing unrelated functions together.

    **If the user has provided detailed descriptions for the worker (especially, evaluate worker), generate their description with as much detail as possible, making sure not to shorten the provided principles.**

    """

    # Insert LLM configuration into the prompt
    llm_config_str = "\n".join([
                                   f"    - name: {llm['name']}\n      api_key: {llm['api_key']}\n      base_url: {llm['base_url']}\n      model: {llm['model']}"
                                   for llm in llm_config])

    # Insert Tools configuration into the prompt
    tools_config_str = "\n".join([f"    - func_name: {tool['func_name']}" for tool in tools_config])

    # Combine everything into a final prompt
    final_prompt = prompt_template + f"\nThe new name of mas is {mas_name}\n" + f"\nThe llm you can choose is \n {llm_config_str}\n, the tools you can choose is \n {tools_config_str}."


    client = OpenAI(api_key='sk-ZfjYtt6PJWcXNJmp17071dE24dE145D3Ac0c2b9d02D73793',
                    base_url='https://api.ai-gaochao.cn/v1')

    completion = client.chat.completions.create(
        model="o4-mini-2025-04-16",
        messages=[
            {
                "role": "system",
                "content": final_prompt
            },
            {
                "role": "user",
                "content": "This is the description user provide: " + user_prompt
            }]
    )
    res = completion.choices[0].message.content
    print(res)
    res = json.loads(res)

    for worker in res["worker"]:
        if "tools" in worker:
            for tool in worker["tools"]:
                tool_details = next((tc for tc in tools_config if tc["func_name"] == tool), None)
                if tool_details:
                    res.setdefault("tools", {})[tool] = tool_details.get("gen_json")


    return res


def save_mas(mas_data):
    if os.path.exists(config_file):
        with open(config_file, "r", encoding="utf-8") as f:
            all_mas = json.load(f)
    else:
        all_mas = []
    all_mas.append(mas_data)
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(all_mas, f, indent=4)
    st.success("MAS saved successfully!")


# ========= 新增：在选中的 MAS 中更新被编辑节点 =========
def _save_all_mas(all_mas):
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(all_mas, f, ensure_ascii=False, indent=4)


def update_node_in_mas(mas_obj: dict, target: str, node_id: str, value: dict) -> bool:
    if target == "manager":
        mas_obj["manager"] = value
        return True
    if target == "task":
        for i, t in enumerate(mas_obj.get("task", [])):
            if t.get("name") == node_id:
                mas_obj["task"][i] = value
                return True
        return False
    if target == "worker":
        for i, w in enumerate(mas_obj.get("worker", [])):
            if w.get("name") == node_id:
                mas_obj["worker"][i] = value
                return True
        return False
    if target == "tool":
        tools_map = mas_obj.setdefault("tools", {})
        if node_id in tools_map:
            tools_map[node_id] = value
            return True
        return False
    return False


# ---- Mermaid 渲染函数 ----
def render_mermaid(mas, selected_mas_name=None):
    def safe_id(name: str) -> str:
        return re.sub(r"[^0-9a-zA-Z_]", "_", name)

    lines = ["flowchart LR"]
    mid = safe_id(mas["manager"]["name"])

    lines.append(f'{mid}(["{mas["manager"]["name"]}"])')
    lines.append(f'click {mid} nodeClickCallback "{mas["manager"]["name"]}"')

    for t in mas["task"]:
        tid, wid = safe_id(t["name"]), safe_id(t["worker"])
        lines += [
            f'{tid}(["{t["name"]}"]):::task',
            f'{wid}(["{t["worker"]}"]):::worker',
            f"{mid} --> {tid}",
            f"{tid} --> {wid}",
            f'click {tid} nodeClickCallback "{t["name"]}"',
            f'click {wid} nodeClickCallback "{t["worker"]}"',
        ]
    for w in mas["worker"]:
        for tool in w.get("tools", []):
            toid = safe_id(tool)
            lines += [
                f'{toid}(["{tool}"]):::tool',
                f"{safe_id(w['name'])} --> {toid}",
                f'click {toid} nodeClickCallback "{tool}"',
            ]
    lines += [
        "classDef manager fill:#FFD1DC,stroke:#E75480,stroke-width:1px,color:#000000",
        "classDef task    fill:#E0F7FA,stroke:#00ACC1,stroke-width:1px,color:#000000",
        "classDef worker  fill:#FFF3CD,stroke:#C9A93B,stroke-width:1px,color:#000000",
        "classDef tool    fill:#E8F5E9,stroke:#6FA86C,stroke-width:1px,color:#000000",
        f"class {mid} manager",
        *[f"class {safe_id(t['name'])} task" for t in mas["task"]],
        *[f"class {safe_id(w['name'])} worker" for w in mas["worker"]],
        *[f"class {safe_id(tool)} tool"
          for w in mas["worker"] for tool in w.get("tools", [])],
    ]
    mermaid_code = "\n".join(lines)
    payload = {
        "manager": mas["manager"],
        "task": mas["task"],
        "worker": mas["worker"],
        "tools": mas.get("tools", {}),
    }
    payload_json = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")

    html_mermaid = py_html.escape(mermaid_code)
    mermaid_local_js = Path("assets/js/mermaid.min.js").read_text(encoding="utf-8")
    prism_js = Path("assets/js/prism.js").read_text(encoding="utf-8")
    prism_json_js = Path("assets/js/prism-json.min.js").read_text(encoding="utf-8")
    prism_css = Path("assets/css/prism.css").read_text(encoding="utf-8")
    # ===== 替换详情区：直接在多彩窗口中编辑 =====
    html_content = f"""
    <div style="border:1px solid #e5e7eb;border-radius:12px;padding:12px">
      <pre class="mermaid" style="margin:0">{html_mermaid}</pre>
    </div>

    <div id="details" style="margin-top:16px;padding:16px;border:1px solid #e5e7eb;border-radius:12px;">
      <div id="details-head" style="font-weight:600;margin-bottom:8px;">Click a node to view & edit</div>

      <div style="margin-bottom:8px;display:flex;gap:8px;flex-wrap:wrap;">
        <button id="btn-edit"   style="padding:6px 10px;border-radius:8px;border:1px solid #e5e7eb;background:#f8f9fa;">Edit</button>
        <button id="btn-format" style="padding:6px 10px;border-radius:8px;border:1px solid #e5e7eb;background:#f8f9fa;">Format</button>
        <button id="btn-save"   style="padding:6px 10px;border-radius:8px;border:1px solid #e5e7eb;background:#e8f5e9;">Save</button>
        <button id="btn-cancel" style="padding:6px 10px;border-radius:8px;border:1px solid #e5e7eb;background:#fff;">Cancel</button>
        <span id="save-status"  style="margin-left:6px;color:#4b5563;"></span>
      </div>

      <div id="details-body"></div>
    </div>

    <style>{prism_css}</style>
    <script>{prism_js}</script>
    <script>{prism_json_js}</script>

    <script>
    {mermaid_local_js}
    mermaid.initialize({{ startOnLoad: false, securityLevel: 'loose', theme: 'default' }});
    mermaid.run({{ querySelector: '.mermaid' }});

    const MAS_NAME = {json.dumps(selected_mas_name or mas.get("name", ""))};
    const payload = {payload_json};

    let currentTarget = null; // 'manager' | 'task' | 'worker' | 'tool'
    let currentId = null;
    let currentObj = null;
    let isEditing = false;
    function renderPreview(obj, editable=false) {{
      const body = document.getElementById('details-body');

      while (body.firstChild) {{
        body.removeChild(body.firstChild);
      }}

      const pre = document.createElement('pre');
      pre.style.margin = '0';
      pre.style.background = '#f8f9fa';
      pre.style.borderRadius = '8px';
      pre.style.padding = '12px';
      pre.style.fontFamily = "'Fira Code','Courier New',monospace";
      pre.style.fontSize = '13px';
      pre.style.overflowX = 'auto';

      const code = document.createElement('code');
      code.id = 'details-code';
      code.style.whiteSpace = 'pre-wrap';
      code.style.wordBreak = 'break-word';
      code.style.overflowWrap = 'anywhere';

      if (typeof isEditing === 'undefined') {{
        window.isEditing = false;
      }}

      if (editable) {{
        code.textContent = JSON.stringify(obj, null, 2);
        code.setAttribute('contenteditable', 'true');
        code.setAttribute('spellcheck', 'false');
        isEditing = true;
      }} else {{
        code.className = 'language-json';
        code.textContent = JSON.stringify(obj, null, 2);
        if (window.Prism) {{
          if (typeof Prism.highlightElement === 'function') {{
            Prism.highlightElement(code);
          }} else if (typeof Prism.highlightAll === 'function') {{
            Prism.highlightAll();
          }}
        }}
        isEditing = false;
      }}

      pre.appendChild(code);
      body.appendChild(pre);

      const status = document.getElementById('save-status');
      if (status) status.textContent = '';
    }}

        window.nodeClickCallback = function(id) {{
          const head = document.getElementById('details-head');

          if (payload.manager.name === id) {{
            currentTarget = 'manager'; currentId = id; currentObj = payload.manager;
            head.textContent = 'Manager';
          }} else if (payload.task.find(x => x.name === id)) {{
            currentTarget = 'task'; currentId = id; currentObj = payload.task.find(x => x.name === id);
            head.textContent = 'Task — ' + id;
          }} else if (payload.worker.find(x => x.name === id)) {{
            currentTarget = 'worker'; currentId = id; currentObj = payload.worker.find(x => x.name === id);
            head.textContent = 'Worker — ' + id;
          }} else if (payload.tools[id]) {{
            currentTarget = 'tool'; currentId = id; currentObj = payload.tools[id];
            head.textContent = 'Tool — ' + id;
          }} else {{
            currentTarget = null; currentId = null; currentObj = null;
            head.textContent = 'Not Found';
            document.getElementById('details-body').innerHTML = '';
            return;
          }}
          renderPreview(currentObj, /*editable=*/false);
        }};

        document.getElementById('btn-edit').onclick = function() {{
          if (!currentObj) return;
          renderPreview(currentObj, /*editable=*/true);
        }};

    document.getElementById('btn-format').onclick = function() {{
      const status = document.getElementById('save-status');
      const code = document.getElementById('details-code');
      if (!isEditing || !code) return;
      try {{
        const obj = JSON.parse(code.innerText);
        code.innerText = JSON.stringify(obj, null, 2);
        status.textContent = 'Formatted.';
        status.style.color = '#4b5563';
        setTimeout(()=>{{status.textContent='';}}, 1200);
      }} catch(e) {{
        status.textContent = 'Invalid JSON: ' + e.message;
        status.style.color = '#b91c1c';
      }}
    }};

    document.getElementById('btn-cancel').onclick = function() {{
      if (!currentObj) return;
      renderPreview(currentObj, /*editable=*/false);
    }};

    document.getElementById('btn-save').onclick = function() {{
      const status = document.getElementById('save-status');
      if (!currentTarget || !currentId) {{
        status.textContent = 'No node selected.';
        status.style.color = '#b91c1c';
        return;
      }}
      const code = document.getElementById('details-code');
      const text = isEditing ? code.innerText : code.textContent;
      try {{
        const val = JSON.parse(text);
        currentObj = val;

        const payloadToSave = {{
          mas_name: MAS_NAME,
          target: currentTarget,
          id: currentId,
          value: val
        }};
        const enc = encodeURIComponent(JSON.stringify(payloadToSave));
        const url = new URL(window.parent.location.href);
        url.searchParams.set('mas_save_payload', enc);
        url.searchParams.set('mas_save_nonce', Date.now().toString());
        window.parent.history.replaceState({{}}, '', url.toString());
        status.textContent = 'Save requested...';
        status.style.color = '#4b5563';
      }} catch (e) {{
        status.textContent = 'Invalid JSON: ' + e.message;
        status.style.color = '#b91c1c';
      }}
    }};
    </script>
    """

    left, right = st.columns([5, 1], gap="small")
    with left:
        components_html(html_content, height=740, scrolling=True)
    with right:
        st.markdown(
            """
            <div style="padding:6px 0;">
              <span style="background-color:#FFD1DC;border-radius:8px;padding:4px 8px;">Manager</span>
            </div>
            <div style="padding:6px 0;">
              <span style="background-color:#E0F7FA;border-radius:8px;padding:4px 8px;">Task</span>
            </div>
            <div style="padding:6px 0;">
              <span style="background-color:#FFF3CD;border-radius:8px;padding:4px 8px;">Worker</span>
            </div>
            <div style="padding:6px 0;">
              <span style="background-color:#E8F5E9;border-radius:8px;padding:4px 8px;">Tool</span>
            </div>
            """,
            unsafe_allow_html=True,
        )


st.title("🤖 Multi-Agent System")
st.caption("""
Create, view, and modify multi-agent workflows.  
Each MAS defines how managers, workers, and tools interact to complete complex tasks autonomously.  
Use **Add MAS** to generate a new workflow from selected tools, **Modify MAS** to update task links or logic, and **Existing MAS** to visualize or inspect current configurations.
""")
tab_existing, tab_add, tab_modify = st.tabs(["Existing MAS", "Add MAS", "Modify MAS"])

# =================== Existing MAS ===================
with tab_existing:
    # ===== 新增：处理来自前端的保存请求 =====
    qp = st.query_params
    if "mas_save_payload" in qp:
        try:
            raw = qp.get("mas_save_payload")
            payload_save = json.loads(urllib.parse.unquote(raw))
            mas_name = payload_save.get("mas_name")
            target = payload_save.get("target")
            node_id = payload_save.get("id")
            value = payload_save.get("value")

            all_mas = load_mas()
            found = False
            for i, m in enumerate(all_mas):
                if m.get("name") == mas_name:
                    ok = update_node_in_mas(m, target, node_id, value)
                    if ok:
                        all_mas[i] = m
                        _save_all_mas(all_mas)
                        st.success(f"Saved: [{mas_name}] {target} — {node_id}")
                    else:
                        st.error(f"Target not found in MAS: {target} — {node_id}")
                    found = True
                    break
            if not found:
                st.error(f"MAS '{mas_name}' not found.")
        except Exception as e:
            st.error(f"Failed to save (parse error): {e}")

        st.query_params.clear()
        st.rerun()
    # ===== 正常渲染 =====
    all_mas = load_mas()
    names = [m["name"] for m in all_mas]
    if names:
        chosen = st.selectbox("Select MAS to view", names)
        mas_data = next(m for m in all_mas if m["name"] == chosen)
        render_mermaid(mas_data, selected_mas_name=chosen)
    else:
        st.info("No MAS available.")
    st.caption("""
    #### Editing Guide

    1. **Click a Node** — Select any node (Manager, Task, Worker, or Tool) in the diagram to view its JSON details.  

    2. **Edit** — Switches the JSON view into an editable mode.  
       ⚠️ *Only the `"description"` field is allowed to be modified.* Do not change `"name"`, `"llm"`, `"tools"`, or other structural keys.  

    3. **Format** — Beautifies the JSON layout for better readability while keeping the same content.  

    4. **Save** — Validates your edit and saves it back to the MAS configuration file if the JSON is valid.  

    5. **Cancel** — Discards unsaved edits and restores the last saved version.
    """)

# =================== Add MAS ===================
with tab_add:
    st.subheader("Add New MAS")
    st.caption("""
    Write a clear description that defines the purpose, logic, and execution order of your Multi-Agent System.  
    Describe when and how each function or tool should be called, the conditions for transitions between stages, and the evaluation or termination criteria.  
    Keep it procedural and explicit — the prompt should serve as a step-by-step instruction for agents to follow autonomously.
    """)
    name = st.text_input("MAS Name")
    prompt = st.text_area("MAS Description / Prompt", height=300)

    if st.button("Generate Preview"):
        if name and prompt:
            st.session_state["pending_add"] = tansfer2mas(name, prompt)
        else:
            st.error("Please fill all fields.")

    if "pending_add" in st.session_state:
        st.markdown("### Preview Mermaid & JSON")
        render_mermaid(st.session_state["pending_add"])
        st.json(st.session_state["pending_add"])

        if st.button("Save MAS"):
            save_mas(st.session_state["pending_add"])
            del st.session_state["pending_add"]

# -------- Modify MAS --------
with tab_modify:
    all_mas = load_mas()
    if not all_mas:
        st.warning("No MAS to modify.")
    else:
        template_name = st.selectbox("Select template MAS:", [m["name"] for m in all_mas])
        new_name = st.text_input("New MAS Name")
#         template = """Design Space Expansion:
# If all variables are categorical:
# If the optimal conditions consistently fall within one category, do not expand immediately; instead refine within that category.
# If none of the categories produce satisfactory performance, or if all categories show similar performance without improvement, consider expanding by introducing new categorical options (e.g., new ligands, bases, solvents).
#
# call get_next_exps_llm (use the LLM-based optimizer instead of Bayesian optimization) to propose the candidate experimental conditions."""
        feedback = st.text_area("Modification feedback / new description", height=300)

        if st.button("Generate Modified MAS"):
            if new_name and feedback:
                st.session_state["pending_modify"] = modify_mas(new_name, template_name, feedback)
            else:
                st.error("Provide new name and feedback.")

        if "pending_modify" in st.session_state:
            st.markdown("### Modified MAS")
            render_mermaid(st.session_state["pending_modify"])
            if st.button("Save Modified MAS"):
                save_mas(st.session_state["pending_modify"])
                del st.session_state["pending_modify"]
