# residential_ai_engine.py
# AI Plan Checker for Residential Buildings (Based on Model Building By-laws, 1977)
# Developed for the City Council Digital Submission System

import json
import math

# --- 1. THE RULES DATABASE ---
RULES_DB = [
    # SITE AND SETBACKS (Chapter 5)
    {"id": "R-001", "name": "Front Setback", "category": "Setback", "unit": "meters", "threshold": 3.0, "comparison": ">=", "message": "Front setback must be at least 3.0 meters."},
    {"id": "R-002", "name": "Side Setback", "category": "Setback", "unit": "meters", "threshold": 1.5, "comparison": ">=", "message": "Side setback must be at least 1.5 meters."},
    {"id": "R-003", "name": "Rear Setback", "category": "Setback", "unit": "meters", "threshold": 2.5, "comparison": ">=", "message": "Rear setback must be at least 2.5 meters."},
    
    # BUILDING HEIGHT (Chapters 5 & 10)
    {"id": "R-004", "name": "Max Building Height", "category": "Height", "unit": "meters", "threshold": 12.0, "comparison": "<=", "message": "Total building height must not exceed 12.0 meters."},
    {"id": "R-005", "name": "Min Storey Height (Residential)", "category": "Height", "unit": "meters", "threshold": 2.4, "comparison": ">=", "message": "Storey height must be at least 2.4 meters."},
    
    # PLOT COVERAGE (Chapter 5)
    {"id": "R-008", "name": "Max Plot Coverage", "category": "Coverage", "unit": "%", "threshold": 60.0, "comparison": "<=", "message": "Total ground floor coverage must not exceed 60% of the plot area."},
    
    # FOUNDATIONS (Chapter 4)
    {"id": "R-010", "name": "Min Foundation Depth", "category": "Foundations", "unit": "mm", "threshold": 450, "comparison": ">=", "message": "Foundation depth must be at least 450mm below ground level."},
    {"id": "R-011", "name": "Min Foundation Width (Sleeper Walls)", "category": "Foundations", "unit": "mm", "threshold": 300, "comparison": ">=", "message": "Width of foundations under sleeper walls must be at least 300mm."},
    {"id": "R-012", "name": "Min Foundation Thickness (Walls <200mm)", "category": "Foundations", "unit": "mm", "threshold": 150, "comparison": ">=", "message": "Vertical thickness of foundations for walls <200mm must be at least 150mm."},
    {"id": "R-013", "name": "Min Foundation Thickness (Walls >=200mm)", "category": "Foundations", "unit": "mm", "threshold": 200, "comparison": ">=", "message": "Vertical thickness of foundations for walls >=200mm must be at least 200mm."},
    
    # WALLS (Chapter 5)
    {"id": "R-014", "name": "Min External Bearing Wall Thickness", "category": "Walls", "unit": "mm", "threshold": 215, "comparison": ">=", "message": "External bearing walls must be at least 215mm thick (Brick) or 200mm (Block)."},
    {"id": "R-015", "name": "Min Internal Bearing Wall Thickness", "category": "Walls", "unit": "mm", "threshold": 100, "comparison": ">=", "message": "Internal bearing walls must be at least 100mm thick (Brick) or 150mm (Block)."},
    
    # LIGHTING & VENTILATION (Chapters 8 & 10)
    {"id": "R-017", "name": "Min Daylight Opening Area (Kitchen)", "category": "Lighting", "unit": "%", "threshold": 12.0, "comparison": ">=", "message": "Kitchens must have daylight openings equal to at least 12% of the floor area."},
    {"id": "R-019", "name": "Min Daylight Opening Area (Other Rooms)", "category": "Lighting", "unit": "%", "threshold": 10.0, "comparison": ">=", "message": "Habitable rooms must have daylight openings equal to at least 10% of the floor area."},
    {"id": "R-020", "name": "Min Ventilation Opening Area", "category": "Ventilation", "unit": "%", "threshold": 5.0, "comparison": ">=", "message": "Habitable rooms must have ventilation openings equal to at least 5% of the floor area."}
]

# --- 2. THE AI CHECKER ENGINE ---
def check_plan(plan_data):
    """
    plan_data: A dictionary containing the measurements from the CAD file.
    """
    
    results = {
        "status": "PENDING",
        "violations": [],
        "passed_count": 0,
        "failed_count": 0,
        "total_rules_checked": 0
    }
    
    # Helper function to check a single rule
    def check_rule(rule_index, value, rule_name_override=None):
        if value is None:
            return
        results["total_rules_checked"] += 1
        rule = RULES_DB[rule_index]
        if rule["comparison"] == ">=":
            passed = value >= rule["threshold"]
        elif rule["comparison"] == "<=":
            passed = value <= rule["threshold"]
        else:
            passed = False
        
        if passed:
            results["passed_count"] += 1
        else:
            results["failed_count"] += 1
            results["violations"].append({
                "rule_id": rule["id"],
                "rule_name": rule["name"] if not rule_name_override else rule_name_override,
                "message": rule["message"],
                "value_provided": f"{value} {rule['unit']}",
                "threshold": f"{rule['threshold']} {rule['unit']}"
            })
    
    # --- RUN ALL CHECKS ---
    
    # Setbacks
    check_rule(0, plan_data.get("front_setback"))
    check_rule(1, plan_data.get("side_setback"))
    check_rule(2, plan_data.get("rear_setback"))
    
    # Heights
    check_rule(3, plan_data.get("total_height"))
    check_rule(4, plan_data.get("storey_height"))
    
    # Plot Coverage
    footprint = plan_data.get("building_footprint")
    plot_area = plan_data.get("plot_area")
    if footprint is not None and plot_area is not None and plot_area > 0:
        coverage_percent = (footprint / plot_area) * 100
        check_rule(5, coverage_percent)
    
    # Foundations
    check_rule(6, plan_data.get("foundation_depth"))
    check_rule(7, plan_data.get("foundation_width"))  # R-011
    check_rule(8, plan_data.get("foundation_thickness_small"))  # R-012
    check_rule(9, plan_data.get("foundation_thickness_large"))  # R-013
    
    # Walls
    check_rule(10, plan_data.get("external_wall_thickness"))  # R-014
    check_rule(11, plan_data.get("internal_wall_thickness"))   # R-015
    
    # Lighting & Ventilation (Only if data exists)
    if plan_data.get("has_kitchen", False):
        check_rule(12, plan_data.get("kitchen_window_area"))  # R-017
    
    check_rule(13, plan_data.get("other_window_area"))  # R-019
    check_rule(14, plan_data.get("ventilation_area"))   # R-020
    
    # --- Final Status ---
    if results["failed_count"] == 0 and results["total_rules_checked"] > 0:
        results["status"] = "PASSED"
    elif results["total_rules_checked"] == 0:
        results["status"] = "INSUFFICIENT_DATA"
    else:
        results["status"] = "FAILED"
    
    return results

# --- 3. SAMPLE RUN (Testing the AI) ---
if __name__ == "__main__":
    print("=" * 60)
    print("AI PLAN CHECKER FOR RESIDENTIAL BUILDINGS")
    print("=" * 60)

    # Sample Plan 1: A fully compliant residential house
    compliant_plan = {
        "building_type": "residential",
        "plot_area": 500,
        "building_footprint": 250,
        "front_setback": 4.0,
        "side_setback": 2.0,
        "rear_setback": 3.0,
        "total_height": 10.5,
        "storey_height": 2.6,
        "foundation_depth": 600,
        "foundation_width": 350,
        "foundation_thickness_small": 180,
        "foundation_thickness_large": 220,
        "external_wall_thickness": 215,
        "internal_wall_thickness": 100,
        "has_kitchen": True,
        "kitchen_window_area": 12.5,
        "other_window_area": 11.0,
        "ventilation_area": 6.0,
        "num_storeys": 3,
        "floor_area": 100
    }

    # Sample Plan 2: A non-compliant plan
    non_compliant_plan = {
        "building_type": "residential",
        "plot_area": 300,
        "building_footprint": 200,
        "front_setback": 2.0,
        "side_setback": 1.0,
        "rear_setback": 2.0,
        "total_height": 13.0,      # FAILS (> 12.0m)
        "storey_height": 2.2,       # FAILS (< 2.4m)
        "foundation_depth": 400,    # FAILS (< 450mm)
        "foundation_width": 250,    # FAILS (< 300mm)
        "foundation_thickness_small": 120,  # FAILS (< 150mm)
        "foundation_thickness_large": 180,  # FAILS (< 200mm)
        "external_wall_thickness": 190,     # FAILS (< 215mm)
        "internal_wall_thickness": 80,      # FAILS (< 100mm)
        "has_kitchen": True,
        "kitchen_window_area": 11.0,        # FAILS (< 12%)
        "other_window_area": 8.0,           # FAILS (< 10%)
        "ventilation_area": 4.0,            # FAILS (< 5%)
        "num_storeys": 3,
        "floor_area": 100
    }

    print("\n--- TEST 1: COMPLIANT PLAN ---")
    result_1 = check_plan(compliant_plan)
    print(json.dumps(result_1, indent=2))

    print("\n--- TEST 2: NON-COMPLIANT PLAN ---")
    result_2 = check_plan(non_compliant_plan)
    print(json.dumps(result_2, indent=2))
