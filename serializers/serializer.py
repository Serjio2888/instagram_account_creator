from typing import Iterator, List, Dict, Any, Union

from insta_pb2 import InstaRegisterAccountsTaskMessage, AccountCredentialsMessage
from useid_pb2 import TaskProgressMessage


class GrpcSerializer:
    @staticmethod
    def _prepare_account(account: Dict[str, Any]) -> Dict[str, str]:
        return {"email": account.get("email"), "password": account.get("password")}

    @staticmethod
    def prepare_new_account(
        items: List[Dict[str, Any]]
    ) -> Iterator[InstaRegisterAccountsTaskMessage]:
        return iter(
            [
                AccountCredentialsMessage(**GrpcSerializer._prepare_account(x))
                for x in items
            ]
        )

    @staticmethod
    def prepare_task_message(
        task_id: str, current_percentage: Union[int, float], task_status: str
    ) -> Iterator[TaskProgressMessage]:
        return iter(
            [
                TaskProgressMessage(
                    taskId=str(task_id),
                    currentPercentage=current_percentage,
                    taskStatus=task_status,
                    taskStatusInfo="OK",
                )
            ]
        )
