from playwright.sync_api import sync_playwright
from playwright.sync_api import Page, Locator
from langchain_core.tools import tool
from ..manager import browser_manager
import json
import time
import random

SOM_STATE = []

def get_som_state():
    global SOM_STATE
    return SOM_STATE

def set_som_state(state):
    global SOM_STATE
    SOM_STATE = state