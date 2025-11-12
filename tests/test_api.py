"""
Tests for the Mergington High School Activities API.
"""

import pytest
from fastapi.testclient import TestClient


class TestRootEndpoint:
    """Tests for the root endpoint."""
    
    def test_root_redirects_to_static_index(self, client: TestClient):
        """Test that root endpoint redirects to static index.html."""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestActivitiesEndpoint:
    """Tests for the activities endpoint."""
    
    def test_get_activities_success(self, client: TestClient, reset_activities):
        """Test successful retrieval of activities."""
        response = client.get("/activities")
        assert response.status_code == 200
        
        activities = response.json()
        assert isinstance(activities, dict)
        assert len(activities) == 9
        
        # Test specific activity structure
        chess_club = activities["Chess Club"]
        assert "description" in chess_club
        assert "schedule" in chess_club
        assert "max_participants" in chess_club
        assert "participants" in chess_club
        assert chess_club["max_participants"] == 12
        assert len(chess_club["participants"]) == 2
        assert "michael@mergington.edu" in chess_club["participants"]
    
    def test_activities_contain_required_fields(self, client: TestClient, reset_activities):
        """Test that all activities contain required fields."""
        response = client.get("/activities")
        activities = response.json()
        
        required_fields = ["description", "schedule", "max_participants", "participants"]
        
        for activity_name, activity_data in activities.items():
            for field in required_fields:
                assert field in activity_data, f"Missing {field} in {activity_name}"
            
            # Validate data types
            assert isinstance(activity_data["description"], str)
            assert isinstance(activity_data["schedule"], str)
            assert isinstance(activity_data["max_participants"], int)
            assert isinstance(activity_data["participants"], list)


class TestSignupEndpoint:
    """Tests for the signup endpoint."""
    
    def test_signup_success(self, client: TestClient, reset_activities):
        """Test successful signup for an activity."""
        email = "newstudent@mergington.edu"
        activity = "Chess Club"
        
        response = client.post(f"/activities/{activity}/signup?email={email}")
        assert response.status_code == 200
        
        result = response.json()
        assert "message" in result
        assert f"Signed up {email} for {activity}" in result["message"]
        
        # Verify the participant was added
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email in activities[activity]["participants"]
    
    def test_signup_duplicate_participant(self, client: TestClient, reset_activities):
        """Test signup with duplicate participant."""
        email = "michael@mergington.edu"  # Already in Chess Club
        activity = "Chess Club"
        
        response = client.post(f"/activities/{activity}/signup?email={email}")
        assert response.status_code == 400
        
        result = response.json()
        assert "detail" in result
        assert "already signed up" in result["detail"]
    
    def test_signup_nonexistent_activity(self, client: TestClient, reset_activities):
        """Test signup for non-existent activity."""
        email = "student@mergington.edu"
        activity = "Nonexistent Activity"
        
        response = client.post(f"/activities/{activity}/signup?email={email}")
        assert response.status_code == 404
        
        result = response.json()
        assert "detail" in result
        assert "Activity not found" in result["detail"]
    
    def test_signup_with_special_characters(self, client: TestClient, reset_activities):
        """Test signup with URL encoded special characters."""
        from urllib.parse import quote
        
        email = "test+user@mergington.edu"
        activity = "Art Club"
        
        response = client.post(f"/activities/{activity}/signup?email={quote(email)}")
        assert response.status_code == 200
        
        # Verify the participant was added
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email in activities[activity]["participants"]


class TestRemoveParticipantEndpoint:
    """Tests for the remove participant endpoint."""
    
    def test_remove_participant_success(self, client: TestClient, reset_activities):
        """Test successful removal of a participant."""
        email = "michael@mergington.edu"
        activity = "Chess Club"
        
        # Verify participant exists first
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email in activities[activity]["participants"]
        
        # Remove participant
        response = client.delete(f"/activities/{activity}/participants/{email}")
        assert response.status_code == 200
        
        result = response.json()
        assert "message" in result
        assert f"Removed {email} from {activity}" in result["message"]
        
        # Verify participant was removed
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email not in activities[activity]["participants"]
    
    def test_remove_nonexistent_participant(self, client: TestClient, reset_activities):
        """Test removal of non-existent participant."""
        email = "nonexistent@mergington.edu"
        activity = "Chess Club"
        
        response = client.delete(f"/activities/{activity}/participants/{email}")
        assert response.status_code == 404
        
        result = response.json()
        assert "detail" in result
        assert "Participant not found" in result["detail"]
    
    def test_remove_participant_from_nonexistent_activity(self, client: TestClient, reset_activities):
        """Test removal of participant from non-existent activity."""
        email = "student@mergington.edu"
        activity = "Nonexistent Activity"
        
        response = client.delete(f"/activities/{activity}/participants/{email}")
        assert response.status_code == 404
        
        result = response.json()
        assert "detail" in result
        assert "Activity not found" in result["detail"]
    
    def test_remove_participant_with_special_characters(self, client: TestClient, reset_activities):
        """Test removal of participant with special characters in email."""
        from urllib.parse import quote
        
        # First add a participant with special characters
        email = "test+user@mergington.edu"
        activity = "Drama Club"
        
        # Add the participant
        client.post(f"/activities/{activity}/signup?email={quote(email)}")
        
        # Remove the participant
        response = client.delete(f"/activities/{quote(activity)}/participants/{quote(email)}")
        assert response.status_code == 200
        
        # Verify removal
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email not in activities[activity]["participants"]


class TestIntegrationScenarios:
    """Integration tests for complex scenarios."""
    
    def test_signup_and_remove_workflow(self, client: TestClient, reset_activities):
        """Test complete workflow of signup and removal."""
        email = "workflow@mergington.edu"
        activity = "Programming Class"
        
        # Initial state check
        activities_response = client.get("/activities")
        activities = activities_response.json()
        initial_count = len(activities[activity]["participants"])
        
        # Sign up
        signup_response = client.post(f"/activities/{activity}/signup?email={email}")
        assert signup_response.status_code == 200
        
        # Verify signup
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert len(activities[activity]["participants"]) == initial_count + 1
        assert email in activities[activity]["participants"]
        
        # Remove participant
        remove_response = client.delete(f"/activities/{activity}/participants/{email}")
        assert remove_response.status_code == 200
        
        # Verify removal
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert len(activities[activity]["participants"]) == initial_count
        assert email not in activities[activity]["participants"]
    
    def test_multiple_signups_same_user(self, client: TestClient, reset_activities):
        """Test that one user can sign up for multiple activities."""
        email = "multi@mergington.edu"
        activities_list = ["Chess Club", "Art Club", "Drama Club"]
        
        # Sign up for multiple activities
        for activity in activities_list:
            response = client.post(f"/activities/{activity}/signup?email={email}")
            assert response.status_code == 200
        
        # Verify all signups
        activities_response = client.get("/activities")
        activities = activities_response.json()
        
        for activity in activities_list:
            assert email in activities[activity]["participants"]
    
    def test_activity_capacity_tracking(self, client: TestClient, reset_activities):
        """Test that participant count affects available spots correctly."""
        activity = "Science Olympiad"
        
        # Get initial state
        activities_response = client.get("/activities")
        activities = activities_response.json()
        max_participants = activities[activity]["max_participants"]
        current_participants = len(activities[activity]["participants"])
        
        # Calculate available spots
        available_spots = max_participants - current_participants
        
        # Add participants up to the limit
        for i in range(available_spots):
            email = f"student{i}@mergington.edu"
            response = client.post(f"/activities/{activity}/signup?email={email}")
            assert response.status_code == 200
        
        # Verify all spots are filled
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert len(activities[activity]["participants"]) == max_participants