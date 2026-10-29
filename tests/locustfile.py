from locust import HttpUser, task, between

class RecruiterUser(HttpUser):
    wait_time = between(1, 3)

    @task(1)
    def health_check(self):
        self.client.get("/health")

    @task(3)
    def analyze_cv(self):
        payload = {
            "cv": "John Doe - 10 years of experience in ML and NLP. Python, PyTorch, AWS.",
            "job_description": "Senior ML Engineer - 5+ years experience, Python, deep learning."
        }
        self.client.post("/api/v1/analyze", json=payload)