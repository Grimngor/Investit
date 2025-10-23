import warnings

# Silence deprecation warning from python-jose using utcnow (third-party)
warnings.filterwarnings(
    "ignore",
    category=DeprecationWarning,
    message=r".*datetime\.utcnow\(\) is deprecated.*",
)

# (Optional) Could add global fixtures here later
