import pytest
from app.plans import PlanFeatures

def test_free_plan_features():
    """Test free plan features"""
    features = PlanFeatures.get_plan_features("free")
    
    assert features["storage_limit_gb"] == 5
    assert features["max_upload_size_mb"] == 50
    assert features["max_aliases"] == 5
    assert features["max_team_members"] == 1
    assert features["api_rate_limit"] == 100
    assert features["max_projects"] == 3
    assert features["max_file_versions"] == 5
    
    # Check some features
    assert "basic_email_features" in features["features"]
    assert "5gb_storage" in features["features"]
    assert "custom_domains" not in features["features"]

def test_pro_plan_features():
    """Test pro plan features"""
    features = PlanFeatures.get_plan_features("pro")
    
    assert features["storage_limit_gb"] == 50
    assert features["max_upload_size_mb"] == 2048
    assert features["max_aliases"] == "unlimited"
    assert features["max_team_members"] == 10
    assert features["api_rate_limit"] == 1000
    assert features["max_projects"] == "unlimited"
    
    # Check some features
    assert "advanced_email_features" in features["features"]
    assert "custom_domains" in features["features"]
    assert "priority_support" in features["features"]

def test_enterprise_plan_features():
    """Test enterprise plan features"""
    features = PlanFeatures.get_plan_features("enterprise")
    
    assert features["storage_limit_gb"] == "unlimited"
    assert features["max_upload_size_mb"] == "unlimited"
    assert features["max_aliases"] == "unlimited"
    assert features["max_team_members"] == "unlimited"
    assert features["api_rate_limit"] == "unlimited"
    
    # Check some features
    assert "all_pro_features" in features["features"]
    assert "24/7_phone_support" in features["features"]
    assert "custom_policies" in features["features"]

def test_feature_access():
    """Test feature access checking"""
    # Free plan features
    assert PlanFeatures.check_feature_access("free", "basic_email_features") is True
    assert PlanFeatures.check_feature_access("free", "custom_domains") is False
    
    # Pro plan features
    assert PlanFeatures.check_feature_access("pro", "basic_email_features") is True
    assert PlanFeatures.check_feature_access("pro", "custom_domains") is True
    assert PlanFeatures.check_feature_access("pro", "24/7_phone_support") is False
    
    # Enterprise plan features
    assert PlanFeatures.check_feature_access("enterprise", "basic_email_features") is True
    assert PlanFeatures.check_feature_access("enterprise", "custom_domains") is True
    assert PlanFeatures.check_feature_access("enterprise", "24/7_phone_support") is True

def test_storage_limits():
    """Test storage limit checking"""
    # Free plan
    assert PlanFeatures.check_storage_limit("free", 4) is True
    assert PlanFeatures.check_storage_limit("free", 5) is True
    assert PlanFeatures.check_storage_limit("free", 6) is False
    
    # Pro plan
    assert PlanFeatures.check_storage_limit("pro", 49) is True
    assert PlanFeatures.check_storage_limit("pro", 50) is True
    assert PlanFeatures.check_storage_limit("pro", 51) is False
    
    # Enterprise plan
    assert PlanFeatures.check_storage_limit("enterprise", 1000) is True
    assert PlanFeatures.check_storage_limit("enterprise", 1000000) is True

def test_upload_size_limits():
    """Test upload size limit checking"""
    # Free plan
    assert PlanFeatures.check_upload_size("free", 49) is True
    assert PlanFeatures.check_upload_size("free", 50) is True
    assert PlanFeatures.check_upload_size("free", 51) is False
    
    # Pro plan
    assert PlanFeatures.check_upload_size("pro", 2047) is True
    assert PlanFeatures.check_upload_size("pro", 2048) is True
    assert PlanFeatures.check_upload_size("pro", 2049) is False
    
    # Enterprise plan
    assert PlanFeatures.check_upload_size("enterprise", 10000) is True
    assert PlanFeatures.check_upload_size("enterprise", 1000000) is True

def test_team_member_limits():
    """Test team member limit checking"""
    # Free plan
    assert PlanFeatures.check_team_member_limit("free", 0) is True
    assert PlanFeatures.check_team_member_limit("free", 1) is True
    assert PlanFeatures.check_team_member_limit("free", 2) is False
    
    # Pro plan
    assert PlanFeatures.check_team_member_limit("pro", 9) is True
    assert PlanFeatures.check_team_member_limit("pro", 10) is True
    assert PlanFeatures.check_team_member_limit("pro", 11) is False
    
    # Enterprise plan
    assert PlanFeatures.check_team_member_limit("enterprise", 100) is True
    assert PlanFeatures.check_team_member_limit("enterprise", 10000) is True

def test_plan_limits():
    """Test getting plan limits"""
    free_limits = PlanFeatures.get_plan_limits("free")
    assert free_limits["storage_limit_gb"] == 5
    assert free_limits["max_upload_size_mb"] == 50
    
    pro_limits = PlanFeatures.get_plan_limits("pro")
    assert pro_limits["storage_limit_gb"] == 50
    assert pro_limits["max_upload_size_mb"] == 2048
    
    enterprise_limits = PlanFeatures.get_plan_limits("enterprise")
    assert enterprise_limits["storage_limit_gb"] == "unlimited"
    assert enterprise_limits["max_upload_size_mb"] == "unlimited"

def test_invalid_plan():
    """Test handling of invalid plan names"""
    features = PlanFeatures.get_plan_features("invalid_plan")
    # Should default to free plan features
    assert features == PlanFeatures.get_plan_features("free")
    
    # Feature access should work the same way
    assert PlanFeatures.check_feature_access("invalid_plan", "basic_email_features") is True
    assert PlanFeatures.check_feature_access("invalid_plan", "custom_domains") is False