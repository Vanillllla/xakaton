import openai
from dotenv import load_dotenv
import os


class LinkAI:
    load_dotenv()
    MODEL = os.getenv('MODEL')
    API_KEY = os.getenv('API_KEY')
    CLOUD_FOLDER = os.getenv('CLOUD_FOLDER')
    def single_prompt(self, input):
        client = openai.OpenAI(
            api_key=self.API_KEY,
            base_url="https://rest-assistant.api.cloud.yandex.net/v1",
            project=self.CLOUD_FOLDER
        )

        response = client.responses.create(
            model=f"gpt://{self.CLOUD_FOLDER}/{self.MODEL}",
            input=input,
            temperature=0.8,
            max_output_tokens=1500
        )

        return response

    def prompt_with_user_context(self, input, context):
        client = openai.OpenAI(
            api_key=self.API_KEY,
            base_url="https://rest-assistant.api.cloud.yandex.net/v1",
            project=self.CLOUD_FOLDER
        )

        response = client.responses.create(
            model=f"gpt://{self.CLOUD_FOLDER}/{self.MODEL}",
            input=[{"role": "user", "content": input}],
            previous_response_id=context
        )

        return response

    def single_prompt_with_system_context(self, input, context):
        client = openai.OpenAI(
            api_key=self.API_KEY,
            base_url="https://rest-assistant.api.cloud.yandex.net/v1",
            project=self.CLOUD_FOLDER
        )

        response = client.responses.create(
            model=f"gpt://{self.CLOUD_FOLDER}/{self.MODEL}",
            input=[{"role": "system", "content": context},
                   {"role": "user", "content": input}],
        )

        return response


    def prompt(self, input, context, system):
        client = openai.OpenAI(
            api_key=self.API_KEY,
            base_url="https://rest-assistant.api.cloud.yandex.net/v1",
            project=self.CLOUD_FOLDER
        )

        response = client.responses.create(
            model=f"gpt://{self.CLOUD_FOLDER}/{self.MODEL}",
            input=[{"role": "system", "content": system},
                   {"role": "user", "content": input}],
            previous_response_id=context
        )

        return response
