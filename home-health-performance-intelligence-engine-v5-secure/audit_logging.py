import logging

logger = logging.getLogger("audit")
logger.setLevel(logging.INFO)

handler = logging.FileHandler("audit.log")
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


def log_event(user: str, action: str, detail: str = ""):
    logger.info(f"User: {user} | Action: {action} | Detail: {detail}")

# Example usage:
# log_event("admin", "login", "Successful login")
# log_event("admin", "report_generation", "Generated report for agency ABC")
