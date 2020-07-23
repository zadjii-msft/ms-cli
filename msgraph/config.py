"""Configuration settings for console app using device flow authentication
"""

# client id/secret moved to parameter you must pass not hardcode and check in, jeez

AUTHORITY_URL = "https://login.microsoftonline.com/common"
RESOURCE = "https://graph.microsoft.com"
#API_VERSION = "v1.0"
API_VERSION = "beta"
