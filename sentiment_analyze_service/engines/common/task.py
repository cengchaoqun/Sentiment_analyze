import asyncio
import uuid
from dataclasses import dataclass
from typing import Coroutine

from mistune.plugins.task_lists import task_lists


@dataclass(slots=True)
class ResearchTask:
    query:str
    task_id:str

class TaskManager:

    def __init__(self):
        self.research_tasks:dict[str,ResearchTask]={}
        self.backgrounds:set[asyncio.Task] = set()

    def create_research_task(self,query:str)->ResearchTask:
        """
        职责：创建任务记录
        :param query:
        :return:
        """
        # 1.创建ResearchTask
        task_id = uuid.uuid4().hex
        research_task = ResearchTask(query=query,task_id=task_id)

        # 2.保存研究任务id和研究任务对象（未来可以根据任务id查询到研究结果的md文件）
        self.research_tasks[task_id] = research_task

        # 3.返回
        return research_task

    def create_background_task(self,coro:Coroutine):
        """
        职责：将协程对象，交给事件循环在后台并发执行
        特点：“一个”事件循环线程并发执行两个异步任务
        :param coro:
        :return:
        """
        task = asyncio.create_task(coro)
        self.backgrounds.add(task)
        task.add_done_callback(self.backgrounds.discard)

task_manager = TaskManager()
