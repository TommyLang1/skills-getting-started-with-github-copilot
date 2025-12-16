"""
Tests for the Mergington High School Activities API
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities

# Create a test client
client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities to initial state before each test"""
    global activities
    activities.clear()
    activities.update({
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        },
        "Gym Class": {
            "description": "Physical education and sports activities",
            "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
            "max_participants": 30,
            "participants": ["john@mergington.edu", "olivia@mergington.edu"]
        },
    })
    yield
    activities.clear()


class TestRoot:
    """Tests for root endpoint"""
    
    def test_root_redirects_to_static(self):
        """Root should redirect to static index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]


class TestGetActivities:
    """Tests for GET /activities endpoint"""
    
    def test_get_activities_returns_all(self):
        """Should return all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data
    
    def test_activity_structure(self):
        """Activity should have correct structure"""
        response = client.get("/activities")
        data = response.json()
        activity = data["Chess Club"]
        
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity
        assert isinstance(activity["participants"], list)
    
    def test_participants_list(self):
        """Participants list should contain correct emails"""
        response = client.get("/activities")
        data = response.json()
        participants = data["Chess Club"]["participants"]
        
        assert "michael@mergington.edu" in participants
        assert "daniel@mergington.edu" in participants


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_new_participant(self):
        """Should successfully sign up a new participant"""
        response = client.post(
            "/activities/Chess Club/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "newstudent@mergington.edu" in data["message"]
    
    def test_signup_adds_to_participants(self):
        """Signup should add email to participants list"""
        client.post(
            "/activities/Chess Club/signup?email=newstudent@mergington.edu"
        )
        response = client.get("/activities")
        participants = response.json()["Chess Club"]["participants"]
        
        assert "newstudent@mergington.edu" in participants
    
    def test_signup_duplicate_fails(self):
        """Should not allow duplicate signups"""
        response = client.post(
            "/activities/Chess Club/signup?email=michael@mergington.edu"
        )
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"].lower()
    
    def test_signup_nonexistent_activity(self):
        """Should fail for non-existent activity"""
        response = client.post(
            "/activities/Fake Club/signup?email=student@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()
    
    def test_signup_multiple_participants(self):
        """Should allow multiple different participants"""
        emails = ["student1@mergington.edu", "student2@mergington.edu", "student3@mergington.edu"]
        for email in emails:
            response = client.post(
                f"/activities/Programming Class/signup?email={email}"
            )
            assert response.status_code == 200
        
        response = client.get("/activities")
        participants = response.json()["Programming Class"]["participants"]
        for email in emails:
            assert email in participants


class TestUnregisterFromActivity:
    """Tests for DELETE /activities/{activity_name}/participants endpoint"""
    
    def test_unregister_existing_participant(self):
        """Should successfully unregister an existing participant"""
        response = client.delete(
            "/activities/Chess Club/participants?email=michael@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "michael@mergington.edu" not in data["participants"]
    
    def test_unregister_removes_from_participants(self):
        """Unregister should remove email from participants list"""
        client.delete(
            "/activities/Chess Club/participants?email=michael@mergington.edu"
        )
        response = client.get("/activities")
        participants = response.json()["Chess Club"]["participants"]
        
        assert "michael@mergington.edu" not in participants
        assert "daniel@mergington.edu" in participants  # Other should remain
    
    def test_unregister_not_signed_up(self):
        """Should fail when unregistering non-existent participant"""
        response = client.delete(
            "/activities/Chess Club/participants?email=nothere@mergington.edu"
        )
        assert response.status_code == 400
        data = response.json()
        assert "not signed up" in data["detail"].lower()
    
    def test_unregister_nonexistent_activity(self):
        """Should fail for non-existent activity"""
        response = client.delete(
            "/activities/Fake Club/participants?email=student@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()
    
    def test_unregister_returns_updated_list(self):
        """Response should contain updated participants list"""
        response = client.delete(
            "/activities/Chess Club/participants?email=michael@mergington.edu"
        )
        data = response.json()
        
        assert "participants" in data
        assert "max_participants" in data
        assert isinstance(data["participants"], list)
        assert len(data["participants"]) == 1
        assert data["participants"][0] == "daniel@mergington.edu"


class TestIntegration:
    """Integration tests for signup and unregister flows"""
    
    def test_signup_then_unregister(self):
        """Should be able to signup then unregister"""
        email = "tempstudent@mergington.edu"
        
        # Signup
        response = client.post(
            f"/activities/Programming Class/signup?email={email}"
        )
        assert response.status_code == 200
        
        # Verify signup
        response = client.get("/activities")
        assert email in response.json()["Programming Class"]["participants"]
        
        # Unregister
        response = client.delete(
            f"/activities/Programming Class/participants?email={email}"
        )
        assert response.status_code == 200
        
        # Verify unregister
        response = client.get("/activities")
        assert email not in response.json()["Programming Class"]["participants"]
    
    def test_multiple_signups_and_unregisters(self):
        """Should handle multiple signup/unregister operations"""
        activity = "Gym Class"
        emails = ["test1@mergington.edu", "test2@mergington.edu", "test3@mergington.edu"]
        
        # Sign up all
        for email in emails:
            response = client.post(f"/activities/{activity}/signup?email={email}")
            assert response.status_code == 200
        
        # Verify all signed up
        response = client.get("/activities")
        participants = response.json()[activity]["participants"]
        assert len(participants) == 5  # Original 2 + 3 new
        
        # Unregister some
        for email in emails[:2]:
            response = client.delete(f"/activities/{activity}/participants?email={email}")
            assert response.status_code == 200
        
        # Verify correct unregisters
        response = client.get("/activities")
        participants = response.json()[activity]["participants"]
        assert len(participants) == 3
        assert emails[2] in participants
