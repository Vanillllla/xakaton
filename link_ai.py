import openai
from dotenv import load_dotenv
from yandex_cloud_ml_sdk import YCloudML
import os
import json


class LinkAI:
    load_dotenv()
    MODEL = os.getenv('MODEL')
    API_KEY = os.getenv('API_KEY')
    CLOUD_FOLDER = os.getenv('CLOUD_FOLDER')
    SIZE = {1: '100', 2: '250', 3: '500'}
    SETTINGS = json.load(open('settings.json'))['settings']
    QUESTIONS = json.load(open('settings.json'))['questions']

    def single_prompt(self, prompt):
        '''
        Только промт
        :param prompt:
        :return:
        '''
        client = openai.OpenAI(
            api_key=self.API_KEY,
            base_url="https://rest-assistant.api.cloud.yandex.net/v1",
            project=self.CLOUD_FOLDER
        )

        response = client.responses.create(
            model=f"gpt://{self.CLOUD_FOLDER}/{self.MODEL}",
            input=prompt,
            temperature=0.8,
            max_output_tokens=1500
        )

        return response

    def prompt_with_user_context(self, prompt, context):
        '''
        Промпт в диалоге
        :param prompt:
        :param context:
        :return:
        '''
        client = openai.OpenAI(
            api_key=self.API_KEY,
            base_url="https://rest-assistant.api.cloud.yandex.net/v1",
            project=self.CLOUD_FOLDER
        )

        response = client.responses.create(
            model=f"gpt://{self.CLOUD_FOLDER}/{self.MODEL}",
            input=[{"role": "user", "content": prompt}],
            previous_response_id=context
        )

        return response

    def prompt_with_system_context(self, prompt, context):
        '''
        Промпт и знание об НКО
        :param prompt:
        :param context:
        :return:
        '''
        client = openai.OpenAI(
            api_key=self.API_KEY,
            base_url="https://rest-assistant.api.cloud.yandex.net/v1",
            project=self.CLOUD_FOLDER
        )

        response = client.responses.create(
            model=f"gpt://{self.CLOUD_FOLDER}/{self.MODEL}",
            input=[{"role": "system", "content": context},
                   {"role": "user", "content": prompt}],
        )

        return response

    def prompt(self, prompt, context, system):
        '''
        Промпт с знанием об НКО и контекстом диалоаг
        :param prompt:
        :param context:
        :param system:
        :return:
        '''
        client = openai.OpenAI(
            api_key=self.API_KEY,
            base_url="https://rest-assistant.api.cloud.yandex.net/v1",
            project=self.CLOUD_FOLDER
        )

        response = client.responses.create(
            model=f"gpt://{self.CLOUD_FOLDER}/{self.MODEL}",
            input=[{"role": "system", "content": system},
                   {"role": "user", "content": prompt}],
            previous_response_id=context
        )

        return response

    async def draw(self, prompt):
        '''
        Делает картинки
        :param prompt:
        :return:
        '''
        sdk = YCloudML(
            folder_id=self.CLOUD_FOLDER,
            auth=self.API_KEY
        )
        model = sdk.models.image_generation("yandex-art")

        operation = model.run_deferred(prompt)
        result = operation.wait()

        return result

    def rewrite(self, prompt):
        '''
        Исправление ошибок
        :param prompt:
        :return:
        '''
        client = openai.OpenAI(
            api_key=self.API_KEY,
            base_url="https://rest-assistant.api.cloud.yandex.net/v1",
            project=self.CLOUD_FOLDER
        )

        response = client.responses.create(
            model=f"gpt://{self.CLOUD_FOLDER}/{self.MODEL}",
            input=[{
                "role": "system",
                "content": "Исправь грамматические, орфографические и пунктуационные ошибки в тексте. Сохраняй исходный порядок слов."
            }, {"role": "user", "content": prompt}],
            temperature=0.8,
            max_output_tokens=1500
        )

        return response

    def content_plan(self, prompt, info):
        '''
        Контент план
        :param prompt:
        :return:
        '''
        client = openai.OpenAI(
            api_key=self.API_KEY,
            base_url="https://rest-assistant.api.cloud.yandex.net/v1",
            project=self.CLOUD_FOLDER
        )

        response = client.responses.create(
            model=f"gpt://{self.CLOUD_FOLDER}/{self.MODEL}",
            input=[{
                "role": "system",
                "content": f"""
Используй форматирование MarkdownV2.
Создай контент-план для социальных сетей НКО [Название НКО взять из информации после символа - ㅤ встреченного позже] 
на период [указать временной промежуток, например, месяц] с учётом следующих параметров:   
1. Укажи дни когда нужно сделать пост, учитывая частоту, если указана, и важные события
2. Для каждого поста в плане укажи его тематику, хештэг к нему, варианты для его оформления.
Опирайся на информацию ниже ㅤ{info}"""

            }, {"role": "user", "content": prompt}],
            temperature=0.8
        )

        return response

    def create_system_prompt(self, prompt):
        '''
                Функция для собирания информации об организации в системный промт
                :param prompt:
                :return:
                '''
        client = openai.OpenAI(
            api_key=self.API_KEY,
            base_url="https://rest-assistant.api.cloud.yandex.net/v1",
            project=self.CLOUD_FOLDER
        )

        response = client.responses.create(
            model=f"gpt://{self.CLOUD_FOLDER}/{self.MODEL}",
            input=[{
                "role": "system",
                "content": """
Используй форматирование MarkdownV2.
Ты эксперт в создании промтов для yandexgpt-lite.
Сделай системный промпт так, чтобы нейросеть учитывала полученные данные на протяжении всего диалога с пользователем.
Нейросеть не может задать вопрос в процессе диалога, все данные предоставлены до него в полученном тобой сообщении"""
            }, {"role": "user", "content": prompt}],
            temperature=0.3,
            max_output_tokens=1500
        )

        return response

    def prompt_from_settings(self, settings: dict) -> str:
        style = self.SETTINGS['style_type'][str(settings['set_style_type'])]
        tone = self.SETTINGS['tone'][str(settings['set_tone'])]
        size = self.SETTINGS['size'][str(settings['set_size'])]
        return f"Пиши в стиле:{style}, в тоне: {tone}, около {size} слов. Не уточняй по поводу вышеперечисленных пунктов и сконцентрируйся на вводе пользователя."

    def dialogue(self, answers: dict, org_info: str):
        client = openai.OpenAI(
            api_key=self.API_KEY,
            base_url="https://rest-assistant.api.cloud.yandex.net/v1",
            project=self.CLOUD_FOLDER
        )
        messages = [{"role": "system", "content": f"""
Используй форматирование MarkdownV2.
Ты опытный SMM специалист, ты помогаешь НКО сделать пост в их социальных сетях. 
Для получения информации ты сначала проводишь опрос, потом предлагешь текст поста. 
Ответы уже получены. Старайся не ссылаться на примеры в заданных тобой вопросах. 
Используй хештэги указанные пользователем и подходящие из описания НКО, указанного ниже.{org_info}"""}]
        for key, value in answers.items():
            messages.append({"role": "assistant", "content": self.QUESTIONS[key]["text"]})
            messages.append({"role": "user", "content": value})
        response = client.responses.create(
            model=f"gpt://{self.CLOUD_FOLDER}/{self.MODEL}",
            input=messages,
            temperature=0.8
        )

        return response


if __name__ == "__main__":
    ai = LinkAI()
    resp = ai.draw("Чёрный кот с большими красными глазами")
    # resp = ai.single_prompt(
    #    "Ты делаешь ИИ чат бота для помощи НКО в создании контента для соцсетей. Придумай список уточняющих вопросов, на которые должен ответить человек, чтобы бот смог сделать пост наиболее релевантым и живым")
    # resp = ai.create_system_prompt("НКО занимается помощью людям без определенного места жительства. Называется 'Ночлежка', работает в Москве")
    print(resp)
