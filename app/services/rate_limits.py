FREE_PLAN_LIMIT = 1000
STARTER_PLAN_LIMIT = 10000
PRO_PLAN_LIMIT = 100000

def get_plan_limit(plan_name: str) -> int:
    if plan_name == "pro":
        return PRO_PLAN_LIMIT
    if plan_name == "starter":
        return STARTER_PLAN_LIMIT
    return FREE_PLAN_LIMIT
