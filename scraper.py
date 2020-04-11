import os
import sys
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime, timedelta
import time
from urllib import parse
from bs4 import BeautifulSoup
import scraperwiki
import setEnv

scraperwiki.sqlite.save(unique_keys=['name'], data={"name": "susan", "occupation": "software developer"})


driver.quit()
