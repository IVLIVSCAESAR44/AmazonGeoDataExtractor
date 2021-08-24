from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
from datetime import timedelta
from datetime import date
from datetime import datetime
import pyodbc
import shutil

#password and username to be used to log in
usernamestr = 'InsertUsername'
passwordstr = 'InsertPassword'
options = webdriver.ChromeOptions() 
options.add_argument("user-data-dir=Location of your Chrome User Data Directory")
options.add_experimental_option("prefs", {"download.default_directory": r"Location of your download directory where you want the files to go",
  "download.prompt_for_download": False,
  "download.directory_upgrade": True,
  "safebrowsing.enabled": True
})
options.add_experimental_option("excludeSwitches", ['enable-automation'])

w = webdriver.Chrome(options=options)

#force it to use my browser so I dont get 2FA 
try:

#Go to login link
    w.get('https://vendorcentral.amazon.com')
#do the actual filling in
    username = w.find_element_by_id('ap_email')
    username.click()
    username.clear()
    username.send_keys(usernamestr)
    time.sleep(1)

    password = w.find_element_by_id('ap_password')
    password.send_keys(passwordstr)
    time.sleep(1)

    signinbtn = w.find_element_by_id('signInSubmit')
    signinbtn.click()
    time.sleep(2)
    print('Sign in Complete....')
    
    reportshover = w.find_element_by_id("vss_navbar_tab_reports")
    hover = ActionChains(w).move_to_element(reportshover)
    hover.perform()

    analyticsbtn = w.find_element_by_xpath("//*[@id='ARAP_I90_Amazon_Retail_Analytics_text']").click()
    print('Reports tab clicked....')
    time.sleep(5)
    
    
    GeoDataSalesInsightsReport = w.find_element_by_xpath("//a[@href='/analytics/dashboard/geographicSalesInsights']").click()
    print('Geo Data Reports tab clicked....')
    time.sleep(10)
    
    download1 = w.find_element_by_xpath("//*[@id='downloadButton']/awsui-button-dropdown/div/awsui-button/button/span").click()
    print('Download Button clicked....')
    time.sleep(7)
    
    csv = w.find_element_by_xpath("//*[@id='downloadButton']/awsui-button-dropdown/div/div/ul/li[3]/ul/li[2]").click()
    print('CSV Download clicked....')

    WebDriverWait(w, 60).until(EC.alert_is_present())         
    alert = w.switch_to.alert
    alert.accept()  
    print('Alert accepted....')
    
    time.sleep(45)
    w.quit()
    print('Webdriver portion complete....')
    
    time.sleep(3)
    
    today = date.today()
    subDays = timedelta(4)
    
    execdate = today - subDays
    strexecdate = str(execdate)   
    
#Delete first row
    path = r'Path where you stored the file after download'
    print('File Opened....')
    
    df = pd.read_csv(path + 'Geographic Sales Insights_Detail View_US.csv', sep=',', index_col=False, dtype ='str', encoding='utf-8')
    
    headers = df.loc[0]
        
    new_df = pd.DataFrame(df.values[1:], columns=headers)
    print('Copying data into new data frame....')
    
    new_df["Activity Date"] = execdate
    print('Adding Activity Date Column')
    
    new_df.columns = new_df.columns.str.replace(' ','_')
    print('Replaced spaces with underscores for data integrity')
    
    new_df.rename(columns = {'Country/Region':'Country'}, inplace = True)
    print('Renaming column Country')
    
    new_df = new_df.replace(',','', regex=True)
    new_df = new_df.fillna(value=0)   
    del df   

    conn = pyodbc.connect('Driver={ODBC Driver 17 for SQL Server};'
                          'Server=InsertServerName;'
                          'Database=InsertDatabasename;'
                          'Trusted_Connection=yes;'
                          'autocommit=False;')
    
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    
    print('Beginning Data Load: ' + current_time )
    cursor=conn.cursor()
    for row in new_df.itertuples():
        cursor.execute('''
                   INSERT INTO dbo.Table 
            ([ASIN]
           ,[Product_Title]
           ,[Country]
           ,[State]
           ,[City]
           ,[ZIP]
           ,[Shipped_Revenue]
           ,[Shipped_Units]
           ,[Activity_Date])
            
            VALUES (?,?,?,?,?,?,?,?,?)
            ''',
            row.ASIN,
            row.Product_Title,
            row.Country,
            row.State,
            row.City,
            row.ZIP,
            row.Shipped_Revenue,
            row.Shipped_Units,
            row.Activity_Date
            )
    now1 = datetime.now()
    current_time1 = now1.strftime("%H:%M:%S")
    print('Stage load complete: ' + current_time1)    
    
    cursor.execute("{CALL dbo.SP for pushing data into production}")
    print('Production Load Executed')               
    cursor.commit()
    cursor.close()
    conn.close()    
    print('Connection closed')    
    
    new_df.to_csv(path + 'Geographic Sales Insights_Detail View_US.csv', index=False, encoding='utf-8-sig')
    print('File Saved')

    shutil.move('Old File Location', 'File Archive Location')
    print('File moved to Archive folder')
    
except Exception as e:
    print(e)







