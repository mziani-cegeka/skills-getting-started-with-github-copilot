"""
Tests for the High School Management System API
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app

client = TestClient(app)


class TestGetActivities:
    """Tests for the GET /activities endpoint"""

    def test_get_all_activities(self):
        """Test that all activities are returned"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) > 0
        assert "Chess Club" in data
        assert "Programming Class" in data

    def test_activities_have_required_fields(self):
        """Test that each activity has required fields"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_info in data.items():
            assert "description" in activity_info
            assert "schedule" in activity_info
            assert "max_participants" in activity_info
            assert "participants" in activity_info
            assert isinstance(activity_info["participants"], list)


class TestSignupForActivity:
    """Tests for the POST /activities/{activity_name}/signup endpoint"""

    def test_signup_new_student(self):
        """Test signing up a new student for an activity"""
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "test.student@mergington.edu"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "test.student@mergington.edu" in data["message"]
        assert "Chess Club" in data["message"]

    def test_signup_already_registered(self):
        """Test that signing up an already registered student returns 400"""
        email = "already.registered@mergington.edu"
        
        # First signup
        response1 = client.post(
            "/activities/Soccer Team/signup",
            params={"email": email}
        )
        assert response1.status_code == 200
        
        # Try to signup again with the same email
        response2 = client.post(
            "/activities/Soccer Team/signup",
            params={"email": email}
        )
        assert response2.status_code == 400
        assert "already signed up" in response2.json()["detail"]

    def test_signup_nonexistent_activity(self):
        """Test signing up for an activity that doesn't exist"""
        response = client.post(
            "/activities/Nonexistent Activity/signup",
            params={"email": "test@mergington.edu"}
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_signup_multiple_activities(self):
        """Test that a student can sign up for multiple different activities"""
        email = "multi.tasker@mergington.edu"
        
        response1 = client.post(
            "/activities/Chess Club/signup",
            params={"email": email}
        )
        assert response1.status_code == 200
        
        response2 = client.post(
            "/activities/Drama Club/signup",
            params={"email": email}
        )
        assert response2.status_code == 200


class TestUnregisterFromActivity:
    """Tests for the POST /activities/{activity_name}/unregister endpoint"""

    def test_unregister_registered_student(self):
        """Test unregistering a student from an activity they're in"""
        email = "unregister.test@mergington.edu"
        
        # Sign up first
        client.post(
            "/activities/Basketball Club/signup",
            params={"email": email}
        )
        
        # Then unregister
        response = client.post(
            "/activities/Basketball Club/unregister",
            params={"email": email}
        )
        assert response.status_code == 200
        data = response.json()
        assert "Unregistered" in data["message"]
        assert email in data["message"]

    def test_unregister_not_registered(self):
        """Test that unregistering a non-registered student returns 400"""
        response = client.post(
            "/activities/Math Olympiad/unregister",
            params={"email": "not.registered@mergington.edu"}
        )
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"]

    def test_unregister_nonexistent_activity(self):
        """Test unregistering from an activity that doesn't exist"""
        response = client.post(
            "/activities/Ghost Activity/unregister",
            params={"email": "test@mergington.edu"}
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_signup_and_unregister_cycle(self):
        """Test signing up and unregistering multiple times"""
        email = "cycle.test@mergington.edu"
        activity = "Art Workshop"
        
        # Sign up
        response1 = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert response1.status_code == 200
        
        # Unregister
        response2 = client.post(
            f"/activities/{activity}/unregister",
            params={"email": email}
        )
        assert response2.status_code == 200
        
        # Sign up again
        response3 = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert response3.status_code == 200


class TestRootEndpoint:
    """Tests for the root endpoint"""

    def test_root_redirects(self):
        """Test that the root endpoint redirects to /static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]


class TestIntegration:
    """Integration tests combining multiple endpoints"""

    def test_full_user_workflow(self):
        """Test a complete user workflow: get activities, sign up, verify signup, unregister"""
        # Get all activities
        response = client.get("/activities")
        assert response.status_code == 200
        activities = response.json()
        activity_name = list(activities.keys())[0]
        
        email = "workflow.test@mergington.edu"
        
        # Sign up for an activity
        signup_response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        assert signup_response.status_code == 200
        
        # Get activities again to verify signup
        activities_after = client.get("/activities").json()
        assert email in activities_after[activity_name]["participants"]
        
        # Unregister
        unregister_response = client.post(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        assert unregister_response.status_code == 200
        
        # Verify unregistered
        activities_final = client.get("/activities").json()
        assert email not in activities_final[activity_name]["participants"]
