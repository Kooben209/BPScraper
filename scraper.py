import os
import sys
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException ,NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime, timedelta
import time
from urllib import parse
from bs4 import BeautifulSoup
import scraperwiki
import setEnv

import alterDatabase

os.environ['SCRAPERWIKI_DATABASE_NAME'] = 'sqlite:///data.sqlite'

def safe_execute(default, exception, function, *args):
    try:
        return function(*args).get_attribute('value')
    except exception:
        return default

DEBUG = 0
if os.environ.get("MORPH_DEBUG") is not None:
	DEBUG = int(os.environ["MORPH_DEBUG"])

DOMAIN = '/'
if os.environ.get("MORPH_DOMAIN") is not None:
	DOMAIN = os.environ["MORPH_DOMAIN"]

SLEEP_SECS = 5
if os.environ.get("MORPH_SLEEP") is not None:
	SLEEP_SECS = int(os.environ["MORPH_SLEEP"])

DELAY_SECS = 5
if os.environ.get("MORPH_DELAY") is not None:
    #time to wait when looking for elements on page
    DELAY_SECS = int(os.environ["MORPH_DELAY"]) # seconds

RANGE_DAYS = 7
if os.environ.get("MORPH_RANGE_DAYS") is not None:
    RANGE_DAYS = int(os.environ["MORPH_RANGE_DAYS"]) # seconds

START_URL = '#'
if os.environ.get("MORPH_START_URL") is not None:
	START_URL = os.environ["MORPH_START_URL"]

DOCUMENTS_URL = '#'
if os.environ.get("MORPH_DOCUMENTS_URL") is not None:
	DOCUMENTS_URL = os.environ["MORPH_DOCUMENTS_URL"]

SEARCH_ITEMS = {k:v for (k,v) in os.environ.items() if 'MORPH_SEARCH' in k}

WEB_DRIVER_OPTIONS = Options()
WEB_DRIVER_OPTIONS.add_argument("--headless")
WEB_DRIVER_OPTIONS.add_argument("--disable-gpu")

WEB_DRIVER_OPTIONS.add_argument("--no-sandbox")
WEB_DRIVER_OPTIONS.add_argument("start-maximized")
WEB_DRIVER_OPTIONS.add_argument("disable-infobars")
WEB_DRIVER_OPTIONS.add_argument("--disable-extensions")

if not DEBUG:
    WEB_DRIVER_OPTIONS.add_argument("--log-level=3")

WEB_DRIVER_OPTIONS.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36")

scraperwiki.sqlite.execute("CREATE TABLE IF NOT EXISTS 'data' ('application' TEXT, 'dateAdded' DATE, 'decision' TEXT, 'address' TEXT, 'proposal' TEXT, 'applicationType' TEXT, 'applicationURL' TEXT, 'documentsURL' TEXT, 'searchName' TEXT,'amendedDateTime' DATETIME, PRIMARY KEY('application','dateAdded','decision'))")
scraperwiki.sqlite.execute("CREATE UNIQUE INDEX IF NOT EXISTS 'data_unique_key' ON 'data' ('application','dateAdded','decision')")

#driver = webdriver.Chrome(options=WEB_DRIVER_OPTIONS,executable_path='/usr/local/bin/chromedriver')
driver = webdriver.Chrome(options=WEB_DRIVER_OPTIONS)

#set dates
todayDate = datetime.now().strftime("%d/%m/%Y")
fromDate = datetime.now() - timedelta(days=RANGE_DAYS)
fromDate = fromDate.strftime("%d/%m/%Y")

#initial page load
driver.get(START_URL)

for k, v in SEARCH_ITEMS.items():
    searchName = k.replace('MORPH_SEARCH_','')
    #run search twice, once for applications received and once for decisions added
    i = 0
    while i < 2:
        #reset form
        resetBtn = driver.find_element_by_id('MainContent_btnReset')
        resetBtn.click()
        
        if 'ROAD' in k:
            wardName = ''
            roadName = v
            #set road name
            roadNameInput = driver.find_element_by_id('ctl00_MainContent_RadStreetName_Input')
            roadNameInput.send_keys(roadName.replace('#',''))
        elif 'WARD' in k:
            roadName = ''
            wardName = v
            #set ward
            wardInput= driver.find_element_by_id('ctl00_MainContent_ddlWard_Input')
            wardInput.click()
            time.sleep(2)
            wardOptions = driver.find_element_by_id('ctl00_MainContent_ddlWard_DropDown').find_elements_by_class_name('rcbItem')
            for option in wardOptions:
                if option.text == wardName:
                    option.click()
                    break        
        else:
            #search all apps
            wardName = ''
            roadName = ''

        if DEBUG:
            searchCriteria = "road name: "+roadName+" - ward name: "+wardName
            print("running for for "+searchCriteria+" between "+fromDate+" and "+todayDate)
        
        appsReceivedDateFromInput= driver.find_element_by_id('MainContent_txtDateReceivedFrom')
        appsReceivedDateToInput= driver.find_element_by_id('MainContent_txtDateReceivedTo')
        appsDecisionDateFromInput= driver.find_element_by_id('MainContent_txtDateIssuedFrom')
        appsDecisionDateToInput= driver.find_element_by_id('MainContent_txtDateIssuedTo')

        if i == 0:
            if DEBUG:
                print("running applications check for "+searchCriteria+" between "+fromDate+" and "+todayDate)
            #set applications Received date range
            appsReceivedDateFromInput.send_keys(fromDate)
            appsReceivedDateToInput.send_keys(todayDate)
        else:
            if DEBUG:
                print("running decisions check for "+searchCriteria+" between "+fromDate+" and "+todayDate)
            #set decisions added date range
            appsDecisionDateFromInput.send_keys(fromDate)
            appsDecisionDateToInput.send_keys(todayDate)

        #submit form
        time.sleep(SLEEP_SECS)
        driver.find_element_by_name('ctl00$MainContent$btnSearch').click()

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        table = soup.find("table", { "class" : "rgMasterTable rgClipCells" })
        rows = table.findAll("tr", {"class":["rgRow", "rgAltRow"]})

        if DEBUG:
            print("Returned "+str(len(rows))+" Rows")

        if len(rows) < 1:
            i += 1
            try:
                backPageBtn = WebDriverWait(driver, DELAY_SECS).until(EC.presence_of_element_located((By.ID, 'MainContent_hypBack')))
                backPageBtn.click()
                time.sleep(SLEEP_SECS)
            except:
                break
            continue

        try:
            #set page size
            pageSizeInput = WebDriverWait(driver, DELAY_SECS).until(EC.presence_of_element_located((By.ID, 'ctl00_MainContent_grdResults_ctl00_ctl03_ctl01_PageSizeComboBox_Arrow')))
            pageSizeInput.click()
            pageSizeOption = WebDriverWait(driver, DELAY_SECS).until(EC.presence_of_element_located((By.XPATH, '//*[@id="ctl00_MainContent_grdResults_ctl00_ctl03_ctl01_PageSizeComboBox_DropDown"]/div/ul/li[3]')))
            time.sleep(SLEEP_SECS)
            pageSizeOption.click()
        except TimeoutException:
            if DEBUG:
                print("pageSizeInput element not present")

        #loop over pages
        while True:  
            for row in rows:
                application = row.findAll("td")[1].text.strip()
                dateAdded = datetime.strptime(row.findAll("td")[0].text.strip(), '%d/%m/%Y').date()
                decision = row.findAll("td")[4].text.strip() or 'Under consideration'
                address = row.findAll("td")[2].text.strip()
                proposal = row.findAll("td")[3].text.strip()
                applicationURL = row.findAll("td")[1].find("a").get('href') or '#'
                applicationType = "Full Planning Application"
                if 'prior approval' in proposal.lower():
                    applicationType = 'Prior Approval'
                elif 'change of use' in proposal.lower():
                    applicationType = 'Change of use'
                elif 'Prior notification' in proposal.lower():
                    applicationType = 'Prior Approval'
                elif 'lawful development certificate' in proposal.lower():
                    applicationType = 'Lawful Development Application'
                elif 'extension' in proposal.lower():
                    applicationType = 'Extension'
                elif 'alteration' in proposal.lower():
                    applicationType = 'Alteration'
                elif 'outline' in proposal.lower():
                    applicationType = 'Outline Planning'
                elif 'erection of' in proposal.lower():
                    applicationType = 'New Build'
                elif 'felling' in proposal.lower():
                    applicationType = 'Trees'
                elif 'tree' in proposal.lower():
                    applicationType = 'Trees'
                elif 't1' in proposal.lower():
                    applicationType = 'Trees'
                elif 'tg2' in proposal.lower():
                    applicationType = 'Trees'

                href = parse.urlparse(applicationURL)
                params = parse.parse_qs(href.query)
                if 'recno' in params:
                    recno = params['recno'][0]
                    documentsURL = DOCUMENTS_URL+recno
                else:
                    documentsURL = '#'

                amendedDateTime = datetime.now()
                
                #get other details from DisplayRecord
                #get href from a tag with id containing string _hypDisplayRecord 
                displayRecordURL = row.find("a", {"id" : lambda L: L and L.endswith('_hypDisplayRecord')}).get('href')
                #follow link in new window and get details
                main_window= driver.current_window_handle
                #Open a new tab in blank
                driver.execute_script("window.open(''),'_blannk'")
                # Switch to the new window
                driver.switch_to.window(driver.window_handles[1])
                #Change the url in the .get**
                driver.get(DOMAIN+displayRecordURL)
                time.sleep(SLEEP_SECS)

                agent = safe_execute("",NoSuchElementException,driver.find_element_by_id,"MainContent_txtAgtName")
                caseOfficer = safe_execute("",NoSuchElementException,driver.find_element_by_id,"MainContent_txtCaseOfficer")
                applicant = safe_execute("",NoSuchElementException,driver.find_element_by_id,"MainContent_txtAppName")
                appOfficialType = safe_execute("",NoSuchElementException,driver.find_element_by_id,"MainContent_txtType")
                decisionMethod = safe_execute("",NoSuchElementException,driver.find_element_by_id,"MainContent_txtCommitteeDelegated")
                receivedDate = safe_execute("",NoSuchElementException,driver.find_element_by_id,"MainContent_txtReceivedDate")
                advertExpiry = safe_execute("",NoSuchElementException,driver.find_element_by_id,"MainContent_txtAdvertExpiry")
                siteNoticeExpiry = safe_execute("",NoSuchElementException,driver.find_element_by_id,"MainContent_txtSiteNoticeExpiry")
                validDate = safe_execute("",NoSuchElementException,driver.find_element_by_id,"MainContent_txtValidDate")
                neighbourExpiry = safe_execute("",NoSuchElementException,driver.find_element_by_id,"MainContent_txtNeighbourExpiry")
                issueDate = safe_execute("",NoSuchElementException,driver.find_element_by_id,"MainContent_txtIssueDate")
                decisionDate = safe_execute("",NoSuchElementException,driver.find_element_by_id,"MainContent_txtDecisionDate")
                committeeDelegatedDate = safe_execute("",NoSuchElementException,driver.find_element_by_id,"MainContent_txtCommitteeDelegatedDate")
                applicationStatus = safe_execute("",NoSuchElementException,driver.find_element_by_id,"MainContent_tdApplicationStatus")

                #Close Current Tab
                driver.close()
                #Focus to the main window
                driver.switch_to.window(main_window)

                if DEBUG:
                    print("write to db")
                scraperwiki.sqlite.execute("INSERT OR IGNORE INTO 'data' VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (application,dateAdded,decision,address,proposal,applicationType,applicationURL,documentsURL,searchName,amendedDateTime,agent,caseOfficer,applicant,appOfficialType,decisionMethod,decisionDate,siteNoticeExpiry))
            #if there is a next button click it then get rows and loop over them again
            try:
                nextPageBtn = WebDriverWait(driver, DELAY_SECS).until(EC.presence_of_element_located((By.XPATH, '//*[@id="ctl00_MainContent_grdResults_ctl00"]/tfoot/tr/td/table/tbody/tr/td/div[3]/input[1]')))
                if nextPageBtn.get_attribute("onclick") == 'return false;':
                    break
                nextPageBtn.click()
                time.sleep(SLEEP_SECS)
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                table = soup.find("table", { "class" : "rgMasterTable rgClipCells" })
                rows = table.findAll("tr", {"class":["rgRow", "rgAltRow"]})
            except:
                break
        i += 1
        try:
            backPageBtn = WebDriverWait(driver, DELAY_SECS).until(EC.presence_of_element_located((By.ID, 'MainContent_hypBack')))
            backPageBtn.click()
            time.sleep(SLEEP_SECS)
        except:
            break

driver.quit()
