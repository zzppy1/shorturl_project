from locust import HttpUser, task, between
import random

class ShortUrlUser(HttpUser):
    wait_time=between(0.5,1.5)
    def on_start(self):
        resp=self.client.post("/api/shorten/",json={"url":"https://example.com/test0"})
        if resp.status_code==200:
            self.test_short_code=resp.json()["short_code"]
        else:
            self.test_short_code="1"

        @task(3)
        def follow_redirect(self):
            self.client.get(f"/{self.test_short_code}",allow_redirects=False)

        @task(1)
        def creat_short(self):
            self.client.post("/api/shorten/",json={"url":"https://example.com/"+str(random.randint(1,10000))})
