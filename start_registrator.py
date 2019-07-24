from multiprocessing import Process

from rest_api import start_healthcheck
from worker.registraton_worker import RegistrationWorker

if __name__ == "__main__":
    mass_registrator = RegistrationWorker()
    healthcheck_process = Process(target=start_healthcheck)
    healthcheck_process.start()
    matcher_process = Process(target=mass_registrator.start_async)
    matcher_process.start()
    healthcheck_process.join()
    matcher_process.join()
