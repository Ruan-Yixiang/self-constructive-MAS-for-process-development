from pydantic import BaseModel
import uuid
import json
from typing import List, Dict, Optional
from manager import Manager
from llm import LLM
import os


class Flow(BaseModel):
    id: str
    description: str
    manager: Manager
    max_inter: int = 100
    memory: Optional[Dict] = None
    history: Optional[Dict] = None
    summary: Optional[LLM] = None
    # end: str = "E#N#D#!"


    # def __init__(self, **data):
    #     super().__init__(**data)
    #     if not os.path.exists(f"flow/{self.id}.json"):
    #         self.config['id'] = self.id
    #         with open(f"flow/{self.id}.json", 'w') as f:
    #             json.dump(self.config, f, indent=4)
    #         self.create_memory()
    #         self.create_history()
    #         print(f"Create Flow {self.id}")



    def create_history(self):
        with open(f"history/{self.id}.json", 'w') as f:
            json.dump({"flow_id": str(self.id), "agent": []}, f)

    def create_memory(self):
        with open(f"memory/{self.id}.json", 'w') as f:
            json.dump({"flow_id": str(self.id), "workflow": [{}]}, f)

    def load_memory(self):
        with open(f"memory/{self.id}.json", 'r+') as f:
            memory = json.load(f)
        return memory

    def load_history(self):
        with open(f"history/{self.id}.json", 'r+') as f:
            history = json.load(f)
        return history

    def record_memory(self):
        with open(f"memory/{self.id}.json", 'r+') as f:
            self.memory["workflow"].append({})
            memory = self.memory
            f.seek(0)
            json.dump(memory, f, indent=4)
            f.truncate()

    def record_history(self, context):
        with open(f"history/{self.id}.json", 'r+') as f:
            history = json.load(f)
            history["agent"].append(context)
            f.seek(0)
            json.dump(history, f, indent=4)
            f.truncate()

    def manager_judge(self, tasks_descriptions):
        res, history, self.memory = self.manager.judge(self.memory)
        self.record_history(history)
        # self.record_memory(memory)
        task_chosen = res['task']
        end = res['end']
        if task_chosen != 'none':
            print("\033[1;34mTask\033[0m", f"\033[1;34m{task_chosen}\033[0m")
        return task_chosen, end

    def worker_execute(self, worker_agent, task_name):
        print("\033[1;33mWorker\033[0m", f"\033[1;33m{worker_agent.name}\033[0m")
        history, self.memory, memory_nl = worker_agent.worker_execute(str(self.id), self.description, self.memory, task_name)
        self.record_memory()
        self.record_history(history)
        return memory_nl

    def worker_re_execute(self, worker_agent, user_feedback):
        print("\033[1;33mWorker\033[0m", f"\033[1;33m{worker_agent.name}\033[0m")
        history, self.memory, memory_nl = worker_agent.worker_execute(str(self.id), self.description, str(self.memory) + "User's feedback is following: " + user_feedback)
        self.record_memory()
        self.record_history(history)
        return memory_nl


    def execute(self):
        print("Flow id:", self.id)
        # tasks_descriptions = [task.model_dump(include={"name", "description"}) for task in self.tasks]
        for num_inter in range(self.max_inter):
            self.memory = self.load_memory()
            # task_chosen_name = self.choose_task(tasks_descriptions)
            task_chosen_name, end = self.manager_judge(self.memory)
            if end:
                break
            chosen_task = next((task for task in self.manager.tasks if task.name == task_chosen_name), None)
            worker_agent = chosen_task.worker
            # task_description = chosen_task.description
            memory_nl = self.worker_execute(worker_agent, task_chosen_name)
            if chosen_task.human:
                while True:
                    print('\033[1;32mModify general task, input 1; Re_execute worker agent, input 2; press enter to skip.\033[0m')
                    feedback_type = input("Feedback type:")
                    if not feedback_type:
                        break
                    else:
                        user_feedback = input("User feedback:")
                        if feedback_type == "1" and user_feedback:
                                self.description += "User's modification is following: " + user_feedback
                                self.memory = self.load_memory()
                                self.worker_execute(worker_agent)
                        elif feedback_type == "2" and user_feedback:
                            self.worker_re_execute(worker_agent, user_feedback)
            num_inter += 1
        if self.summary:
            summery_content = self.description + "The completion process is " + memory_nl
            # print(memory_nl)
            message = [{"role": "system", "content": "Summary the workflow include process and final conclusions within 100 words."},
                    {"role": "user", "content": summery_content}]
            answer = self.summary.call(messages=message)
            print('\n', "-----------------------Summary-------------------------")
            print(answer['content'])
            message.append(answer)
            self.record_history(message)
            with open(f"memory/{self.id}.json", 'r+') as f:
                summary_final = json.load(f)

                summary_final['summary'] = answer['content']
                f.seek(0)
                json.dump(summary_final, f, indent=4)
                f.truncate()


