import random

from locust import HttpUser, between, task

CATEGORIES = (
    "cookware",
    "tools",
    "kitchen-appliances",
    "footwear",
    "bags-luggage",
    "outdoor-gear",
    "electronics",
    "home-basics",
)

QUERIES = (
    "cast iron",
    "resolable boots",
    "repairable",
    "lifetime warranty",
    "stainless",
)


class Shopper(HttpUser):
    wait_time = between(1, 4)

    @task(5)
    def home(self):
        self.client.get("/", name="/")

    @task(4)
    def category(self):
        slug = random.choice(CATEGORIES)
        self.client.get(f"/category/{slug}", name="/category/{slug}")

    @task(4)
    def product(self):
        product_id = random.randint(1, 136)
        with self.client.get(
            f"/product/{product_id}", name="/product/{id}", catch_response=True
        ) as response:
            if response.status_code == 404:
                response.success()

    @task(3)
    def search(self):
        self.client.get("/search", params={"q": random.choice(QUERIES)}, name="/search")

    @task(1)
    def recommendations(self):
        self.client.get("/recommendations", name="/recommendations")

    @task(6)
    def send_events(self):
        batch = [
            {"type": "page_view", "path": "/"},
            {
                "type": "product_view",
                "product_id": random.randint(1, 136),
                "category": random.choice(CATEGORIES),
            },
            {"type": "search", "query": random.choice(QUERIES)},
            {"type": "dwell", "dwell_ms": random.randint(1_000, 60_000)},
        ]
        self.client.post("/api/events", json={"events": batch}, name="/api/events")
