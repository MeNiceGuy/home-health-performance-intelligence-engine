from setuptools import setup, find_packages

setup(
    name="home-health-performance-intelligence-engine",
    version="2.0.0",
    description="HHVBP decision intelligence engine for home health agencies",
    packages=find_packages(include=["services", "services.*"]),
    py_modules=[
        "server",
        "home_health_decision_engine_cli_v2",
        "pdf_generator",
        "audit_logging",
        "auth",
        "secure_auth",
        "user_management",
        "home_health_decision_engine",
        "home_health_decision_engine_pdf",
        "natural_language_parser",
    ],
    install_requires=[
        "fastapi>=0.115.0",
        "uvicorn>=0.30.0",
        "jinja2>=3.1.0",
        "requests>=2.31.0",
        "reportlab>=4.0.0",
        "matplotlib>=3.8.0",
        "openai>=1.35.0",
        "jsonschema>=4.21.0",
        "python-multipart>=0.0.9",
    ],
)
