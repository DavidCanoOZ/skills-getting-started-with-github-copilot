"""
Tests for the Mergington High School Activities API
Using the AAA (Arrange-Act-Assert) testing pattern
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app

client = TestClient(app)


class TestGetActivities:
    """Tests for GET /activities endpoint"""
    
    def test_get_activities_returns_all_activities(self):
        """Should return all activities as a dictionary"""
        # Arrange
        expected_activities = ["Chess Club", "Programming Class", "Drama Club"]
        
        # Act
        response = client.get("/activities")
        activities = response.json()
        
        # Assert
        assert response.status_code == 200
        assert isinstance(activities, dict)
        for activity_name in expected_activities:
            assert activity_name in activities
    
    def test_activities_have_required_fields(self):
        """Each activity should have required fields"""
        # Arrange
        required_fields = {"description", "schedule", "max_participants", "participants"}
        
        # Act
        response = client.get("/activities")
        activities = response.json()
        
        # Assert
        assert response.status_code == 200
        for activity_name, activity_data in activities.items():
            for field in required_fields:
                assert field in activity_data, f"Missing {field} in {activity_name}"
            assert isinstance(activity_data["participants"], list)


class TestSignup:
    """Tests for POST /activities/{name}/signup endpoint"""
    
    def test_signup_new_participant_success(self):
        """Should successfully sign up a new participant"""
        # Arrange
        activity_name = "Chess Club"
        email = "newstudent@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )
        
        # Assert
        assert response.status_code == 200
        message = response.json()["message"]
        assert email in message
        assert activity_name in message
        
        # Verify participant was added to activity
        activities = client.get("/activities").json()
        assert email in activities[activity_name]["participants"]
    
    def test_signup_duplicate_fails(self):
        """Should reject duplicate signup with 400 status"""
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Already signed up
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )
        
        # Assert
        assert response.status_code == 400
        assert response.json()["detail"] == "Student already signed up"
    
    def test_signup_nonexistent_activity_fails(self):
        """Should return 404 for non-existent activity"""
        # Arrange
        activity_name = "Nonexistent Activity"
        email = "test@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )
        
        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"
    
    def test_signup_multiple_different_activities(self):
        """Should allow same student to signup for multiple activities"""
        # Arrange
        email = "multiactivity@mergington.edu"
        first_activity = "Chess Club"
        second_activity = "Art Studio"
        
        # Act - Sign up for first activity
        response1 = client.post(
            f"/activities/{first_activity}/signup?email={email}"
        )
        
        # Act - Sign up for second activity
        response2 = client.post(
            f"/activities/{second_activity}/signup?email={email}"
        )
        
        # Assert - Both signups successful
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # Assert - Both activities contain the student
        activities = client.get("/activities").json()
        assert email in activities[first_activity]["participants"]
        assert email in activities[second_activity]["participants"]


class TestUnsign:
    """Tests for POST /activities/{name}/unsign endpoint"""
    
    def test_unsign_existing_participant_success(self):
        """Should successfully remove a participant from activity"""
        # Arrange
        activity_name = "Programming Class"
        email = "unregister_test@mergington.edu"
        
        # Arrange - First ensure participant is signed up
        client.post(f"/activities/{activity_name}/signup?email={email}")
        
        # Act - Remove the participant
        response = client.post(
            f"/activities/{activity_name}/unsign?email={email}"
        )
        
        # Assert - Unsign was successful
        assert response.status_code == 200
        message = response.json()["message"]
        assert "Removed" in message
        assert email in message
        
        # Assert - Participant no longer in activity
        activities = client.get("/activities").json()
        assert email not in activities[activity_name]["participants"]
    
    def test_unsign_nonexistent_participant_fails(self):
        """Should return 404 when attempting to remove student not signed up"""
        # Arrange
        activity_name = "Chess Club"
        email = "notregistered@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/unsign?email={email}"
        )
        
        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Student not signed up"
    
    def test_unsign_nonexistent_activity_fails(self):
        """Should return 404 when activity doesn't exist"""
        # Arrange
        activity_name = "Fake Activity"
        email = "test@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/unsign?email={email}"
        )
        
        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"


class TestRootRedirect:
    """Tests for GET / endpoint"""
    
    def test_root_redirects_to_static(self):
        """Root path should redirect to static index page"""
        # Arrange
        expected_location = "/static/index.html"
        
        # Act
        response = client.get("/", follow_redirects=False)
        
        # Assert
        assert response.status_code == 307
        assert response.headers["location"] == expected_location


class TestIntegrationFlow:
    """Integration tests for complete user workflows"""
    
    def test_signup_and_unsign_workflow(self):
        """Should support signing up and then unregistering"""
        # Arrange
        activity_name = "Gym Class"
        email = "workflow_test@mergington.edu"
        
        # Act - Get initial participants count
        initial_activities = client.get("/activities").json()
        initial_count = len(initial_activities[activity_name]["participants"])
        
        # Act - Sign up
        signup_response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )
        
        # Assert - Signup successful
        assert signup_response.status_code == 200
        
        # Act - Verify participant count increased
        after_signup_activities = client.get("/activities").json()
        assert len(after_signup_activities[activity_name]["participants"]) == initial_count + 1
        assert email in after_signup_activities[activity_name]["participants"]
        
        # Act - Unregister
        unsign_response = client.post(
            f"/activities/{activity_name}/unsign?email={email}"
        )
        
        # Assert - Unsign successful
        assert unsign_response.status_code == 200
        
        # Assert - Participant count back to original
        final_activities = client.get("/activities").json()
        assert len(final_activities[activity_name]["participants"]) == initial_count
        assert email not in final_activities[activity_name]["participants"]
