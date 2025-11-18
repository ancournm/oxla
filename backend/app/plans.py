from typing import Dict, Any
from enum import Enum

class PlanFeatures:
    """Configuration for different subscription plans"""
    
    PLANS = {
        "free": {
            "storage_limit_gb": 5,
            "max_upload_size_mb": 50,
            "max_aliases": 5,
            "max_team_members": 1,
            "max_emails_per_month": 300,
            "max_emails_per_minute": 5,
            "features": [
                "basic_email_features",
                "5gb_storage",
                "basic_collaboration",
                "community_support"
            ],
            "api_rate_limit": 100,  # requests per minute
            "max_projects": 3,
            "max_file_versions": 5
        },
        "pro": {
            "storage_limit_gb": 50,
            "max_upload_size_mb": 2048,  # 2GB
            "max_aliases": "unlimited",
            "max_team_members": 10,
            "max_emails_per_month": 500,
            "max_emails_per_minute": 20,
            "features": [
                "advanced_email_features",
                "50gb_storage",
                "advanced_collaboration",
                "priority_support",
                "custom_domains",
                "advanced_analytics",
                "api_access",
                "webhooks"
            ],
            "api_rate_limit": 1000,  # requests per minute
            "max_projects": "unlimited",
            "max_file_versions": 50
        },
        "enterprise": {
            "storage_limit_gb": "unlimited",
            "max_upload_size_mb": "unlimited",
            "max_aliases": "unlimited",
            "max_team_members": "unlimited",
            "max_emails_per_month": "unlimited",
            "max_emails_per_minute": 100,
            "features": [
                "all_pro_features",
                "unlimited_storage",
                "enterprise_collaboration",
                "24/7_phone_support",
                "custom_integrations",
                "advanced_security",
                "compliance_certifications",
                "dedicated_account_manager",
                "custom_policies",
                "audit_logs",
                "sso_integration"
            ],
            "api_rate_limit": "unlimited",
            "max_projects": "unlimited",
            "max_file_versions": "unlimited"
        }
    }
    
    @classmethod
    def get_plan_features(cls, plan: str) -> Dict[str, Any]:
        """Get features for a specific plan"""
        return cls.PLANS.get(plan, cls.PLANS["free"])
    
    @classmethod
    def check_feature_access(cls, plan: str, feature: str) -> bool:
        """Check if a plan has access to a specific feature"""
        plan_features = cls.get_plan_features(plan)
        return feature in plan_features["features"]
    
    @classmethod
    def check_storage_limit(cls, plan: str, current_usage_gb: float) -> bool:
        """Check if user is within storage limit"""
        plan_features = cls.get_plan_features(plan)
        storage_limit = plan_features["storage_limit_gb"]
        
        if storage_limit == "unlimited":
            return True
        
        return current_usage_gb <= storage_limit
    
    @classmethod
    def check_upload_size(cls, plan: str, file_size_mb: float) -> bool:
        """Check if file size is within upload limit"""
        plan_features = cls.get_plan_features(plan)
        upload_limit = plan_features["max_upload_size_mb"]
        
        if upload_limit == "unlimited":
            return True
        
        return file_size_mb <= upload_limit
    
    @classmethod
    def check_team_member_limit(cls, plan: str, current_members: int) -> bool:
        """Check if user is within team member limit"""
        plan_features = cls.get_plan_features(plan)
        member_limit = plan_features["max_team_members"]
        
        if member_limit == "unlimited":
            return True
        
        return current_members <= member_limit
    
    @classmethod
    def get_plan_limits(cls, plan: str) -> Dict[str, Any]:
        """Get all limits for a specific plan"""
        plan_features = cls.get_plan_features(plan)
        return {
            "storage_limit_gb": plan_features["storage_limit_gb"],
            "max_upload_size_mb": plan_features["max_upload_size_mb"],
            "max_aliases": plan_features["max_aliases"],
            "max_team_members": plan_features["max_team_members"],
            "api_rate_limit": plan_features["api_rate_limit"],
            "max_projects": plan_features["max_projects"],
            "max_file_versions": plan_features["max_file_versions"],
            "max_emails_per_month": plan_features["max_emails_per_month"],
            "max_emails_per_minute": plan_features["max_emails_per_minute"]
        }
    
    @classmethod
    def check_email_monthly_limit(cls, plan: str, current_usage: int) -> bool:
        """Check if user is within monthly email limit"""
        plan_features = cls.get_plan_features(plan)
        max_emails = plan_features["max_emails_per_month"]
        
        if max_emails == "unlimited":
            return True
        
        return current_usage < max_emails
    
    @classmethod
    def check_email_rate_limit(cls, plan: str) -> int:
        """Get email rate limit per minute for a plan"""
        plan_features = cls.get_plan_features(plan)
        return plan_features["max_emails_per_minute"]