# self-constructive-MAS-for-process-development

**MAS** is a Streamlit-based web platform for testing and visualizing **Multi-Agent Systems (MAS)** designed for autonomous chemical reasoning and workflow execution.  

---

## 🚀 Quick Start (Docker Deployment)

### 1️⃣ Build the image

```bash
docker build -t mas:v0.1 .
```

### 2️⃣ Run the container

```bash
docker run -d   --name streamlit   -e TZ=Asia/Shanghai LLM_BASE_URL=xxx -e LLM_BASE_API_KEY=xxx -p 8501:8501   mas:v0.1
```

> 🕒 `TZ=Asia/Shanghai` ensures the app runs in **Beijing Time (UTC +8)**.  
> After startup, open **http://localhost:8501** in your browser.

---

## 📁 Project Structure

```
mas/
├── assets/                   # Static assets (images, icons, etc.)
├── config/                   # MAS configuration files (MAS / tools JSON)
├── data/                     # General data directory
├── flow/                     # Flow logs
├── history/                  # Execution history logs
├── memory/                   # Agent memory storage
├── pages/                    # Streamlit page modules
│   ├── 1-LLM_config.py
│   ├── 2-Tools_box.py
│   ├── 3-Multi-agent_generation.py
│   ├── 4-Playground.py
│   └── 5-History.py
│
├── agent.py                  # Agent class definitions
├── Dockerfile                # Docker build configuration
├── flow.py                   # Main flow control
├── functions.py              # Tool function implementations
├── Home.py                   # Streamlit entry page
├── llm.py                    # LLM class definitions
├── manager.py                # Manager agent
├── requirements.txt          # Python dependencies
├── run.py                    # Workflow runner
├── task.py                   # Task class definitions
├── template.txt              # Prompt or template base file
└── worker.py                 # Worker agent logic
```

---

---

## 🖥️ Application Usage Guide

Once the container is running, open:  
👉 [http://localhost:8501](http://localhost:8501)

The MAS-Playground interface contains **five major pages**, each serving a specific role in the multi-agent workflow:

---

### 🧠 1. LLM Config

This page allows you to configure and test the **language model backend** used by the agents.

- Define the model name.
- Set API key, base URL, and version.
- All settings are saved into `config/llm_config.json` for later use by the MAS.

---

### 🧰 2. Tools Box

A toolbox for managing and editing all available **agent tools**.

- Each tool consists of:
  - Function name and natural-language description.
  - Python code implementation.
  - Automatically generated **JSON Schema** for worker agent calling.
- The page can:
  - **Auto-generate** JSON schema from the Python code body.
  - Allow users to **edit or delete** tools dynamically.
  - Display scrollable code blocks and structured metadata for each tool.
- All tools are stored in `config/tools_config.json` and are dynamically bound to worker agents in runtime.

---

### 🤖 3. Multi-Agent Generation

A page for self-generating, visualizing, and self-modifying **MAS architectures**.

#### 🔹 Automatic Generation

- Supports **automatic MAS generation** based on predefined templates or natural-language prompts.
- Automatically creates manager–worker–task relationships and binds each worker to relevant tools.
- Saves the generated MAS configuration as `config/mas_config.json` for later use in the Playground.

#### 🔹 Self-Modification

- Enables **self-modification** of existing MAS configurations.
- Changes can be applied to selected sections without rebuilding the entire MAS.

#### 🔹 Visualization and Inspection

- Displays the list of existing MAS architectures saved in the project.
- For a selected MAS, clicking **Manager**, **Workers**, **Tasks**,or **Tools** reveals the exact **JSON configuration** of that node (parameters, bindings, and connections).

---

### 🧩 4. Playground

This is the **interactive execution and visualization core** of the system.

- Select one MAS configuration to launch.
- In the **Conversation** tab:
  - Type a prompt or instruction for the MAS (e.g., “Find the possible synthesis procedure for X”).
  - Optionally upload a related file (`PDF`, `TXT`, or `MD`), which will be saved under `/app/data/uploads/`.
  - The system will create a unique `flow_id` and start the reasoning workflow.
  - Each reasoning step, including worker/tool interactions, is displayed in real time.
- In the **Flow Chart** tab:
  - View the MAS topology (manager → task → worker → tool connections).
  - Monitor live data flow and reasoning sequence updates.

---

### 📜 5. History

A record and review page for **past workflow executions**.

- All completed workflows and memory logs are stored under `/memory/` and `/flow/`.
- You can reload previous `flow_id`s to inspect results and agent reasoning traces.

---

## 🧠 Example Workflow

1. Go to **LLM Config** to set up the desired language model.  
2. Open **Tools Box** to ensure the correct functions are available to the agents.  
3. Use **Multi-Agent Generation** to create a new MAS configuration or modify an existing one.  
4. Launch **Playground**, select your MAS, and input a research query.  
5. Observe real-time reasoning, intermediate outputs, and visual flow in the **Flow Chart** tab.  
6. After execution, switch to **History** to revisit or analyze previous results.

---

