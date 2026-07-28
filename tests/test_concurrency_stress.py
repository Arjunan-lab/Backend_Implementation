"""Concurrent Multi-User Stress & Load Test Suite.

Simulates multiple users hitting API endpoints concurrently using ThreadPoolExecutor
to verify database session pooling, ML model thread-safety, and concurrent request handling.
"""

import os
import sys
import time
import unittest
from concurrent.futures import ThreadPoolExecutor, as_completed
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app
from app.config import settings

client = TestClient(app)


class ConcurrencyStressTestSuite(unittest.TestCase):
    """Stress test suite for multi-user concurrency performance."""

    @classmethod
    def setUpClass(cls):
        """Prepare authentication credentials for concurrency testing."""
        cls.farmer_email = "concurrent_farmer@example.com"
        cls.farmer_password = "Password123!"

        cls.admin_email = "concurrent_admin@example.com"
        cls.admin_password = "Password123!"

        # Register Farmer
        client.post(
            "/register",
            json={
                "email": cls.farmer_email,
                "password": cls.farmer_password,
                "confirm_password": cls.farmer_password,
                "language_id": 1,
                "role": "farmer",
            },
        )

        # Register Admin
        client.post(
            "/register",
            json={
                "email": cls.admin_email,
                "password": cls.admin_password,
                "confirm_password": cls.admin_password,
                "language_id": 1,
                "role": "admin",
                "admin_secret": settings.ADMIN_SECRET_KEY,
            },
        )

        # Obtain Farmer Token
        f_login = client.post(
            "/login",
            json={"email": cls.farmer_email, "password": cls.farmer_password},
        ).json()
        cls.farmer_token = f_login.get("access_token")

        # Obtain Admin Token
        a_login = client.post(
            "/admin/login",
            json={"email": cls.admin_email, "password": cls.admin_password},
        ).json()
        cls.admin_token = a_login.get("access_token")

    def test_01_concurrent_farmer_logins(self):
        """Simulate 30 concurrent farmer login requests simultaneously."""
        num_requests = 30
        success_count = 0

        def perform_login():
            res = client.post(
                "/login",
                json={"email": self.farmer_email, "password": self.farmer_password},
            )
            return res.status_code

        start_time = time.time()
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(perform_login) for _ in range(num_requests)]
            for future in as_completed(futures):
                if future.result() == 200:
                    success_count += 1

        elapsed = time.time() - start_time
        print(f"\n[STRESS TEST] 30 Concurrent Logins completed in {elapsed:.2f}s | Success: {success_count}/{num_requests}")
        self.assertEqual(success_count, num_requests)

    def test_02_concurrent_ml_crop_predictions(self):
        """Simulate 50 concurrent ML crop recommendation requests simultaneously."""
        num_requests = 50
        success_count = 0

        payload = {
            "soil_type": "Loamy",
            "nitrogen": 90.0,
            "phosphorus": 42.0,
            "potassium": 43.0,
            "ph": 6.5,
            "organic_carbon": 0.75,
            "electrical_conductivity": 1.2,
            "temperature": 25.5,
            "humidity": 80.0,
        }

        def predict():
            res = client.post(
                "/predict-crop",
                json=payload,
                headers={"Authorization": f"Bearer {self.farmer_token}"},
            )
            return res.status_code

        start_time = time.time()
        with ThreadPoolExecutor(max_workers=15) as executor:
            futures = [executor.submit(predict) for _ in range(num_requests)]
            for future in as_completed(futures):
                if future.result() == 200:
                    success_count += 1

        elapsed = time.time() - start_time
        print(f"[STRESS TEST] 50 Concurrent ML Crop Predictions completed in {elapsed:.2f}s | Success: {success_count}/{num_requests}")
        self.assertEqual(success_count, num_requests)

    def test_03_concurrent_soil_health_scores(self):
        """Simulate 30 concurrent soil health score calculations simultaneously."""
        num_requests = 30
        success_count = 0

        payload = {
            "soil_type": "Clayey",
            "nitrogen": 70.0,
            "phosphorus": 35.0,
            "potassium": 38.0,
            "ph": 6.2,
            "organic_carbon": 0.6,
            "electrical_conductivity": 1.0,
            "temperature": 27.0,
            "humidity": 70.0,
        }

        def score():
            res = client.post(
                "/soil-health-score",
                json=payload,
                headers={"Authorization": f"Bearer {self.farmer_token}"},
            )
            return res.status_code

        start_time = time.time()
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(score) for _ in range(num_requests)]
            for future in as_completed(futures):
                if future.result() == 200:
                    success_count += 1

        elapsed = time.time() - start_time
        print(f"[STRESS TEST] 30 Concurrent Soil Health Scores completed in {elapsed:.2f}s | Success: {success_count}/{num_requests}")
        self.assertEqual(success_count, num_requests)

    def test_04_concurrent_admin_user_queries(self):
        """Simulate 30 concurrent Admin user list queries simultaneously."""
        num_requests = 30
        success_count = 0

        def list_users():
            res = client.get(
                "/admin/users",
                headers={"Authorization": f"Bearer {self.admin_token}"},
            )
            return res.status_code

        start_time = time.time()
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(list_users) for _ in range(num_requests)]
            for future in as_completed(futures):
                if future.result() == 200:
                    success_count += 1

        elapsed = time.time() - start_time
        print(f"[STRESS TEST] 30 Concurrent Admin Queries completed in {elapsed:.2f}s | Success: {success_count}/{num_requests}")
        self.assertEqual(success_count, num_requests)

    def test_05_concurrent_chatbot_requests(self):
        """Simulate 20 concurrent AI chatbot questions simultaneously."""
        num_requests = 20
        success_count = 0

        def ask_chat():
            res = client.post(
                "/chat",
                json={"question": "What is the recommended fertilizer for cotton crop?"},
                headers={"Authorization": f"Bearer {self.farmer_token}"},
            )
            return res.status_code

        start_time = time.time()
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(ask_chat) for _ in range(num_requests)]
            for future in as_completed(futures):
                if future.result() == 200:
                    success_count += 1

        elapsed = time.time() - start_time
        print(f"[STRESS TEST] 20 Concurrent AI Chatbot Queries completed in {elapsed:.2f}s | Success: {success_count}/{num_requests}\n")
        self.assertEqual(success_count, num_requests)


if __name__ == "__main__":
    unittest.main()
