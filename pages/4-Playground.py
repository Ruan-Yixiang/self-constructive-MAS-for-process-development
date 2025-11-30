import streamlit as st
import os
import json
import re
from streamlit_autorefresh import st_autorefresh
from graphviz import Digraph
import sys
import threading
import os
from streamlit.components.v1 import html as components_html
import html as py_html
from pathlib import Path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from run import load, run

# Configuration file path
st.set_page_config(layout="wide")
st_autorefresh(interval=2000, key="autofresh")
st.title("🧩 Playground")
st.caption("""
Test and visualize your Multi-Agent System (MAS) to handle complex chemical tasks.  
Use **Flow Chart** to visualize the MAS you select (monitor reasoning steps, or provide real-time feedback during execution), and switch to **Conversation** to give your task prompt to the selected MAS.""")

mas_config_file = "config/mas_config.json"
memory_file_directory = "memory"  # Directory where the memory files are stored

# --- NEW: File-saving utility ---
from hashlib import sha256

DATA_DIR = Path(os.getenv("APP_DATA_DIR", Path(__file__).resolve().parent.parent / "Documents_uploads")).resolve()
DATA_DIR.mkdir(parents=True, exist_ok=True)

def save_uploaded_file(u) -> Path:
    """
    Save uploaded file to ./data/uploads/ (or $APP_DATA_DIR/uploads).
    Returns absolute Path.
    """
    raw = u.read()
    tag = sha256(raw).hexdigest()[:16]
    stem = Path(u.name).stem
    suffix = Path(u.name).suffix or ""
    out = DATA_DIR / f"{stem}__{tag}{suffix}"
    with open(out, "wb") as f:
        f.write(raw)
    return out


# Function to load MAS configuration
def load_mas():
    if os.path.exists(mas_config_file):
        with open(mas_config_file, "r", encoding='utf-8') as f:
            return json.load(f)
    return []

# Function to simulate loading conversation memory from a file
def load_memory(flow_id):
    # flow_id = "cb894bf2-3fb4-4fea-a822-ce87c62f9773"
    memory_file_path = os.path.join(memory_file_directory, f"{flow_id}.json")
    if os.path.exists(memory_file_path):
        with open(memory_file_path, "r", encoding='utf-8') as f:
            return json.load(f)
    return []

# Function to generate an ID (you can customize the logic here)
def generate_id(mas_name, user_input):
    flow_id = load(mas_name, user_input)

    return flow_id  # Replace with actual ID generation logic

# Load MAS data
mas_data = load_mas()

# Sidebar setup
st.sidebar.button("New Chat")

# Top section to select MAS and display configuration
options = [""] + [m["name"] for m in mas_data]

selected = st.selectbox(
    "Select MAS",
    options,
    index=0,
    key="mas_selected"
)

if 'flow_id' not in st.session_state:
    st.session_state.flow_id = None

if 'user_input' not in st.session_state:
    st.session_state.user_input = ""

if 'memory_data' not in st.session_state:
    st.session_state.memory_data = None

tab1, tab2 = st.tabs(["Flow Chart", "Conversation"])

# Tab 1: Display conversation from memory
with tab2:
    if selected:
        # --- File upload area inside Conversation tab ---
        st.markdown("### 📎 Upload File for This Conversation")
        uploaded_file = st.file_uploader(
            "Drag and drop or select a file (PDF / TXT / MD)",
            type=["pdf", "txt", "md"],
            accept_multiple_files=False,
            key="file_in_conversation"
        )

        if uploaded_file is not None:
            saved_path = save_uploaded_file(uploaded_file)
            st.success(f"✅ File saved to: `{saved_path}`")
            st.session_state["uploaded_file_path"] = str(saved_path)

            # Optional: quick preview
            ext = saved_path.suffix.lower()
            if ext == ".pdf":
                try:
                    from pypdf import PdfReader

                    reader = PdfReader(str(saved_path))
                    preview = []
                    for page in reader.pages[:2]:
                        preview.append(page.extract_text() or "")
                    st.text_area("📖 Preview (first two pages)", "\n".join(preview)[:2000], height=240)
                except Exception as e:
                    st.info(f"(Preview requires pypdf. Install via `pip install pypdf`. Error: {e})")

            elif ext in [".txt", ".md"]:
                try:
                    with open(saved_path, "r", encoding="utf-8", errors="ignore") as f:
                        text = f.read(2000)
                    if ext == ".md":
                        st.markdown("---")
                        st.markdown(text)  # Render Markdown
                    else:
                        st.text_area("📄 Preview (first 2000 chars)", text, height=240)
                except Exception as e:
                    st.warning(f"Unable to preview text file: {e}")
        # --- END of upload area ---

        # Manage flow_id and user input states
        if st.session_state.flow_id:
            flow_id = st.session_state.flow_id
        else:
            flow_id = None

        if not st.session_state.user_input:
            user_input = st.chat_input("Type your message here...")
            st.session_state.user_input = user_input
        else:
            user_input = st.session_state.user_input

        # --- NEW: append uploaded file path into the current user input ---
        if user_input and st.session_state.get("uploaded_file_path"):
            from pathlib import Path

            path_str = Path(st.session_state["uploaded_file_path"]).as_posix()
            marker = f"[ATTACHMENT_PATH]: {path_str}"
            if marker not in user_input:
                user_input = f"{user_input}\n\n{marker}"
                st.session_state.user_input = user_input
        # --- END NEW ---

        if user_input:
            # Process the input and get an ID
            if not st.session_state.flow_id:
                st.session_state.flow_id = generate_id(selected, user_input)
                flow_id = st.session_state.flow_id


                def run_in_thread(flow_id):
                    run(flow_id)


                # Start the new thread for run function
                thread = threading.Thread(target=run_in_thread, args=(flow_id,))
                thread.start()
            else:
                flow_id = st.session_state.flow_id

            st.markdown(f"<b>Flow ID:</b> <code>{flow_id}</code>", unsafe_allow_html=True)
            st.markdown(f"<b>User:</b>", unsafe_allow_html=True)
            st.text(user_input)

            # Load memory data from the file corresponding to the generated ID
            memory_data = load_memory(flow_id)
            st.session_state.memory_data = memory_data

            # Display conversation from memory if data exists
            if memory_data:
                for step_id, step in enumerate(memory_data["workflow"][0:-1]):
                    task = step.get("task")
                    worker = step.get("worker")
                    tool = step.get("tool")
                    content = step.get("content")
                    data_section = step.get("tool_output", {})


                    if worker and tool and task:
                        response = f"<b>Step {step_id+1}:</b> <code>{worker}</code> used <b>{tool}</b> to do <b>{task}</b>."
                    elif task and content:
                        response = f"""<b>Step {step_id+1}:</b> <code>{worker}</code> did <b>{tool}</b>, result:<br>
                    <div style="
                    background:#f9fafb;
                    border:1px solid #e5e7eb;
                    border-radius:8px;
                    padding:12px 16px;
                    font-family:'Fira Code','JetBrains Mono','Consolas','Courier New',monospace;
                    font-size:13px;
                    line-height:1.6;
                    color:#111827;
                    white-space:pre-wrap;
                    word-break:break-word;
                    overflow-x:auto;
                    box-shadow:0 1px 2px rgba(0,0,0,0.08);
                    ">{content}</div>"""
                    elif task:
                        response = f"<b>Step {step_id+1}:</b> <code>{worker}</code> will perform <b>{task}</b>."
                    else:
                        response = f"<b>Step {step_id+1}:</b> No specific task defined."

                    st.markdown(response, unsafe_allow_html=True)
                    formatted_data = json.dumps(data_section, indent=2, ensure_ascii=False).strip('"').replace('\\n','\n')
                    if data_section:
                        is_json = False
                        try:
                            parsed = json.loads(formatted_data)
                            is_json = True
                        except json.JSONDecodeError:
                            is_json = False

                        if is_json:
                            st.write("📦 **Processed Data (JSON):**")
                            st.json(parsed)

                        else:
                            img_pattern = re.compile(r'(?:https?://\S+|\S+)\.(?:png|jpg|jpeg|gif|bmp)', re.IGNORECASE)
                            img_paths = img_pattern.findall(formatted_data)

                            if img_paths:
                                st.write("📦 **Processed Data (Images):**")
                                for img in img_paths:
                                    st.markdown(img, unsafe_allow_html=True)
                                    st.image(img, width=1000, use_container_width=False)
                                text_only = img_pattern.sub('', formatted_data).strip()
                                if text_only:
                                    st.markdown(text_only)
                            else:
                                st.write("📦 **Processed Data:**")
                                st.markdown(
                                    f"""<div style="
                                                    background:#f9fafb;
                                                    border:1px solid #e5e7eb;
                                                    border-radius:8px;
                                                    padding:12px 16px;
                                                    font-family:'Fira Code','JetBrains Mono','Consolas','Courier New',monospace;
                                                    font-size:13px;
                                                    line-height:1.6;
                                                    color:#111827;
                                                    white-space:pre-wrap;
                                                    word-break:break-word;
                                                    overflow-x:auto;
                                                    box-shadow:0 1px 2px rgba(0,0,0,0.08);
                                                    ">{formatted_data}</div>""",
                                    unsafe_allow_html=True
                                )

                        st.markdown('<hr class="step-divider">', unsafe_allow_html=True)
                summary = memory_data.get("summary")
                if summary:
                    st.markdown(f"<b>Summary:</b> <i>{summary}</i>", unsafe_allow_html=True)


            else:
                st.write("No memory data found for this ID.")

with tab1:
    # 1. 找到当前选择的 MAS 配置
    selected = st.session_state.get("mas_selected", "")
    idx = next((i for i, d in enumerate(mas_data) if d["name"] == selected), None)
    data = mas_data[idx] if idx is not None else None

    # 2. 从 memory 中取出最后执行的步骤，用于高亮
    last_task = {}
    if st.session_state.memory_data:
        for step in reversed(st.session_state.memory_data.get("workflow", [])):
            if step:
                last_task = step
                break

    if selected and data:
        # 3. Build mermaid source
        lines = ["flowchart LR"]

        manager_name = data["manager"]["name"]
        lines.append(f'{manager_name}(["{manager_name}"])')

        running_nodes = set()

        # tasks + workers
        for t in data["task"]:
            tname = t["name"]
            wname = t["worker"]

            lines.append(f'{tname}(["{tname}"]):::task')
            lines.append(f'{wname}(["{wname}"]):::worker')
            lines.append(f"{manager_name} --> {tname}")
            lines.append(f"{tname} --> {wname}")

            if tname == last_task.get("task"):
                running_nodes.add(tname)
            if wname == last_task.get("worker"):
                running_nodes.add(wname)

        # tools
        for w in data["worker"]:
            wname = w["name"]
            for tool in w.get("tools", []):
                lines.append(f'{tool}(["{tool}"]):::tool')
                lines.append(f"{wname} --> {tool}")
                if tool == last_task.get("tool"):
                    running_nodes.add(tool)

        # classDefs
        lines += [
            "classDef manager fill:#FFD1DC,stroke:#E75480,stroke-width:1px,color:#000000",
            "classDef task    fill:#E0F7FA,stroke:#00ACC1,stroke-width:1px,color:#000000",
            "classDef worker  fill:#FFF3CD,stroke:#C9A93B,stroke-width:1px,color:#000000",
            "classDef tool    fill:#E8F5E9,stroke:#6FA86C,stroke-width:1px,color:#000000",
            # Make running visually obvious
            "classDef running stroke:#FF4D4F,stroke-width:3px,color:#A8071A"
        ]

        # base classes
        lines.append(f"class {manager_name} manager")
        lines += [f"class {t['name']} task" for t in data["task"]]
        lines += [f"class {w['name']} worker" for w in data["worker"]]
        lines += [f"class {tool} tool" for w in data["worker"] for tool in w.get("tools", [])]

        # apply running LAST to avoid being overridden
        for nid in sorted(running_nodes):
            # If you prefer merging, you could also do: f"class {nid} tool,running" etc.
            lines.append(f"class {nid} running")

        # click bindings
        for t in data["task"]:
            lines.append(f'click {t["name"]} nodeClickCallback "{t["name"]}"')
        for w in data["worker"]:
            lines.append(f'click {w["name"]} nodeClickCallback "{w["name"]}"')
            for tool in w.get("tools", []):
                lines.append(f'click {tool} nodeClickCallback "{tool}"')
        lines.append(f'click {manager_name} nodeClickCallback "{manager_name}"')

        mermaid_code = "\n".join(lines)

        payload = {
            "manager": data["manager"],
            "task": data["task"],
            "worker": data["worker"],
            "tools": data.get("tools", {}),
        }
        payload_json = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")

        # 4. 布局：左边图和详情，右边图例
        st.title(f"{data.get('name', 'Optimization')} — Workflow")
        left, right = st.columns([5, 1], gap="small")

        with left:
            html_mermaid = py_html.escape(mermaid_code)
            mermaid_local_js = Path("assets/js/mermaid.min.js").read_text(encoding="utf-8")
            prism_js = Path("assets/js/prism.js").read_text(encoding="utf-8")
            prism_json_js = Path("assets/js/prism-json.min.js").read_text(encoding="utf-8")
            prism_css = Path("assets/css/prism.css").read_text(encoding="utf-8")
            html_content = f"""
            <div style="border:1px solid #e5e7eb;border-radius:12px;padding:12px">
              <pre class="mermaid" style="margin:0">{html_mermaid}</pre>
            </div>

            <div id="details" style="margin-top:16px;padding:16px;border:1px solid #e5e7eb;border-radius:12px;">
              <div id="details-body"></div>
              <div id="details-body"></div>
            </div>

             <style>{prism_css}</style>
             <script>{prism_js}</script>
             <script>{prism_json_js}</script>

           <script>
                {mermaid_local_js}
                mermaid.initialize({{ startOnLoad: false, securityLevel: 'loose', theme: 'default' }});
                mermaid.run({{ querySelector: '.mermaid' }});

              const payload = {payload_json};

function pretty(obj) {{
  const jsonStr = JSON.stringify(obj, null, 2)
    .replace(/[&<>]/g, c => ({{'&':'&amp;','<':'&lt;','>':'&gt;'}}[c]))
    .trimStart();

  return `<pre style="margin:0;background:#f8f9fa;border-radius:8px;
   padding:12px;font-family:'Fira Code','Courier New',monospace;
   font-size:13px;overflow-x:auto;">
<code class="language-json"
  style="white-space: pre-wrap !important;
         word-break: break-word;
         overflow-wrap:anywhere;">${{jsonStr}}</code>
</pre>`;
}}

              window.nodeClickCallback = function(id) {{
                const b = document.getElementById('details-body');
                if (payload.manager.name === id) b.innerHTML = '<b>Manager</b>' + pretty(payload.manager);
                else if (payload.task.find(x => x.name === id)) b.innerHTML = '<b>Task</b>' + pretty(payload.task.find(x => x.name === id));
                else if (payload.worker.find(x => x.name === id)) b.innerHTML = '<b>Worker</b>' + pretty(payload.worker.find(x => x.name === id));
                else if (payload.tools[id]) b.innerHTML = '<b>Tool</b>' + pretty(payload.tools[id]);
                else b.innerHTML = 'Not Found';
                Prism.highlightAll();
              }};
            </script>
            """
            components_html(html_content, height=650, scrolling=True)

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
