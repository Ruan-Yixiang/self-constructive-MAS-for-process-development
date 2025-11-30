from agent import Agent
from typing import List
from task import Task
import copy
import json


def task_selection(tasks_data):
    task_names = [task['name'] for task in tasks_data] + ['none']  # Add 'none' as a termination option

    task_selection = [
        {
            "type": "function",
            "function": {
                "name": "task_selection",
                "description": "Manager agent selects the next task or decides whether to terminate the process.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "task": {
                            "type": "string",
                            "enum": task_names,  # Limit task to current task names
                            "description": "The task to be executed next. If no task, return 'none'."
                        },
                        "end": {
                            "type": "boolean",
                            "description": "Indicates whether the process should end. 'true' if terminated, 'false' if the process continues."
                        }
                    },
                    "required": ["task", "end"]
                }
            }
        }
    ]

    return task_selection


class Manager(Agent):
    tasks: List[Task]


    def judge(self, memory):
        system_prompt= """You are a manager in the workflow, You are responsible for selecting the next task in the process based on process operation logic and determine whether to terminate the process."""

        tasks_descriptions = [task.model_dump(include={"name", "description"}) for task in self.tasks]
        task_selection_tool = task_selection(tasks_descriptions)
        memory_clear = copy.deepcopy(memory)
        found_data = False
        for i in reversed(memory_clear["workflow"]):
            if "data" in i:
                if not found_data:
                    found_data = True
                else:
                    del i["data"]
        memory_nl = self.dict_to_natural_language(memory_clear)
        # print('man_clear', memory_clear)
        content = "The process operation logic is "+ self.description + " The descriptions of each tasks are following:" + str(
            tasks_descriptions) + " The memory in this workflow is following:" + memory_nl
        message = [{"role": "system", "content": system_prompt},
                    {"role": "user", "content": content}]
        current_memory = memory["workflow"][-1]
        answer = self.llm.call(messages=message, tools=task_selection_tool)
        fun = answer['tool_calls'][0]['function']
        if type(fun['arguments']) == dict:
            fun_args = fun['arguments']
        else:
            fun_args = json.loads(fun['arguments'])
        task_chosen = fun_args['task']
        message.append(answer)
        current_memory["task"] = task_chosen
        return fun_args, message, memory