import os
import scraperwiki
import setEnv


DB_ALTER = 0
if os.environ.get("MORPH_DB_ALTER") is not None:
	DB_ALTER = int(os.environ["MORPH_DB_ALTER"])

def columnExists(table_name, column_name):
    results = scraperwiki.sqlite.execute('PRAGMA table_info({})'.format(table_name))
    for row in results['data']:
        if row[1] == column_name:
            return True
    return False


if DB_ALTER == 1:
    os.environ['SCRAPERWIKI_DATABASE_NAME'] = 'sqlite:///data.sqlite'

    try:
        #add agent
        applied=0
        if not columnExists('data','agent'):
            scraperwiki.sqlite.execute("ALTER TABLE '{tn}' ADD COLUMN '{cn}' {ct} "\
                    .format(tn='data', cn='agent', ct='TEXT'))
            applied=1
        
        #add caseOfficer   
        if not columnExists('data','caseOfficer'):
            scraperwiki.sqlite.execute("ALTER TABLE '{tn}' ADD COLUMN '{cn}' {ct} "\
                    .format(tn='data', cn='caseOfficer', ct='TEXT'))
            applied=1
            
        #add applicant   
        if not columnExists('data','applicant'):
            scraperwiki.sqlite.execute("ALTER TABLE '{tn}' ADD COLUMN '{cn}' {ct} "\
                    .format(tn='data', cn='applicant', ct='TEXT'))
            applied=1
            
        #add appOfficialType   
        if not columnExists('data','appOfficialType'):
            scraperwiki.sqlite.execute("ALTER TABLE '{tn}' ADD COLUMN '{cn}' {ct} "\
                    .format(tn='data', cn='appOfficialType', ct='TEXT'))
            applied=1
            
        #add decisionMethod   
        if not columnExists('data','decisionMethod'):
            scraperwiki.sqlite.execute("ALTER TABLE '{tn}' ADD COLUMN '{cn}' {ct} "\
                    .format(tn='data', cn='decisionMethod', ct='TEXT'))
            applied=1
            
        #add decisionDate   
        if not columnExists('data','decisionDate'):
            scraperwiki.sqlite.execute("ALTER TABLE '{tn}' ADD COLUMN '{cn}' {ct} "\
                    .format(tn='data', cn='decisionDate', ct='DATE'))
            applied=1
            
        #add siteNoticeExpiry   
        if not columnExists('data','siteNoticeExpiry'):
            scraperwiki.sqlite.execute("ALTER TABLE '{tn}' ADD COLUMN '{cn}' {ct} "\
                    .format(tn='data', cn='siteNoticeExpiry', ct='DATE'))
            applied=1
            
            
    except Exception as e:
        if hasattr(e, 'message'):
            print(e.message)
        else:
            print(e)    
    else:
        if applied==1:
            print("DB alter applied successfully")

