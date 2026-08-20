# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""
Common utilities for CDK stacks
"""
from typing import List, Dict, Any


def create_waf_managed_rules(
    scope: str, start_priority: int, rules: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Create AWS managed WAF rules

    Args:
        scope: "REGIONAL" or "CLOUDFRONT"
        start_priority: Starting priority number
        rules: List of rule configurations

    Returns:
        List of WAF rule configurations
    """
    waf_rules = []
    priority = start_priority

    for rule_config in rules:
        name = rule_config["name"]
        override_action = rule_config.get("overrideAction", {"none": {}})
        rule_action_overrides = rule_config.get("ruleActionOverrides", [])

        waf_rule = {
            "name": f"{name}Rule",
            "priority": priority,
            "statement": {
                "managedRuleGroupStatement": {
                    "vendorName": "AWS",
                    "name": name,
                }
            },
            "overrideAction": override_action,
            "visibilityConfig": {
                "sampledRequestsEnabled": True,
                "cloudWatchMetricsEnabled": True,
                "metricName": f"{name}Metric",
            },
        }

        if rule_action_overrides:
            waf_rule["statement"]["managedRuleGroupStatement"][
                "ruleActionOverrides"
            ] = rule_action_overrides

        waf_rules.append(waf_rule)
        priority += 1

    return waf_rules
