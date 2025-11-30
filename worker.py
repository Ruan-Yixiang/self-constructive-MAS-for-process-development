from agent import Agent
import json
import copy
from typing import List, Optional, Dict



class Worker(Agent):
    tools: Optional[List[Dict]] = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # if self.end:
        #     self.description += " If it is determined that the workflow can be ended, then output " + self.end + " in the answer. If not, do not output any word similar as " + self.end + " in the answer."
        if self.max_output:
            self.description += " the max output words should be less than or equal to " + str(self.max_output)
    def worker_execute(self, flow_id, flow_description, memory, task_name):
        memory_clear = copy.deepcopy(memory)
        last_index = -1
        for i, d in enumerate(memory_clear["workflow"]):
            if "data" in d:
                last_index = i
        for i, d in enumerate(memory_clear["workflow"]):
            if "data" in d and i != last_index:
                del d["data"]
        # for i in memory_clear["workflow"][:-2]:
        #     if "data" in i:
        #         del i["data"]
        # print("clear_w", memory_clear)
        memory_nl = self.dict_to_natural_language(memory_clear)
        system_prompt = f"The task is {task_name}. {self.description}"
        content = "The goal is following:" + flow_description + "The memory in this workflow is following:" + memory_nl
        message = [{"role": "system", "content": system_prompt},
                    {"role": "user", "content": content}]
        answer = self.llm.call(messages=message, tools=self.tools)
        current_memory = memory["workflow"][-1]
        current_memory["worker"] = self.name
        if answer["content"]:
            current_memory["content"] = answer["content"]
        if 'tool_calls' in answer:
            if answer['tool_calls']:
                fun = answer['tool_calls'][0]['function']
                fun_name = fun['name']
                current_memory["tool"] = fun_name
                if type(fun['arguments']) == dict:
                    fun_args = fun['arguments']
                else:
                    fun_args = json.loads(fun['arguments'])
                fun_args['flow_id'] =  flow_id
                if hasattr(self, fun_name):
                    tool_output = getattr(self, fun_name)(**fun_args)
                    fun['output'] = tool_output
                    current_memory["tool_output"] = tool_output
                    json_file_path = f'data/{flow_id}.json'
                    with open(json_file_path, "r", encoding='utf-8') as json_file:
                        json_data = json.load(json_file)
                    current_memory['data'] = json_data
            else:
                print(answer['content'])
        else:
            print(answer['content'])
        message.append(answer)
        return message, memory, memory_nl