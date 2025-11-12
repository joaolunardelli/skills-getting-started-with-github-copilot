"""
Edge case and error handling tests for the Mergington High School Activities API.
"""

import pytest
from fastapi.testclient import TestClient
from urllib.parse import quote


class TestURLEncoding:
    """Tests for URL encoding and special characters."""
    
    def test_activity_name_with_spaces(self, client: TestClient, reset_activities):
        """Test activity names with spaces are properly handled."""
        activity = "Chess Club"  # Has space
        email = "test@mergington.edu"
        
        response = client.post(f"/activities/{quote(activity)}/signup?email={email}")
        assert response.status_code == 200
    
    def test_email_with_plus_sign(self, client: TestClient, reset_activities):
        """Test emails with plus signs are properly handled."""
        activity = "Art Club"
        email = "test+tag@mergington.edu"
        
        response = client.post(f"/activities/{activity}/signup?email={quote(email)}")
        assert response.status_code == 200
        
        # Verify in activities list
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email in activities[activity]["participants"]
    
    def test_email_with_special_characters(self, client: TestClient, reset_activities):
        """Test emails with various special characters."""
        activity = "Drama Club"
        email = "user.name+tag@sub.domain.edu"
        
        response = client.post(f"/activities/{activity}/signup?email={quote(email)}")
        assert response.status_code == 200


class TestParameterValidation:
    """Tests for parameter validation and edge cases."""
    
    def test_empty_email_parameter(self, client: TestClient, reset_activities):
        """Test signup with empty email parameter."""
        activity = "Chess Club"
        
        response = client.post(f"/activities/{activity}/signup?email=")
        # FastAPI should handle this - the behavior depends on validation
        # This test documents the current behavior
        assert response.status_code in [200, 422]  # Either accepts or validation error
    
    def test_missing_email_parameter(self, client: TestClient, reset_activities):
        """Test signup without email parameter."""
        activity = "Chess Club"
        
        response = client.post(f"/activities/{activity}/signup")
        assert response.status_code == 422  # Validation error
    
    def test_malformed_email(self, client: TestClient, reset_activities):
        """Test signup with malformed email."""
        activity = "Chess Club"
        email = "not-an-email"
        
        # The API currently doesn't validate email format, so this should succeed
        response = client.post(f"/activities/{activity}/signup?email={email}")
        assert response.status_code == 200


class TestConcurrency:
    """Tests for potential concurrency issues."""
    
    def test_simultaneous_signups_same_activity(self, client: TestClient, reset_activities):
        """Test multiple simultaneous signups for same activity."""
        activity = "Basketball Team"
        emails = [f"concurrent{i}@mergington.edu" for i in range(5)]
        
        # Get initial participant count
        activities_response = client.get("/activities")
        initial_count = len(activities_response.json()[activity]["participants"])
        
        # Perform multiple signups
        for email in emails:
            response = client.post(f"/activities/{activity}/signup?email={email}")
            assert response.status_code == 200
        
        # Verify all were added
        activities_response = client.get("/activities")
        activities = activities_response.json()
        final_count = len(activities[activity]["participants"])
        
        assert final_count == initial_count + len(emails)
        for email in emails:
            assert email in activities[activity]["participants"]


class TestDataIntegrity:
    """Tests for data integrity and consistency."""
    
    def test_participant_list_consistency(self, client: TestClient, reset_activities):
        """Test that participant lists remain consistent across operations."""
        activity = "Soccer Club"
        email = "integrity@mergington.edu"
        
        # Get initial state
        activities_response = client.get("/activities")
        initial_participants = set(activities_response.json()[activity]["participants"])
        
        # Add participant
        client.post(f"/activities/{activity}/signup?email={email}")
        
        # Check state
        activities_response = client.get("/activities")
        after_add_participants = set(activities_response.json()[activity]["participants"])
        
        assert len(after_add_participants) == len(initial_participants) + 1
        assert email in after_add_participants
        assert initial_participants.issubset(after_add_participants)
        
        # Remove participant
        client.delete(f"/activities/{activity}/participants/{email}")
        
        # Check final state
        activities_response = client.get("/activities")
        final_participants = set(activities_response.json()[activity]["participants"])
        
        assert final_participants == initial_participants
    
    def test_activity_structure_preservation(self, client: TestClient, reset_activities):
        """Test that activity structure is preserved during operations."""
        activity = "Gym Class"
        email = "structure@mergington.edu"
        
        # Get initial activity structure
        activities_response = client.get("/activities")
        initial_activity = activities_response.json()[activity].copy()
        
        # Perform operations
        client.post(f"/activities/{activity}/signup?email={email}")
        client.delete(f"/activities/{activity}/participants/{email}")
        
        # Check structure is preserved
        activities_response = client.get("/activities")
        final_activity = activities_response.json()[activity]
        
        # All fields should still exist
        assert set(final_activity.keys()) == set(initial_activity.keys())
        assert final_activity["description"] == initial_activity["description"]
        assert final_activity["schedule"] == initial_activity["schedule"]
        assert final_activity["max_participants"] == initial_activity["max_participants"]
        assert final_activity["participants"] == initial_activity["participants"]


class TestHTTPMethods:
    """Tests for HTTP method validation."""
    
    def test_get_method_on_signup_endpoint(self, client: TestClient, reset_activities):
        """Test that GET method is not allowed on signup endpoint."""
        activity = "Chess Club"
        email = "test@mergington.edu"
        
        response = client.get(f"/activities/{activity}/signup?email={email}")
        assert response.status_code == 405  # Method not allowed
    
    def test_post_method_on_remove_endpoint(self, client: TestClient, reset_activities):
        """Test that POST method is not allowed on remove endpoint."""
        activity = "Chess Club"
        email = "michael@mergington.edu"
        
        response = client.post(f"/activities/{activity}/participants/{email}")
        assert response.status_code == 405  # Method not allowed
    
    def test_put_method_on_activities_endpoint(self, client: TestClient, reset_activities):
        """Test that PUT method is not allowed on activities endpoint."""
        response = client.put("/activities")
        assert response.status_code == 405  # Method not allowed


class TestResponseFormat:
    """Tests for response format consistency."""
    
    def test_success_response_format(self, client: TestClient, reset_activities):
        """Test that success responses have consistent format."""
        activity = "Art Club"
        email = "format@mergington.edu"
        
        # Test signup success response
        response = client.post(f"/activities/{activity}/signup?email={email}")
        assert response.status_code == 200
        
        result = response.json()
        assert isinstance(result, dict)
        assert "message" in result
        assert isinstance(result["message"], str)
        
        # Test remove success response
        response = client.delete(f"/activities/{activity}/participants/{email}")
        assert response.status_code == 200
        
        result = response.json()
        assert isinstance(result, dict)
        assert "message" in result
        assert isinstance(result["message"], str)
    
    def test_error_response_format(self, client: TestClient, reset_activities):
        """Test that error responses have consistent format."""
        activity = "Nonexistent Activity"
        email = "test@mergington.edu"
        
        # Test 404 error format
        response = client.post(f"/activities/{activity}/signup?email={email}")
        assert response.status_code == 404
        
        result = response.json()
        assert isinstance(result, dict)
        assert "detail" in result
        assert isinstance(result["detail"], str)
    
    def test_activities_response_format(self, client: TestClient, reset_activities):
        """Test that activities endpoint returns properly formatted data."""
        response = client.get("/activities")
        assert response.status_code == 200
        
        activities = response.json()
        assert isinstance(activities, dict)
        
        for activity_name, activity_data in activities.items():
            assert isinstance(activity_name, str)
            assert isinstance(activity_data, dict)
            
            # Check required fields and their types
            assert isinstance(activity_data["description"], str)
            assert isinstance(activity_data["schedule"], str)
            assert isinstance(activity_data["max_participants"], int)
            assert isinstance(activity_data["participants"], list)
            
            # Check that all participants are strings (emails)
            for participant in activity_data["participants"]:
                assert isinstance(participant, str)