from worker import Worker
from llm import LLM
from decorators import bind_function
from manager import Manager
from flow import Flow
from task import Task
from functools import partial
import json
import uuid
import os
import importlib

def load(mas_name, user_input):
    CONFIG_FILE_PATH = 'config/mas_config.json'

    with open(CONFIG_FILE_PATH, "r", encoding="utf-8") as file:
        content = file.read()

    # Parse the JSON content and search for the dictionary with the matching mas_name
    config = next((item for item in json.loads(content) if item.get("name") == mas_name), None)

    if not config:
        raise ValueError(f"Configuration with name '{mas_name}' not found.")

    # Generate a new unique flow id
    id = str(uuid.uuid4())

    # Add the 'flow' key to the config dictionary
    config['flow'] = {
        "description": user_input,
        "manager": config.get("manager", {}).get("name", ""),
        "max_inter": 100,
        "summary": "o4-mini"
    }

    if not os.path.exists(f"flow/{id}.json"):
        config['id'] = id
        with open(f"flow/{id}.json", 'w') as f:
            json.dump(config, f, indent=4)
        with open(f"memory/{id}.json", 'w') as f:
            json.dump({"flow_id": str(id), "workflow": [{}]}, f)
        with open(f"history/{id}.json", 'w') as f:
            json.dump({"flow_id": str(id), "agent": []}, f)
        print(f"Create Flow {id}")
    return id





def run(flow_id):

    with open(f"flow/{flow_id}.json", "r", encoding="utf-8") as file:
        content = file.read()

    config = json.loads(content)

    worker_dict = {}
    llm_dict = {}
    tool_dict = config["tools"]
    task_dict = {}

    llm_config = config['llm']
    worker_config = config['worker']
    task_config = config['task']
    manager_config = config['manager']
    flow_config = config['flow']

    for i in llm_config:
        llm_dict[i["name"]] = LLM(
            model=i["model"],
            base_url=i["base_url"],
            api_key=i.get("api_key"),
            origins=i.get("origins", "openai")
        )

    for i in worker_config:
        tools = [tool_dict[tool] for tool in i["tools"]] if "tools" in i else None
        max_output = i.get("max_output", None)
        worker_dict[i["name"]] = Worker(
            name=i["name"],
            description=i['description'],
            llm=llm_dict[i["llm"]],
            tools=tools,
            max_output=max_output
        )

    # functions_module = importlib.import_module('functions')
    #
    # for worker_name, worker in worker_dict.items():
    #     for tool in worker.tools if worker.tools else []:
    #         function_name = tool["function"]["name"]
    #         func = getattr(functions_module, function_name, None)
    #         if func:
    #             bind_func_name = f"_bind_{function_name}"
    #             bind_func = partial(func)
    #             bind_function(worker, function_name)(bind_func)

    with open('config/tools_config.json', 'r', encoding='utf-8') as f:
        tools_list = json.load(f)

    func_code_map = {
        tool_def['func_name']: tool_def['code']
        for tool_def in tools_list
    }

    for worker_name, worker in worker_dict.items():
        for tool in (getattr(worker, 'tools', None) or []):
            func_name = tool['function']['name']

            module_ns = {
                "__name__": func_name,
                "__builtins__": __builtins__,
                "__file__": os.path.abspath(__file__) if "__file__" in globals() else f"<{func_name}>",
            }

            try:
                code_str = func_code_map[func_name]
            except KeyError:
                print(f"[Warning] Tool `{func_name}` is not defined in JSON; skipping.")
                continue

            try:
                exec(code_str, module_ns)
            except Exception as e:
                print(f"[Error] Failed to execute code for `{func_name}`: {e}")
                continue

            func = module_ns.get(func_name)
            if not callable(func):
                print(f"[Warning] `{func_name}` was not exported as a callable function; skipping.")
                continue

            bind_func = partial(func)
            bind_function(worker, func_name)(bind_func)

    for i in task_config:
        task_dict[i["name"]] = Task(name=i["name"], description=i["description"], worker=worker_dict[i["worker"]], human=i.get("human"))

    manager = Manager(name=manager_config["name"], description=manager_config["description"],
                      tasks=list(task_dict.values()), llm=llm_dict[manager_config["llm"]])

    flow = Flow(id=flow_id, description=flow_config["description"], manager=manager, max_inter=flow_config["max_inter"],
                summary=llm_dict[flow_config["summary"]])

    flow.execute()

