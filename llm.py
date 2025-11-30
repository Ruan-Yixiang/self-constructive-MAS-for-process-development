from pydantic import BaseModel
from typing import Optional, Literal
from openai import OpenAI, max_retries
import requests
import json
import time


class LLM(BaseModel):
    model: str
    base_url: str
    api_key: Optional[str] = None
    origins: Literal["openai", "ollama"] = "openai"

    def call(self, messages, tools=None):
        if self.origins == "openai":
            client = OpenAI(api_key=self.api_key, base_url=self.base_url, max_retries=10)
            completion_args = {
                "model": self.model,
                "messages": messages,
            }
            if tools is not None:
                completion_args["tools"] = tools
            completion = client.chat.completions.create(**completion_args)
            print(completion_args)
            res = completion.choices[0].message.model_dump()
            print('res', res)
            return res
        elif self.origins == "ollama":
            url = self.base_url
            headers = {
                "Content-Type": "application/json"
            }
            completion_args = {
                "model": self.model,
                "messages": messages,
                "stream": False,
            }
            if tools is not None:
                completion_args["tools"] = tools
            # print('m', completion_args)

            response = requests.post(url, headers=headers, json=completion_args)
            # print(response.text)
            res = json.loads(response.text)['message']
            # print('res', res)
            return res