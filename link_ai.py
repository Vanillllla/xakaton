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

    def content_plan(self, prompt):
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
                "content": """Создай контент-план для социальных сетей НКО [Название НКО] на период [указать временной промежуток, например, месяц] с учётом следующих параметров:

1. **Цель и задачи:** опиши основные цели и задачи НКО [Название НКО] в социальных сетях.
2. **Целевая аудитория:** укажи основные группы людей, которых нужно охватить (например, молодёжь, семьи с детьми, пожилые люди).
3. **Тематика постов:** предложи разнообразие тем для публикаций, которые будут интересны целевой аудитории (например, социальные проблемы, благотворительные акции, истории успеха, советы и рекомендации).
4. **Частота публикаций:** определи оптимальное количество постов в день/неделю для каждой социальной сети (например, 3–5 постов в неделю).
5. **Формат постов:** укажи предпочтительные форматы публикаций (например, текст, фото, видео, инфографика).
6. **Взаимодействие с аудиторией:** предложи способы взаимодействия с аудиторией (например, комментарии, опросы, конкурсы).
7. **Аналитика и обратная связь:** опиши, какие метрики можно использовать для оценки эффективности публикаций (например, количество лайков, комментариев, репостов).
8. **Специальные мероприятия и акции:** включи в план проведение специальных мероприятий и акций, которые помогут привлечь внимание к деятельности НКО.
9. **Привлечение новых подписчиков:** предложи способы привлечения новых подписчиков в социальные сети НКО.
10. **Упоминание конкурентов и коллег:** определи, нужно ли учитывать деятельность других НКО в контент-плане, и если да, то каким образом."""
            }, {"role": "user", "content": prompt}],
            temperature=0.8,
            max_output_tokens=1500
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
                "content": """Ты эксперт в создании промтов для yandexgpt-lite.
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

    def dialogue(self, answers: dict):
        questions = self.SETTINGS["questions"]
        client = openai.OpenAI(
            api_key=self.API_KEY,
            base_url="https://rest-assistant.api.cloud.yandex.net/v1",
            project=self.CLOUD_FOLDER
        )
        messages = [{"role": "system", "content": answers['system']}]
        for key, value in answers:
            if key != "system":
                messages.append({"role": "assistant", "content": questions[key]["text"]})
                messages.append({"role": "user", "content": value})
        response = client.responses.create(
            model=f"gpt://{self.CLOUD_FOLDER}/{self.MODEL}",
            input=messages,
            temperature=0.8
        )

        return response


if __name__ == "__main__":
    ai = LinkAI()
    # ai.draw("Чёрный кот с большими красными глазами")
    resp = ai.single_prompt(
        "Ты делаешь ИИ чат бота для помощи НКО в создании контента для соцсетей. Придумай список уточняющих вопросов, на которые должен ответить человек, чтобы бот смог сделать пост наиболее релевантым и живым")
    # resp = ai.create_system_prompt("НКО занимается помощью людям без определенного места жительства. Называется 'Ночлежка', работает в Москве")
    print(resp.output_text)
