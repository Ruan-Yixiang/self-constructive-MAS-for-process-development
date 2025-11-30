from pydantic import BaseModel
from worker import Worker
from typing import Optional



class Task(BaseModel):
    name: str
    description: str
    worker: Worker
    human: Optional[bool] = False
    # expected_output: str