# engine.py
# AI Plan Checker for Residential Buildings (Based on Model Building By-laws, 1977)

import json
import math

# --- 1. THE RULES DATABASE ---
RULES_DB = [
    {"id": "R-001", "name": "Front Setback", "category": "Setback", "unit": "meters", "threshold": 3.0, "comparison": ">=", "message": "Front setback must be at least 3.0 meters."},
    {"id": "R-002", "name": "Side Setback", "category": "Setback", "unit": "meters", "threshold": 1.5, "comparison": ">=", "message": "Side setback must be at least 1.5 meters."},
    {"id": "R-003", "name": "Rear Setback", "category": "Setback", "unit": "meters", "threshold": 2.5, "comparison": ">=", "message": "Rear setback must be at least 2.5 meters."},
    {"id": "R-004", "name": "Max Building Height", "category": "Height", "unit": "meters", "threshold": 12.0, "comparison": "<=", "message": "Total building height must not exceed 12.0 meters."},
    {"id": "R-005", "name": "Min Storey Height", "category": "Height", "unit": "meters", "threshold": 2.4, "comparison": ">=", "message": "Storey height must be at least 2.4 meters."},
    {"id": "R-008", "name": "Max Plot Coverage", "category": "Coverage", "unit": "%", "threshold": 60.0, "comparison": "<=", "message": "Total ground floor coverage must not exceed 60% of the plot area."},
    {"id": "R-010", "name": "Min Foundation Depth", "category": "Foundations", "unit": "mm", "threshold": 450, "comparison": ">=", "message": "Foundation depth must be at least 450mm below ground level."},
    {"id": "R-014", "name": "Min External Wall Thickness", "category": "Walls", "unit": "mm", "threshold": 215, "comparison": ">=", "message": "External bearing walls must be at least 215mm thick."},
    {"id": "R-015", "name": "Min Internal Wall Thickness", "category": "Walls", "unit": "mm", "threshold": 100, "comparison": ">=", "message": "Internal bearing walls must be at least 100mm thick."},
    {"id": "R-017", "name": "Min Kitchen Daylight Opening", "category": "Lighting", "unit": "%", "threshold": 12.0, "comparison": ">=", "message": "Kitchens must have daylight openings equal to at least 12% of the floor area."},
    {"id": "R-019", "name": "Min Daylight Opening (Other Rooms)", "category": "Lighting", "unit": "%", "threshold": 10.0, "comparison": ">=", "message": "Habitable rooms must have daylight openings equal to at least 10% of the floor area."},
    {"id": "R-020", "name": "Min Ventilation Opening Area", "category": "Ventilation", "unit": "%", "threshold": 5.0, "comparison": ">=", "message": "Habitable rooms must have ventilation openings equal to at least 5% of the floor area."}
]

def check_plan(plan_data):
    """Check plan data against all rules."""
    results = {
        "status": "PENDING",
        "violations": [],
        "passed_count": 0,
        "failed_count": 0,
        "total_rules_checked": 0
    }
    
    # Helper to check a rule
    def check_rule(rule_index, value):
        if value is None:
            return
        results["total_rules_checked"] += 1
        rule = RULES_DB[rule_index]
        passed = False
        if rule["comparison"] == ">=":
            passed = value >= rule["threshold"]
        elif rule["comparison"] == "<=":
            passed = value <= rule["threshold"]
        
        if passed:
            results["passed_count"] += 1
        else:
            results["failed_count"] += 1
            results["violations"].append({
                "rule_id": rule["id"],
                "rule_name": rule["name"],
                "message": rule["message"],
                "value_provided": f"{value} {rule['unit']}",
                "threshold": f"{rule['threshold']} {rule['unit']}"
            })
    
    # Run all checks
    check_rule(0, plan_data.get("front_setback"))
    check_rule(1, plan_data.get("side_setback"))
    check_rule(2, plan_data.get("rear_setback"))
    check_rule(3, plan_data.get("total_height"))
    check_rule(4, plan_data.get("storey_height"))
    
    # Plot Coverage
    footprint = plan_data.get("building_footprint")
    plot_area = plan_data.get("plot_area")
    if footprint and plot_area and plot_area > 0:
        coverage = (footprint / plot_area) * 100
        check_rule(5, coverage)
    
    check_rule(6, plan_data.get("foundation_depth"))
    check_rule(7, plan_data.get("external_wall_thickness"))
    check_rule(8, plan_data.get("internal_wall_thickness"))
    
    if plan_data.get("has_kitchen", False):
        check_rule(9, plan_data.get("kitchen_window_area"))
    
    check_rule(10, plan_data.get("other_window_area"))
    check_rule(11, plan_data.get("ventilation_area"))
    
    # Final status
    if results["failed_count"] == 0 and results["total_rules_checked"] > 0:
        results["status"] = "PASSED"
    elif results["total_rules_checked"] == 0:
        results["status"] = "INSUFFICIENT_DATA"
    else:
        results["status"] = "FAILED"
    
    return results
