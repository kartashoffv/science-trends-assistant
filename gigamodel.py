from langchain.chat_models.gigachat import GigaChat
from langchain_core.prompts import ChatPromptTemplate
import os
from dotenv import load_dotenv
load_dotenv()

CREDENTIALS = os.getenv('OPENAI_API_KEY')


class GigaModel:
    def __init__(self):
        self.llm = GigaChat(
            credentials=CREDENTIALS,
            verify_ssl_certs=False,
            model="GigaChat-Pro",
            scope="GIGACHAT_API_CORP",
        )

    def answer(self, context):

        template = ChatPromptTemplate.from_messages(
            [
                ("system", '''Вы полезный эксперт в области анализа научных трендов и инсайтов.
                Вам будет показана информация из аннотаций научных статей.
                Определите ключевые тренды и инсайты в представленных научных статьях'''),
                ("human", "Информация из научных статей: {context}"),
            ]
        )
        prompt_value = template.invoke({"context": context})
        response = self.llm.ainvoke(prompt_value)
        return response

    def talk(self, question):
        response = self.llm.ainvoke(question)
        response = str(response.content)
        return response
