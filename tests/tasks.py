import aiounittest

from unittest import skip
from services.task_service import TaskService


class TaskServiceTestCase(aiounittest.AsyncTestCase):

    def setUp(self):
        self.task_service = TaskService()

    async def test_process_file_invalid_id(self):
        with self.assertRaises(ValueError):
            await self.task_service.process_file("123131221312312")

    @skip
    async def test_process_file(self):
        # @TODO Handle RuntimeError: Event loop is closed
        await self.task_service.process_file("6227d8a46d353e16a762b314")

    @skip
    async def test_finalise(self):
        # @TODO Implement it
        await self.task_service.finalise_file("6227d8a46d353e16a762b314",
                                              "6227d8a46d353e16a762b314",
                                              {
                                                  "": ""
                                              })
