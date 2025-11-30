"""

This is the main page, that you have to run with "streamlit run" to launch the app locally.
Streamlit automatically create the tabs in the left sidebar from the .py files located in /pages
Here we just have the home page, with a short description of the tabs, and some images

"""

import streamlit as st


st.set_page_config(
    page_title="Home page",
    page_icon="👋",
    layout="wide")


# Description of the features.
st.markdown(
    """
    ## Welcome to the Self-Generated Multi-Agent System (MAS) Platform

This platform allows you to **build, modify, and analyze intelligent workflows** to autonomously handle iterative chemical research.  
Use the left panel to explore different modules:

---

### 🧠 LLM Config
Define or load your preferred large-language-model configuration.  
Customize model names, API keys, and Base URL.

---

### 🧰 Tools Box
Add task-specific tools (e.g., molecule similarity, synthesis retrieval, reaction optimization).  
These tools can be linked to agents to expand their autonomous capabilities.

---

### 🤖 Multi-Agent Generation
Automatically create new MAS configurations from natural-language instructions.  
Start from an existing template, and the system will **self-generate or self-modify** agents, tasks, and tools according to your goal.

---

### 🧩 Playground
Test and visualize your multi-agent workflow interactively.  
Inspect each agent’s reasoning, message passing, and agent states.

---

### 🕓 History
Review previously executed MAS sessions’ results.

---

💡 **Tip:**  
The platform supports *self-generation* (creating new agents from scratch) and *self-modification* (adapting existing MAS).  
Together, they enable **autonomous, adaptive chemical research pipelines**.
"""
)
