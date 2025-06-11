from openai import OpenAI
from config.settings import LLMConfig
from typing import List, Dict, Any, Optional
import json
import time


class LLMService:
    def __init__(self, config=LLMConfig):
        self.client = OpenAI(api_key=config.api_key)
        self.model = config.model
        self.temperature = config.temperature
        self.max_tokens = config.max_tokens
        self.max_retries = config.max_retries
        self.retry_delay = config.max_delay

    def generate_completion(self,
                            system_prompt: str,
                            user_prompt: str,
                            json_mode: bool = True) -> str:
        """Generate completion using OpenAI API with retry logic"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }


        for attempt in range(self.max_retries):
            try:
                response = self.client.chat.completions.create(**kwargs)
                content = response.choices[0].message.content.strip()

                if json_mode:
                    try:
                        # Validate it's proper JSON and return as-is if valid
                        json.loads(content)
                        return content
                    except json.JSONDecodeError:
                        # If not valid JSON, try to extract JSON or wrap it
                        extracted_json = self.extract_json_from_response(content)
                        if extracted_json:
                            return json.dumps(extracted_json)
                        else:
                            # Last resort: wrap in object
                            return json.dumps({"response": content})

                return content

            except Exception as e:
                if attempt < self.max_retries - 1:
                    print(f"LLM API error (attempt {attempt + 1}): {str(e)}")
                    time.sleep(self.retry_delay * (attempt + 1))
                else:
                    raise Exception(f"LLM API failed after {self.max_retries} attempts: {str(e)}")

    def extract_json_from_response(self, response: str) -> Dict[str, Any]:
        """Extract JSON from LLM response even if it contains other text"""
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            start_markers = ['{', '[']
            end_markers = ['}', ']']

            for start_marker, end_marker in zip(start_markers, end_markers):
                start = response.find(start_marker)
                if start != -1:
                    count = 1
                    pos = start + 1
                    while pos < len(response) and count > 0:
                        if response[pos] == start_marker:
                            count += 1
                        elif response[pos] == end_marker:
                            count -= 1
                        pos += 1

                    if count == 0:
                        try:
                            json_str = response[start:pos]
                            return json.loads(json_str)
                        except:
                            continue

            return {}


llm_service = LLMService()