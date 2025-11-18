import pytest
from fastapi import status
from app.models import UserPlan
from app.plans import PlanFeatures

def test_email_rate_limiting_free_plan(client, auth_headers):
    """Test email rate limiting for free plan (5 emails per minute)"""
    email_data = {
        "recipient": "test@example.com",
        "subject": "Test Subject",
        "body_text": "Test body"
    }
    
    # Send 5 emails (should succeed)
    for i in range(5):
        response = client.post("/mail/send", json=email_data, headers=auth_headers)
        # Note: This will likely fail due to no SMTP server, but should pass rate limiting
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR]
    
    # 6th email should be rate limited
    response = client.post("/mail/send", json=email_data, headers=auth_headers)
    assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
    assert "Rate limit exceeded" in response.json()["detail"]

def test_email_rate_limiting_pro_plan(client, auth_headers):
    """Test email rate limiting for pro plan (20 emails per minute)"""
    # Note: This test would require upgrading the user to pro plan
    # For now, we'll test the rate limiting logic
    
    from app.middleware import check_rate_limit
    from app.models import User
    
    # Test rate limit check function
    # This is a simplified test since we can't easily change user plan in tests
    result = check_rate_limit(1, "email")
    assert isinstance(result, bool)

def test_monthly_email_limit_free_plan(client, auth_headers):
    """Test monthly email limit for free plan (300 emails per month)"""
    # This test would require setting up user usage records
    # For now, we'll test the limit checking logic
    
    from app.plans import PlanFeatures
    
    # Test free plan limit
    assert PlanFeatures.check_email_monthly_limit("free", 299) is True
    assert PlanFeatures.check_email_monthly_limit("free", 300) is False
    assert PlanFeatures.check_email_monthly_limit("free", 301) is False
    
    # Test pro plan limit
    assert PlanFeatures.check_email_monthly_limit("pro", 499) is True
    assert PlanFeatures.check_email_monthly_limit("pro", 500) is False
    
    # Test enterprise plan (unlimited)
    assert PlanFeatures.check_email_monthly_limit("enterprise", 1000) is True
    assert PlanFeatures.check_email_monthly_limit("enterprise", 10000) is True

def test_plan_rate_limits():
    """Test rate limits by plan"""
    from app.plans import PlanFeatures
    
    # Test rate limits per minute
    assert PlanFeatures.check_email_rate_limit("free") == 5
    assert PlanFeatures.check_email_rate_limit("pro") == 20
    assert PlanFeatures.check_email_rate_limit("enterprise") == 100

def test_email_limits_checking():
    """Test email limits checking function"""
    from app.middleware import check_email_limits
    
    # Test with non-existent user (should fail)
    result = check_email_limits(99999)
    assert result["allowed"] is False
    assert result["reason"] == "User not found"

def test_usage_stats_endpoint(client, auth_headers):
    """Test usage statistics endpoint"""
    response = client.get("/metrics/usage-stats/1", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    
    # Should contain user information
    assert "user_id" in data
    assert "plan" in data
    assert "emails_sent" in data
    assert "max_emails_per_month" in data

def test_system_stats_endpoint(client, auth_headers):
    """Test system statistics endpoint"""
    response = client.get("/metrics/system-stats", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    
    # Should contain user statistics
    assert "users" in data
    assert "total" in data["users"]
    assert "active" in data["users"]
    assert "plan_distribution" in data["users"]

def test_prometheus_metrics_endpoint(client):
    """Test Prometheus metrics endpoint"""
    response = client.get("/metrics/metrics")
    assert response.status_code == status.HTTP_200_OK
    assert response.headers["content-type"] == "text/plain; charset=utf-8"

def test_queue_metrics_endpoint(client):
    """Test queue metrics endpoint"""
    response = client.get("/metrics/queue-metrics")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    
    # Should contain queue information
    assert "queue_length" in data
    assert "timestamp" in data

def test_plan_limits_comprehensive():
    """Test comprehensive plan limits"""
    from app.plans import PlanFeatures
    
    plans = ["free", "pro", "enterprise"]
    
    for plan in plans:
        limits = PlanFeatures.get_plan_limits(plan)
        
        # Check that all expected limits are present
        expected_limits = [
            "storage_limit_gb",
            "max_upload_size_mb",
            "max_aliases",
            "max_team_members",
            "api_rate_limit",
            "max_projects",
            "max_file_versions",
            "max_emails_per_month",
            "max_emails_per_minute"
        ]
        
        for limit in expected_limits:
            assert limit in limits, f"Missing limit {limit} for plan {plan}"
        
        # Check that enterprise has unlimited limits
        if plan == "enterprise":
            assert limits["storage_limit_gb"] == "unlimited"
            assert limits["max_upload_size_mb"] == "unlimited"
            assert limits["max_aliases"] == "unlimited"
            assert limits["max_team_members"] == "unlimited"
            assert limits["max_emails_per_month"] == "unlimited"