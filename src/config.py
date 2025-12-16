import os
from dotenv import load_dotenv

load_dotenv()

SMARTCHEM_USERNAME = os.getenv("SMARTCHEM_USERNAME")
SMARTCHEM_PASSWORD = os.getenv("SMARTCHEM_PASSWORD")
SMARTCHEM_URL = os.getenv("SMARTCHEM_URL")

SELECTOR_USERNAME = 'input[name="login"]'
SELECTOR_PASSWORD = 'input[name="password"]'
SELECTOR_LOGIN_BUTTON = 'input.user-submit'

SELECTOR_SEARCH_BOX = "input[name='search']"
SELECTOR_APPLICATIONS_TAB = "text=Applications"
