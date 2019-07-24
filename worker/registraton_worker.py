import asyncio
from threading import Thread
from time import sleep

import grpc
from grpc._channel import _Rendezvous
from loguru import logger

from config import GRPC_HOST
from insta_pb2 import InstaRegisterAccountsTaskMessage
from insta_pb2_grpc import InstaDataStub
from registrator.generate_account import AccountCreator
from serializers.serializer import GrpcSerializer
from useid_pb2 import TaskStatus, Empty


class RegistrationWorker:
    def __init__(self):
        channel = grpc.insecure_channel(GRPC_HOST)
        self.stub = InstaDataStub(channel)
        self.logged = False
        task = self._get_task()
        if task:
            self._setup(task)

        self.pending = [task] if task else []
        self.task = None

    def _get_task(self) -> InstaRegisterAccountsTaskMessage:
        try:
            return self.stub.GetRegisterAccountsTask(Empty())
        except _Rendezvous:
            pass

    def _setup(self, task: InstaRegisterAccountsTaskMessage):
        """ RUN my task for create new insta user """
        self.create_insta_user = AccountCreator(
            task.smtpUser,
            task.smtpPassword,
            task.smtpServer,
            task.numOfAccounts,
            self.stub,
        )
        self.logged = True

    def start_async(self):
        main_thread = Thread(target=self._start_with_asyncio, name="RegistrationWorker")
        main_thread.start()
        task_thread = Thread(
            target=self._task_status, name="RegistrationWorkerTaskStatus"
        )
        task_thread.start()

    def _start_with_asyncio(self):
        remote_loop = asyncio.new_event_loop()
        logger.info("RegistrationWorker staring...")
        remote_loop.run_until_complete(self.polling())
        try:
            remote_loop.run_forever()
        except KeyboardInterrupt:
            pass
            logger.info("RegistrationWorker shutting down...")
        finally:
            remote_loop.close()

    def _task_status(self):
        while True:
            completed = False
            if not self.task:
                continue
            if self.create_insta_user.task_percentage == 100:
                completed = True
            if not completed:
                current_percentage = self.create_insta_user.task_percentage
                status = self.create_insta_user.status
                if status == 0:
                    task_status = TaskStatus.NORMAL
                elif status == 1:
                    task_status = TaskStatus.ACCOUNT_EXPIRED_PERMANENTLY
                elif status == 2:
                    task_status = TaskStatus.ACCOUNT_EXPIRED_TEMPORALLY
                else:
                    task_status = TaskStatus.UNKNOWN_ERROR
                responses = self.stub.TaskProgress(
                    GrpcSerializer.prepare_task_message(
                        self.task.id, current_percentage, task_status
                    )
                )
                for response in responses:
                    if response.status == 0:
                        pass
                    elif response.status == 1:
                        self.create_insta_user.to_abort = True
            sleep(3)

    async def polling(self):
        logger.info("RegistrationWorker started")
        while True:
            if self.pending:
                self.task = self.pending.pop()
                if not self.logged and self.task:
                    self._setup(self.task)

                await self.create_insta_user.get_accounts()
            sleep(3)
            get_task = self._get_task()
            self.pending = [get_task] if get_task else []
