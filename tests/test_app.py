"""
Tests for the Mergington High School Activities API
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src directory to path to import app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app, activities


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture
def reset_activities():
    """Reset activities to initial state before each test"""
    # Store original state
    original_activities = {
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
        "No Class": {
            "description": "no activities",
            "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
            "max_participants": 30,
            "participants": ["john@mergington.edu", "olivia@mergington.edu"]
        }
    }
    
    # Reset activities before test
    activities.clear()
    activities.update(original_activities)
    
    yield
    
    # Reset activities after test
    activities.clear()
    activities.update(original_activities)


class TestGetActivities:
    """Tests for the GET /activities endpoint"""
    
    def test_get_activities_returns_all_activities(self, client, reset_activities):
        """Test that GET /activities returns all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data
        assert "No Class" in data
        assert len(data) == 4
    
    def test_get_activities_contains_correct_fields(self, client, reset_activities):
        """Test that activities contain all required fields"""
        response = client.get("/activities")
        data = response.json()
        
        activity = data["Chess Club"]
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity
    
    def test_get_activities_shows_participants(self, client, reset_activities):
        """Test that activities show registered participants"""
        response = client.get("/activities")
        data = response.json()
        
        chess_club = data["Chess Club"]
        assert len(chess_club["participants"]) == 2
        assert "michael@mergington.edu" in chess_club["participants"]
        assert "daniel@mergington.edu" in chess_club["participants"]


class TestSignupForActivity:
    """Tests for the POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_for_existing_activity(self, client, reset_activities):
        """Test signing up for an existing activity"""
        email = "student@mergington.edu"
        activity_name = "Chess Club"
        
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        assert activity_name in data["message"]
    
    def test_signup_adds_participant_to_activity(self, client, reset_activities):
        """Test that signup actually adds the participant"""
        email = "newstudent@mergington.edu"
        activity_name = "Programming Class"
        
        # Verify student not already signed up
        response = client.get("/activities")
        initial_count = len(response.json()[activity_name]["participants"])
        
        # Sign up
        client.post(f"/activities/{activity_name}/signup?email={email}")
        
        # Verify student was added
        response = client.get("/activities")
        final_count = len(response.json()[activity_name]["participants"])
        assert final_count == initial_count + 1
        assert email in response.json()[activity_name]["participants"]
    
    def test_signup_for_nonexistent_activity(self, client, reset_activities):
        """Test signing up for a non-existent activity"""
        email = "student@mergington.edu"
        activity_name = "Nonexistent Activity"
        
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]
    
    def test_signup_multiple_times(self, client, reset_activities):
        """Test that a student can sign up for multiple activities"""
        email = "student@mergington.edu"
        
        # Sign up for first activity
        response1 = client.post("/activities/Chess Club/signup?email=" + email)
        assert response1.status_code == 200
        
        # Sign up for second activity
        response2 = client.post("/activities/Programming Class/signup?email=" + email)
        assert response2.status_code == 200
        
        # Verify student is in both activities
        response = client.get("/activities")
        assert email in response.json()["Chess Club"]["participants"]
        assert email in response.json()["Programming Class"]["participants"]


class TestUnregisterFromActivity:
    """Tests for the POST /activities/{activity_name}/unregister endpoint"""
    
    def test_unregister_existing_participant(self, client, reset_activities):
        """Test unregistering an existing participant"""
        email = "michael@mergington.edu"
        activity_name = "Chess Club"
        
        response = client.post(
            f"/activities/{activity_name}/unregister?email={email}"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        assert activity_name in data["message"]
    
    def test_unregister_removes_participant(self, client, reset_activities):
        """Test that unregister actually removes the participant"""
        email = "daniel@mergington.edu"
        activity_name = "Chess Club"
        
        # Verify student is registered
        response = client.get("/activities")
        assert email in response.json()[activity_name]["participants"]
        
        # Unregister
        client.post(f"/activities/{activity_name}/unregister?email={email}")
        
        # Verify student was removed
        response = client.get("/activities")
        assert email not in response.json()[activity_name]["participants"]
    
    def test_unregister_nonexistent_activity(self, client, reset_activities):
        """Test unregistering from a non-existent activity"""
        email = "student@mergington.edu"
        activity_name = "Nonexistent Activity"
        
        response = client.post(
            f"/activities/{activity_name}/unregister?email={email}"
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]
    
    def test_unregister_non_participant(self, client, reset_activities):
        """Test unregistering someone who's not registered"""
        email = "notregistered@mergington.edu"
        activity_name = "Chess Club"
        
        response = client.post(
            f"/activities/{activity_name}/unregister?email={email}"
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "not signed up" in data["detail"]
    
    def test_unregister_and_signup_again(self, client, reset_activities):
        """Test that a student can unregister and sign up again"""
        email = "testuser@mergington.edu"
        activity_name = "Gym Class"
        
        # Sign up
        client.post(f"/activities/{activity_name}/signup?email={email}")
        response = client.get("/activities")
        assert email in response.json()[activity_name]["participants"]
        
        # Unregister
        client.post(f"/activities/{activity_name}/unregister?email={email}")
        response = client.get("/activities")
        assert email not in response.json()[activity_name]["participants"]
        
        # Sign up again
        client.post(f"/activities/{activity_name}/signup?email={email}")
        response = client.get("/activities")
        assert email in response.json()[activity_name]["participants"]


class TestRootEndpoint:
    """Tests for the GET / endpoint"""
    
    def test_root_redirects_to_static(self, client):
        """Test that root redirects to /static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"
