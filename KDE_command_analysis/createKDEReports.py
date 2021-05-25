import csv
from ctypes import Array  #importing the library
import os
from datetime import datetime
import re
from pprint import pprint

regex = r", in (.*?) (.*?) File (.*?)\"(.*?)\", line ([0-9]*)?"
reportCSV=[]
CSV_HEADERS = ['repo', 'status', 'error','errorPlace']
with open("repo_list.csv") as csvFile:   #open the file
  CSVdata = csv.reader(csvFile, delimiter=',')  #read the data
  for row in CSVdata:   #loop through each row
    reportRow= {}
    repoName= row[0]   #print the data
    print(repoName)
    fileName='./issues/'+repoName.replace('/','_')+'.txt'
    reportRow[CSV_HEADERS[0]]=repoName
    if os.path.isfile(fileName):
        reportRow[CSV_HEADERS[1]]='Error'
        with open(fileName) as f:
            reportRow[CSV_HEADERS[2]] = f.read()
            matches = re.findall(regex, reportRow[CSV_HEADERS[2]] , re.MULTILINE)
            reportRow[CSV_HEADERS[3]] = (' & '.join(matches[-1]))
    else:
        reportRow[CSV_HEADERS[1]]='Pass'
        reportRow[CSV_HEADERS[2]]=''
        reportRow[CSV_HEADERS[3]]=''
    
    reportCSV.append(reportRow)
  csvFile.close()   #close the file


with open('KDE-report-{}.csv'.format(str(int(datetime.now().timestamp()))), 'w') as output_file:
    csv_out = csv.DictWriter(output_file, fieldnames=CSV_HEADERS)
    csv_out.writeheader()
    csv_out.writerows(reportCSV)
