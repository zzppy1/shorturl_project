# from locust import HttpUser, task
#
# class RedirectUser(HttpUser):
#     def on_start(self):
#         # 创建一个测试用的短链接，只做一次
#         resp = self.client.post("/api/shorten/", json={"url": "https://example.com/bench"})
#         if resp.status_code == 200:
#             self.short_code = resp.json()["short_code"]
#         else:
#             self.short_code = "1"  # fallback
#
#     @task
#     def follow_redirect(self):
#         # 注意：末尾加斜杠，与你的路由匹配
#         self.client.get(f"/{self.short_code}/", allow_redirects=False)

from locust import HttpUser, task

class RedirectUser(HttpUser):
    # 直接使用一个你已经手动创建好的、确定存在于数据库中的短码
    # 例如，你可以先在 Django shell 里创建一个短码，然后把它的值填在这里
    SHORT_CODE = "ETm8"   # 替换为你自己的真实短码

    @task
    def follow_redirect(self):
        # 注意末尾斜杠要与 Django 路由一致
        self.client.get(f"/{self.SHORT_CODE}/", allow_redirects=False)