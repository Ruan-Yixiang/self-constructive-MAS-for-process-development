# import os
# import json
# import glob
# import re
# import datetime
# from pathlib import Path
# import streamlit as st
#
# # ===== 基本配置 =====
# memory_file_directory = "D:/llm4optimization/memory"
# st.set_page_config(page_title="Project History", layout="wide")
# st.title("📜 Project History")
#
# # ===== 获取所有记录 =====
# files = sorted(
#     glob.glob(os.path.join(memory_file_directory, "*.json")),
#     key=os.path.getctime,
#     reverse=True
# )
#
# if not files:
#     st.info("No project history found.")
#     st.stop()
#
# # ===== 分页参数 =====
# page_size = 10
# total_pages = (len(files) + page_size - 1) // page_size
# page = st.number_input("Page", min_value=1, max_value=total_pages, value=1, step=1)
#
# start = (page - 1) * page_size
# end = start + page_size
# current_files = files[start:end]
#
# # ===== 顶部选择框（Flow ID + 创建时间） =====
# options = []
# for f in current_files:
#     flow_id = Path(f).stem
#     ctime = datetime.datetime.fromtimestamp(os.path.getctime(f)).strftime("%Y-%m-%d %H:%M:%S")
#     options.append(f"{flow_id} — {ctime}")
#
# selected_display = st.selectbox("Select a project to view conversation history", options, index=0)
# selected_id = selected_display.split(" — ")[0]
#
# # ===== 加载数据 =====
# file_path = next(p for p in current_files if Path(p).stem == selected_id)
# with open(file_path, "r", encoding="utf-8") as f:
#     data = json.load(f)
#
# st.markdown(f"<b>Flow ID:</b> <code>{selected_id}</code>", unsafe_allow_html=True)
# summary = data.get("summary")
# if summary:
#     st.markdown(f"<b>Summary:</b> <i>{summary}</i>", unsafe_allow_html=True)
#
# workflow = data.get("workflow", [])
# if not workflow:
#     st.write("No conversation data found.")
# else:
#     # ===== 展示步骤（沿用 tab2 逻辑） =====
#     for idx, step in enumerate(workflow, start=1):
#         if not step:   # 跳过空步骤
#             continue
#
#         task = step.get("task")
#         worker = step.get("worker")
#         tool = step.get("tool")
#         content = step.get("content")
#         data_section = step.get("tool_output", {})
#
#         if worker and tool and task:
#             response = f"<b>Step {idx}:</b> <code>{worker}</code> used <b>{tool}</b> to do <b>{task}</b>."
#         elif task and content:
#             response = f"<b>Step {idx}:</b> <code>{worker}</code> did <b>{task}</b>, and the result is:<br><i>{content}</i>"
#         elif task:
#             response = f"<b>Step {idx}:</b> <code>{worker}</code> will perform <b>{task}</b>."
#         else:
#             response = f"<b>Step {idx}:</b> No specific task defined."
#
#         st.markdown(response, unsafe_allow_html=True)
#
#         # ======== 处理 tool_output ========
#         if data_section:
#             # 兼容 tab2 原始写法
#             formatted_data = json.dumps(data_section, indent=2, ensure_ascii=False).strip('"').replace('\\n', '\n')
#             is_json = False
#             try:
#                 # 如果 data_section 自身是 dict，直接解析
#                 parsed = json.loads(formatted_data)
#                 is_json = True
#             except Exception:
#                 is_json = False
#
#             if is_json:
#                 st.write("📦 **Processed Data (JSON):**")
#                 st.json(parsed)
#             else:
#                 # 图片或文本
#                 img_pattern = re.compile(r'(?:https?://\S+|\S+)\.(?:png|jpg|jpeg|gif|bmp)', re.IGNORECASE)
#                 img_paths = img_pattern.findall(formatted_data)
#
#                 if img_paths:
#                     st.write("📦 **Processed Data (Images):**")
#                     for img in img_paths:
#                         st.markdown(img, unsafe_allow_html=True)
#                         st.image(img, width=1000, use_container_width=False)
#                     text_only = img_pattern.sub('', formatted_data).strip()
#                     if text_only:
#                         st.markdown(text_only)
#                 else:
#                     st.write("📦 **Processed Data:**")
#                     st.markdown(f"```\n{formatted_data}\n```")
#
#         st.markdown('<hr class="step-divider">', unsafe_allow_html=True)
import os, re, json, glob, datetime
from pathlib import Path
import streamlit as st
from streamlit.components.v1 import html as components_html
import html as py_html

memory_dir = "memory"
flow_dir   = "flow"

st.set_page_config(page_title="Project History", layout="wide")
st.title("🕓 History")
st.caption('Review previously executed MAS sessions’ results.')



# ---------- 列出所有历史 ----------
files = sorted(
    glob.glob(os.path.join(memory_dir, "*.json")),
    key=os.path.getctime,
    reverse=True
)
if not files:
    st.info("No project history found.")
    st.stop()

page_size = 10
total_pages = (len(files) + page_size - 1) // page_size
page = st.number_input("Page", 1, total_pages, 1, 1)
current = files[(page-1)*page_size : page*page_size]

opts = []
for f in current:
    fid = Path(f).stem
    ctime = datetime.datetime.fromtimestamp(os.path.getctime(f)).strftime("%Y-%m-%d %H:%M:%S")
    opts.append(f"{fid} — {ctime}")

sel_disp = st.selectbox("Select a project", opts, index=0)
flow_id = sel_disp.split(" — ")[0]

with open(next(p for p in current if Path(p).stem == flow_id), "r", encoding="utf-8") as f:
    mem = json.load(f)

# ---- 读取 flow/<id>.json ----
flow_desc = "(no description)"
mas_conf = None
fp = os.path.join(flow_dir, f"{flow_id}.json")
if os.path.exists(fp):
    with open(fp, "r", encoding="utf-8") as f:
        fj = json.load(f)
    mas_name = fj.get("name", {})
    flow_desc = fj.get("flow", {}).get("description", flow_desc)
    if all(k in fj for k in ("manager","task","worker")):
        mas_conf = {
            "manager": fj["manager"],
            "task": fj["task"],
            "worker": fj["worker"],
            "tools": fj.get("tools", {})
        }

st.markdown(f"<b>MAS Name:</b> <code>{mas_name}</code>", unsafe_allow_html=True)
st.markdown(f"<b>Flow ID:</b> <code>{flow_id}</code>", unsafe_allow_html=True)
st.markdown(f"<b>User:</b>", unsafe_allow_html=True)
st.text(flow_desc)

if mem.get("summary"):
    st.markdown(f"<b>Summary:</b> <i>{mem['summary']}</i>", unsafe_allow_html=True)

# tab1, tab2 = st.tabs(["Conversation History", "MAS"])

# with tab1:
for i, step in enumerate(mem.get("workflow", []), 1):
    if not step: continue
    t, w, tool, content = step.get("task"), step.get("worker"), step.get("tool"), step.get("content")
    if w and tool and t:
        resp = f"<b>Step {i}:</b> <code>{w}</code> used <b>{tool}</b> to do <b>{t}</b>."
    elif t and content:
        resp = f"""<b>Step {i}:</b> <code>{w}</code> did <b>{t}</b>, result:<br>
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
    elif t:
        resp = f"<b>Step {i}:</b> <code>{w}</code> will perform <b>{t}</b>."
    else:
        resp = f"<b>Step {i}:</b> No specific task defined."
    st.markdown(resp, unsafe_allow_html=True)

    data_section = step.get("tool_output", {})
    if data_section:
        formatted = json.dumps(data_section, indent=2, ensure_ascii=False).strip('"').replace('\\n','\n')
        try:
            parsed = json.loads(formatted)
            st.write("📦 **Processed Data (JSON):**")
            st.json(parsed)
        except:
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
                    ">{formatted}</div>""",
                unsafe_allow_html=True
            )

    st.markdown('<hr class="step-divider">', unsafe_allow_html=True)

# def render_mermaid(mas):
#     def safe_id(name: str) -> str:
#         return re.sub(r"[^0-9a-zA-Z_]", "_", name)
#
#     lines = ["flowchart LR"]
#     mid = safe_id(mas["manager"]["name"])
#
#     # Manager 节点 + 点击事件
#     lines.append(f'{mid}(["{mas["manager"]["name"]}"])')
#     lines.append(f'click {mid} nodeClickCallback "{mas["manager"]["name"]}"')
#
#     for t in mas["task"]:
#         tid, wid = safe_id(t["name"]), safe_id(t["worker"])
#         lines += [
#             f'{tid}(["{t["name"]}"]):::task',
#             f'{wid}(["{t["worker"]}"]):::worker',
#             f"{mid} --> {tid}",
#             f"{tid} --> {wid}",
#             f'click {tid} nodeClickCallback "{t["name"]}"',
#             f'click {wid} nodeClickCallback "{t["worker"]}"',
#         ]
#     for w in mas["worker"]:
#         for tool in w.get("tools", []):
#             toid = safe_id(tool)
#             lines += [
#                 f'{toid}(["{tool}"]):::tool',
#                 f"{safe_id(w['name'])} --> {toid}",
#                 f'click {toid} nodeClickCallback "{tool}"',
#             ]
#     lines += [
#         "classDef manager fill:#FFD1DC,stroke:#E75480,stroke-width:1px,color:#000000",
#         "classDef task    fill:#E0F7FA,stroke:#00ACC1,stroke-width:1px,color:#000000",
#         "classDef worker  fill:#FFF3CD,stroke:#C9A93B,stroke-width:1px,color:#000000",
#         "classDef tool    fill:#E8F5E9,stroke:#6FA86C,stroke-width:1px,color:#000000",
#         f"class {mid} manager",
#         *[f"class {safe_id(t['name'])} task" for t in mas["task"]],
#         *[f"class {safe_id(w['name'])} worker" for w in mas["worker"]],
#         *[f"class {safe_id(tool)} tool"
#           for w in mas["worker"] for tool in w.get("tools", [])],
#     ]
#     mermaid_code = "\n".join(lines)
#
#     payload = {
#         "manager": mas["manager"],
#         "task": mas["task"],
#         "worker": mas["worker"],
#         "tools": mas.get("tools", {}),
#     }
#     payload_json = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")
#
#     # html_mermaid = py_html.escape(mermaid_code)
#     html_mermaid = mermaid_code
#
#     mermaid_local_js = Path("assets/js/mermaid.min.js").read_text(encoding="utf-8")
#     prism_js = Path("assets/js/prism.js").read_text(encoding="utf-8")
#     prism_json_js = Path("assets/js/prism-json.min.js").read_text(encoding="utf-8")
#     prism_css = Path("assets/css/prism.css").read_text(encoding="utf-8")
#
#     html_content = f"""
#     <div style="border:1px solid #e5e7eb;border-radius:12px;padding:12px">
#       <pre class="mermaid" style="margin:0">{html_mermaid}</pre>
#     </div>
#
#     <div id="details" style="margin-top:16px;padding:16px;border:1px solid #e5e7eb;border-radius:12px;">
#       <div id="details-body"></div>
#     </div>
#
#     <style>{prism_css}</style>
#     <script>{prism_js}</script>
#     <script>{prism_json_js}</script>
#
#     <script>
#     {mermaid_local_js}
#     mermaid.initialize({{ startOnLoad: false, securityLevel: 'loose', theme: 'default' }});
#     mermaid.run({{ querySelector: '.mermaid' }});
#
#       const payload = {payload_json};
#
#       function pretty(obj) {{
#         const jsonStr = JSON.stringify(obj, null, 2)
#           .replace(/[&<>]/g, c => ({{'&':'&amp;','<':'&lt;','>':'&gt;'}}[c]));
#         return `<pre style="margin:0;background:#f8f9fa;border-radius:8px;padding:12px;
#                      font-family:'Fira Code','Courier New',monospace;
#                      font-size:13px;overflow-x:auto;"><code class="language-json">${{jsonStr}}</code></pre>`;
#       }}
#
#       window.nodeClickCallback = function(id) {{
#         const b = document.getElementById('details-body');
#         if (payload.manager.name === id) b.innerHTML = '<b>Manager</b>' + pretty(payload.manager);
#         else if (payload.task.find(x => x.name === id)) b.innerHTML = '<b>Task</b>' + pretty(payload.task.find(x => x.name === id));
#         else if (payload.worker.find(x => x.name === id)) b.innerHTML = '<b>Worker</b>' + pretty(payload.worker.find(x => x.name === id));
#         else if (payload.tools[id]) b.innerHTML = '<b>Tool</b>' + pretty(payload.tools[id]);
#         else b.innerHTML = 'Not Found';
#         Prism.highlightAll();
#       }};
#     </script>
#     """
#
#     # 分左右两列：左侧图，右侧图例
#     left, right = st.columns([5, 1], gap="small")
#     with left:
#         components_html(html_content, height=650, scrolling=True)
#     with right:
#         st.markdown(
#             """
#             <div style="padding:6px 0;">
#               <span style="background-color:#FFD1DC;border-radius:8px;padding:4px 8px;">Manager</span>
#             </div>
#             <div style="padding:6px 0;">
#               <span style="background-color:#E0F7FA;border-radius:8px;padding:4px 8px;">Task</span>
#             </div>
#             <div style="padding:6px 0;">
#               <span style="background-color:#FFF3CD;border-radius:8px;padding:4px 8px;">Worker</span>
#             </div>
#             <div style="padding:6px 0;">
#               <span style="background-color:#E8F5E9;border-radius:8px;padding:4px 8px;">Tool</span>
#             </div>
#             """,
#             unsafe_allow_html=True,
#         )
#
# with tab2:
#     if mas_conf:
#         render_mermaid(mas_conf)
#     else:
#         st.info("No MAS configuration found.")


