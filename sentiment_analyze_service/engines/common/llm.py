"""
封装LLM客户端
根据角色返回对应角色的客户端，调用LLM方法（文本内容，结构化对象）
"""
from typing import TypeVar

from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage
from pydantic import BaseModel

from sentiment_analyze_service.engines.common.retryer import with_retry
from sentiment_analyze_service.engines.contract.config import get_config_settings
from sentiment_analyze_service.engines.contract.role import RoleID, ROLE_METADATA

T = TypeVar("T", bound=BaseModel) # 让输入的模型类型与返回对象类型对应起来。


class LLMClient:
    def __init__(self,
                 model_name: str,
                 model_provider: str,
                 api_key: str,
                 base_url: str,
                 ):
        self.model_name = model_name
        self.model_provider = model_provider
        self.api_key = api_key
        self.base_url = base_url

    @classmethod
    def from_role(cls, role: RoleID) -> "LLMClient":
        """
        职责：根据不同的Agent角色，获取对应角色LLM客户端
        :param role:
        :return:
        """
        # 1.根据角色id获取到对应的LLM配置信息
        llm_config_prefix = ROLE_METADATA[role].llm_config_prefix

        # 2.获取settings
        config_settings = get_config_settings()
        return cls(model_name=getattr(config_settings, f"{llm_config_prefix}_MODEL_NAME"),
                   model_provider=getattr(config_settings, f"{llm_config_prefix}_MODEL_PROVIDER"),
                   api_key=getattr(config_settings, f"{llm_config_prefix}_API_KEY"),
                   base_url=getattr(config_settings, f"{llm_config_prefix}_BASE_URL"))
    @with_retry
    async def generate_text(self, system_prompt: str, user_prompt: str) -> str:
        """
        1. 获取到chat_model实例
        2. 调用LLM
        3. 获取响应的文本内容
        使用流式的方式获取非流式的输出结果
        优点：针对长文本生成，可以减少服务端网络超时的发生。
        :param system_prompt:
        :param user_prompt:
        :return:
        """
        # 1.将用户以及系统的提示词内容封装到标准的消息对象中
        messages = _build_messages(system_prompt, user_prompt)

        # 2.创建chat_model实例对象
        chat_model = self._get_chat_model()

        # 3.调用
        final_text: list[str] = []
        try:
            async for chunk in chat_model.astream(messages):
                if text := chunk.text:
                    final_text.append(text)
        except Exception as exc:
            raise ValueError(f"{self.model_name}返回文本失败：{str(exc)}")

        # 4.返回
        return "".join(final_text)
    @with_retry
    async def generate_object(self, system_prompt: str, user_prompt: str, structed_object: type[T]) -> T:
        """
        json_object:输出是一个json格式字符串（提示词：返回json格式）
        function_calling:API（层面）现代大语言模型都支持工具调用
        json_schema：最稳的（物理）-->保证一定获取结构化对象【DeepSeek模型处理】--最准
        :param system_prompt:
        :param user_prompt:
        :return:
        """
        # 1.将用户以及系统的提示词内容封装到标准的消息对象中
        messages = _build_messages(system_prompt, user_prompt)

        # 2.创建chat_model实例对象
        chat_model = self._get_chat_model()

        # 3.为模型调用时取指定结构化输出
        structed_runnable_object = chat_model.with_structured_output(structed_object, method="json_schema")

        # 4.调用
        try:
            structed_response = await structed_runnable_object.ainvoke(messages)
        except Exception as exc:
            raise ValueError(f"{self.model_name}返回结构化输出失败：{str(exc)}")

        if structed_response is None:
            raise ValueError(f"{self.model_name}返回结构化输出为空")

        # 4.返回
        return structed_response

    def _get_chat_model(self) -> BaseChatModel:
        return init_chat_model(
            model_provider=self.model_provider,
            model=self.model_name,
            api_key=self.api_key,
            base_url=self.base_url
        )


def _build_messages(system_prompt: str, user_prompt: str) -> list[BaseMessage]:
    return [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ]


if __name__ == '__main__':
    llm_client = LLMClient.from_role("insight")
    print(llm_client.model_name)
    print(llm_client.model_provider)
    print("==============")
    llm_client1 = LLMClient.from_role("media")
