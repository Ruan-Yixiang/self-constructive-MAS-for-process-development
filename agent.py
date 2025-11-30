from pydantic import BaseModel
from typing import Optional
from llm import LLM


class Agent(BaseModel):
    name: str
    description: str
    llm: LLM
    # end: Optional[str] = None
    max_output: Optional[int] = None
    class Config:
        extra = "allow"

    def dict_to_natural_language(self, data):
        flow_id = data.get("flow_id", "Unknown")
        workflow = data.get("workflow", [])

        if workflow and isinstance(workflow[-1], dict) and not workflow[-1]:
            workflow.pop()

        sentences = [f"The flow ID is {flow_id}."]

        for i, step in enumerate(workflow, start=1):
            if not step:
                continue

            task = step.get("task")
            worker = step.get("worker")
            tool = step.get("tool")
            data_section = step.get("data")
            content = step.get("content")

            if worker and tool and task:
                sentences.append(
                    f"Step {i} used the {worker} worker agent with the {tool} tool to execute the {task} task."
                )
            elif task and content:
                sentences.append(f"In step {i}, the {task} task has been executed by {worker} worker agent, and the answer is {content}")
            elif task:
                sentences.append(f"In step {i}, the task {task} will be executed.")
            else:
                sentences.append(f"In step {i}, no specific task was defined.")

            if data_section:
                sentences.append(f"The data for this step is: {data_section}.")

        return " ".join(sentences)



