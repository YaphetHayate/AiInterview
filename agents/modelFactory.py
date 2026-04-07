import os
from typing import Optional

from langchain_openai import ChatOpenAI
from pydantic import SecretStr


_process_manager_cache: Optional[ChatOpenAI] = None
_interviewer_chat_cache: Optional[ChatOpenAI] = None


def _get_process_manager_zhipu():
    global _process_manager_cache
    if _process_manager_cache is None:
        _process_manager_cache = ChatOpenAI(
            model="GLM-5.1",
            base_url="https://open.bigmodel.cn/api/paas/v4/",
            api_key=SecretStr(os.environ["ZHIPU_API_KEY"]),
            temperature=0,
        )
    return _process_manager_cache


def _get_process_manager_deepseek():
    global _process_manager_cache
    if _process_manager_cache is None:
        _process_manager_cache = ChatOpenAI(
            model="deepseek-chat",
            base_url="https://api.deepseek.com",
            api_key=SecretStr(os.environ["DEEPSEEK_API_KEY"]),
            temperature=0,
        )
    return _process_manager_cache


def _get_process_manager_qwen():
    global _process_manager_cache
    if _process_manager_cache is None:
        _process_manager_cache = ChatOpenAI(
            model="qwen-plus",
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            api_key=SecretStr(os.environ["DASHSCOPE_API_KEY"]),
            temperature=0,
        )
    return _process_manager_cache


def _get_interviewer_zhipu():
    global _interviewer_chat_cache
    if _interviewer_chat_cache is None:
        _interviewer_chat_cache = ChatOpenAI(
            model="GLM-5.1",
            base_url="https://open.bigmodel.cn/api/paas/v4/",
            api_key=SecretStr(os.environ["ZHIPU_API_KEY"]),
            temperature=0.7,
        )
    return _interviewer_chat_cache


def _get_interviewer_deepseek():
    global _interviewer_chat_cache
    if _interviewer_chat_cache is None:
        _interviewer_chat_cache = ChatOpenAI(
            model="deepseek-chat",
            base_url="https://api.deepseek.com",
            api_key=SecretStr(os.environ["DEEPSEEK_API_KEY"]),
            temperature=0.7,
        )
    return _interviewer_chat_cache


def _get_interviewer_qwen():
    global _interviewer_chat_cache
    if _interviewer_chat_cache is None:
        _interviewer_chat_cache = ChatOpenAI(
            model="qwen-plus",
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            api_key=SecretStr(os.environ["DASHSCOPE_API_KEY"]),
            temperature=0.7,
        )
    return _interviewer_chat_cache


manager_provider = "qwen"
interviewer_provider = "qwen"

_MANAGER_FACTORY_MAP = {
    "zhipu": _get_process_manager_zhipu,
    "deepseek": _get_process_manager_deepseek,
    "qwen": _get_process_manager_qwen,
}

_INTERVIEWER_FACTORY_MAP = {
    "zhipu": _get_interviewer_zhipu,
    "deepseek": _get_interviewer_deepseek,
    "qwen": _get_interviewer_qwen,
}


def get_process_manager():
    return _MANAGER_FACTORY_MAP[manager_provider]()


def get_interviewer_chat():
    return _INTERVIEWER_FACTORY_MAP[interviewer_provider]()


process_manager = get_process_manager
interviewer_chat = get_interviewer_chat
