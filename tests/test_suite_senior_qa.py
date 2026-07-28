"""Senior QA Automation & Security Edge-Case Test Suite.

Executes positive, negative, boundary, worst-case security, and ML robustness test cases
against the FastAPI backend using Starlette/FastAPI TestClient.
"""

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import io
import unittest
from fastapi.testclient import TestClient
from app.main import app
from app.config import settings

client = TestClient(app)


class SeniorQABackendTestSuite(unittest.TestCase):
    """Comprehensive Test Suite created by Senior Test Engineer."""

    @classmethod
    def setUpClass(cls):
        """Seed test credentials once for performance."""
        cls.farmer_email = "qa_farmer_suite@example.com"
        cls.farmer_password = "Password123!"

        cls.admin_email = "qa_admin_suite@example.com"
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

        # Register Admin with secret
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

        # Login Farmer
        f_login = client.post(
            "/login",
            json={"email": cls.farmer_email, "password": cls.farmer_password},
        ).json()
        cls.farmer_token = f_login.get("access_token")

        # Login Admin
        a_login = client.post(
            "/admin/login",
            json={"email": cls.admin_email, "password": cls.admin_password},
        ).json()
        cls.admin_token = a_login.get("access_token")
        cls.admin_id = a_login.get("user_id")

    # -------------------------------------------------------------------------
    # 1. AUTHENTICATION & RBAC SECURITY TEST CASES
    # -------------------------------------------------------------------------

    def test_TC_AUTH_01_farmer_registration_success(self):
        """TC_AUTH_01: Verify valid farmer registration returns 201 Created."""
        import uuid
        unique_email = f"fresh_farmer_{uuid.uuid4().hex[:6]}@example.com"
        res = client.post(
            "/register",
            json={
                "email": unique_email,
                "password": "Password123!",
                "confirm_password": "Password123!",
                "language_id": 1,
            },
        )
        self.assertEqual(res.status_code, 201)

    def test_TC_AUTH_02_duplicate_email_registration_conflict(self):
        """TC_AUTH_02: Registering existing email returns 409 Conflict."""
        res = client.post(
            "/register",
            json={
                "email": self.farmer_email,
                "password": "Password123!",
                "confirm_password": "Password123!",
                "language_id": 1,
            },
        )
        self.assertEqual(res.status_code, 409)

    def test_TC_AUTH_03_mismatched_password_bad_request(self):
        """TC_AUTH_03: Mismatched confirm_password returns 400 Bad Request."""
        res = client.post(
            "/register",
            json={
                "email": "mismatch@example.com",
                "password": "Password123!",
                "confirm_password": "DifferentPassword123!",
                "language_id": 1,
            },
        )
        self.assertEqual(res.status_code, 400)

    def test_TC_AUTH_04_weak_password_validation(self):
        """TC_AUTH_04: Weak password (no uppercase/special) returns 422/400."""
        res = client.post(
            "/register",
            json={
                "email": "weak@example.com",
                "password": "weak",
                "confirm_password": "weak",
                "language_id": 1,
            },
        )
        self.assertIn(res.status_code, [400, 422])

    def test_TC_AUTH_05_admin_registration_invalid_secret_denied(self):
        """TC_AUTH_05: Registering admin with wrong admin_secret returns 403 Forbidden."""
        res = client.post(
            "/register",
            json={
                "email": "fake_admin@example.com",
                "password": "Password123!",
                "confirm_password": "Password123!",
                "language_id": 1,
                "role": "admin",
                "admin_secret": "WrongSecretKey",
            },
        )
        self.assertEqual(res.status_code, 403)

    def test_TC_AUTH_06_farmer_attempting_admin_login_denied(self):
        """TC_AUTH_06: Farmer credentials at /admin/login returns 403 Forbidden."""
        res = client.post(
            "/admin/login",
            json={"email": self.farmer_email, "password": self.farmer_password},
        )
        self.assertEqual(res.status_code, 403)

    def test_TC_AUTH_07_admin_attempting_farmer_login_denied(self):
        """TC_AUTH_07: Admin credentials at /login returns 403 Forbidden."""
        res = client.post(
            "/login",
            json={"email": self.admin_email, "password": self.admin_password},
        )
        self.assertEqual(res.status_code, 403)

    def test_TC_AUTH_08_tampered_jwt_token_unauthorized(self):
        """TC_AUTH_08: Request with tampered Bearer token returns 401 Unauthorized."""
        res = client.get(
            "/me",
            headers={"Authorization": "Bearer InvalidTamperedJwtToken.12345.67890"},
        )
        self.assertEqual(res.status_code, 401)

    # -------------------------------------------------------------------------
    # 2. ADMIN MANAGEMENT & RESTRICTED API TEST CASES
    # -------------------------------------------------------------------------

    def test_TC_ADMIN_01_admin_list_users_allowed(self):
        """TC_ADMIN_01: Admin accessing /admin/users returns 200 OK."""
        res = client.get(
            "/admin/users",
            headers={"Authorization": f"Bearer {self.admin_token}"},
        )
        self.assertEqual(res.status_code, 200)
        self.assertIsInstance(res.json(), list)

    def test_TC_ADMIN_02_farmer_list_users_denied(self):
        """TC_ADMIN_02: Farmer accessing /admin/users returns 403 Forbidden."""
        res = client.get(
            "/admin/users",
            headers={"Authorization": f"Bearer {self.farmer_token}"},
        )
        self.assertEqual(res.status_code, 403)

    def test_TC_ADMIN_03_admin_system_analytics_allowed(self):
        """TC_ADMIN_03: Admin accessing /admin/analytics returns 200 OK."""
        res = client.get(
            "/admin/analytics",
            headers={"Authorization": f"Bearer {self.admin_token}"},
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("total_users", data)
        self.assertIn("total_farmers", data)
        self.assertIn("total_admins", data)
        self.assertIn("active_users", data)
        self.assertIn("suspended_users", data)
        self.assertIn("recent_farmers_count", data)
        self.assertIn("users_by_region", data)

    def test_TC_ADMIN_04_farmer_system_analytics_denied(self):
        """TC_ADMIN_04: Farmer accessing /admin/analytics returns 403 Forbidden."""
        res = client.get(
            "/admin/analytics",
            headers={"Authorization": f"Bearer {self.farmer_token}"},
        )
        self.assertEqual(res.status_code, 403)

    def test_TC_ADMIN_05_update_user_status(self):
        """TC_ADMIN_05: Admin updating a user's status to suspended works cleanly."""
        # Create temporary farmer to suspend
        import uuid
        temp_email = f"suspend_test_{uuid.uuid4().hex[:6]}@example.com"
        reg = client.post(
            "/register",
            json={
                "username": "suspend_me",
                "email": temp_email,
                "password": "Password123!",
                "confirm_password": "Password123!",
                "language_id": 1,
                "region": "Telangana",
            },
        )
        self.assertEqual(reg.status_code, 201)

        # Fetch user list to get target user ID
        users_list = client.get(
            "/admin/users",
            headers={"Authorization": f"Bearer {self.admin_token}"},
        ).json()
        target_user = next((u for u in users_list if u["email"] == temp_email), None)
        self.assertIsNotNone(target_user)
        self.assertEqual(target_user["username"], "suspend_me")
        self.assertEqual(target_user["region"], "Telangana")

        # Admin suspends user
        sus_res = client.put(
            f"/admin/users/{target_user['id']}/status",
            json={"status": "suspended"},
            headers={"Authorization": f"Bearer {self.admin_token}"},
        )
        self.assertEqual(sus_res.status_code, 200)
        self.assertEqual(sus_res.json()["user"]["status"], "suspended")

        # Suspended user attempt login -> Expect 403 Forbidden
        login_res = client.post(
            "/login",
            json={"email": temp_email, "password": "Password123!"},
        )
        self.assertEqual(login_res.status_code, 403)

    def test_TC_ADMIN_06_update_user_role_multi_identifier(self):
        """TC_ADMIN_06: Admin updating role by ID, email, or username works and returns structured response."""
        import uuid
        temp_email = f"role_test_{uuid.uuid4().hex[:6]}@example.com"
        reg = client.post(
            "/register",
            json={
                "username": "role_target",
                "email": temp_email,
                "password": "Password123!",
                "confirm_password": "Password123!",
                "language_id": 1,
            },
        )
        self.assertEqual(reg.status_code, 201)

        # Update by email
        up_email = client.put(
            f"/admin/users/{temp_email}/role",
            json={"role": "admin"},
            headers={"Authorization": f"Bearer {self.admin_token}"},
        )
        self.assertEqual(up_email.status_code, 200)
        self.assertEqual(up_email.json()["user"]["role"], "admin")
        self.assertEqual(up_email.json()["user"]["username"], "role_target")

        # Demote by username back to farmer
        up_user = client.put(
            "/admin/users/role_target/role",
            json={"role": "farmer"},
            headers={"Authorization": f"Bearer {self.admin_token}"},
        )
        self.assertEqual(up_user.status_code, 200)
        self.assertEqual(up_user.json()["user"]["role"], "farmer")

    def test_TC_ADMIN_07_delete_user_account(self):
        """TC_ADMIN_07: Admin deleting user account removes account (204 No Content)."""
        import uuid
        temp_email = f"del_test_{uuid.uuid4().hex[:6]}@example.com"
        client.post(
            "/register",
            json={
                "username": "del_me",
                "email": temp_email,
                "password": "Password123!",
                "confirm_password": "Password123!",
                "language_id": 1,
            },
        )

        del_res = client.delete(
            f"/admin/users/{temp_email}",
            headers={"Authorization": f"Bearer {self.admin_token}"},
        )
        self.assertEqual(del_res.status_code, 204)

        # Verify login now fails with 401
        login_res = client.post(
            "/login",
            json={"email": temp_email, "password": "Password123!"},
        )
        self.assertEqual(login_res.status_code, 401)

    def test_TC_ADMIN_08_self_protection_rules(self):
        """TC_ADMIN_08: Admin cannot demote, suspend, or delete their own account."""
        # Attempt self-demotion
        demote_res = client.put(
            f"/admin/users/{self.admin_email}/role",
            json={"role": "farmer"},
            headers={"Authorization": f"Bearer {self.admin_token}"},
        )
        self.assertEqual(demote_res.status_code, 400)

        # Attempt self-suspension
        sus_res = client.put(
            f"/admin/users/{self.admin_email}/status",
            json={"status": "suspended"},
            headers={"Authorization": f"Bearer {self.admin_token}"},
        )
        self.assertEqual(sus_res.status_code, 400)

        # Attempt self-deletion
        del_res = client.delete(
            f"/admin/users/{self.admin_email}",
            headers={"Authorization": f"Bearer {self.admin_token}"},
        )
        self.assertEqual(del_res.status_code, 400)

    # -------------------------------------------------------------------------
    # 3. MACHINE LEARNING MODEL BOUNDARY & EDGE CASES
    # -------------------------------------------------------------------------

    def test_TC_ML_01_crop_recommendation_valid(self):
        """TC_ML_01: Valid NPK parameters return crop recommendation (200 OK)."""
        res = client.post(
            "/predict-crop",
            json={
                "soil_type": "Loamy",
                "nitrogen": 90.0,
                "phosphorus": 42.0,
                "potassium": 43.0,
                "ph": 6.5,
                "organic_carbon": 0.75,
                "electrical_conductivity": 1.2,
                "temperature": 25.5,
                "humidity": 80.0,
            },
            headers={"Authorization": f"Bearer {self.farmer_token}"},
        )
        self.assertEqual(res.status_code, 200)

    def test_TC_ML_02_crop_recommendation_missing_field(self):
        """TC_ML_02: Missing required parameter returns 422 Unprocessable Entity."""
        res = client.post(
            "/predict-crop",
            json={
                "soil_type": "Loamy",
                "nitrogen": 90.0,
                # phosphorus missing
                "potassium": 43.0,
            },
            headers={"Authorization": f"Bearer {self.farmer_token}"},
        )
        self.assertEqual(res.status_code, 422)

    def test_TC_ML_03_soil_health_score_valid(self):
        """TC_ML_03: Soil health score endpoint returns numeric score (200 OK)."""
        res = client.post(
            "/soil-health-score",
            json={
                "soil_type": "Clayey",
                "nitrogen": 70.0,
                "phosphorus": 35.0,
                "potassium": 38.0,
                "ph": 6.2,
                "organic_carbon": 0.6,
                "electrical_conductivity": 1.0,
                "temperature": 27.0,
                "humidity": 70.0,
            },
            headers={"Authorization": f"Bearer {self.farmer_token}"},
        )
        self.assertEqual(res.status_code, 200)

    def test_TC_ML_04_nutrient_deficiency_valid(self):
        """TC_ML_04: Nutrient deficiency endpoint returns deficiency list (200 OK)."""
        res = client.post(
            "/nutrient-analysis",
            json={
                "soil_type": "Sandy",
                "nitrogen": 40.0,
                "phosphorus": 15.0,
                "potassium": 20.0,
                "ph": 5.5,
                "organic_carbon": 0.4,
                "electrical_conductivity": 0.8,
                "temperature": 30.0,
                "humidity": 50.0,
            },
            headers={"Authorization": f"Bearer {self.farmer_token}"},
        )
        self.assertEqual(res.status_code, 200)

    # -------------------------------------------------------------------------
    # 4. FILE UPLOAD & IMAGE CLASSIFICATION EDGE CASES
    # -------------------------------------------------------------------------

    def test_TC_IMG_01_non_image_file_rejected(self):
        """TC_IMG_01: Uploading text file to /predict-image returns 400 Bad Request."""
        text_file = io.BytesIO(b"This is a text file, not a soil image.")
        res = client.post(
            "/predict-image",
            files={"file": ("malicious.txt", text_file, "text/plain")},
            headers={"Authorization": f"Bearer {self.farmer_token}"},
        )
        self.assertIn(res.status_code, [400, 422])

    # -------------------------------------------------------------------------
    # 5. CHATBOT & MULTILINGUAL EDGE CASES
    # -------------------------------------------------------------------------

    def test_TC_CHAT_01_valid_agri_question(self):
        """TC_CHAT_01: Agriculture question returns 200 OK response."""
        res = client.post(
            "/chat",
            json={"question": "What is the best fertilizer for wheat crop?"},
            headers={"Authorization": f"Bearer {self.farmer_token}"},
        )
        self.assertEqual(res.status_code, 200)

    def test_TC_CHAT_02_accepts_message_alias_key(self):
        """TC_CHAT_02: Payload using 'message' key instead of 'question' succeeds."""
        res = client.post(
            "/chat",
            json={"message": "How to treat nitrogen deficiency in maize?"},
            headers={"Authorization": f"Bearer {self.farmer_token}"},
        )
        self.assertEqual(res.status_code, 200)

    def test_TC_CHAT_03_non_agri_question_filtered(self):
        """TC_CHAT_03: Off-topic non-agriculture question returns polite guidance response."""
        res = client.post(
            "/chat",
            json={"question": "What is the capital of France?"},
            headers={"Authorization": f"Bearer {self.farmer_token}"},
        )
        self.assertEqual(res.status_code, 200)
        self.assertIn("agriculture", res.json().get("response", "").lower())

    # -------------------------------------------------------------------------
    # 6. SYSTEM & HISTORY ENDPOINTS
    # -------------------------------------------------------------------------

    def test_TC_SYS_01_root_health_check(self):
        """TC_SYS_01: Root health check returns online status (200 OK)."""
        res = client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json().get("status"), "online")


if __name__ == "__main__":
    unittest.main()
