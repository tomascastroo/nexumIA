from locust import HttpUser, task, between

class DebtorUser(HttpUser):
    wait_time = between(1, 3)

    @task
    def get_debtors(self):
        self.client.get("/debtors?dataset_id=1") 