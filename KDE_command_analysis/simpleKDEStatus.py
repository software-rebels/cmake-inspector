import csv
from ctypes import Array  #importing the library
import os
from datetime import datetime
import re
from pprint import pprint

regex = r", in (.*?) (.*?) File (.*?)\"(.*?)\", line ([0-9]*)?"
reportCSV=[]
CSV_HEADERS = ['repo', 'status']
repoList = []
issued_repos = []
f = open("issued_repos.csv", "r")
allReposWithIssue = f.read()

with open("repo_list.csv") as csvFile:   #open the file
  CSVdata = csv.reader(csvFile, delimiter=',')  #read the data
  for row in CSVdata:   #loop through each row
    reportRow= {}
    reportRow[CSV_HEADERS[0]]= row[0]   

    if allReposWithIssue.find(reportRow[CSV_HEADERS[0]])!=-1:
        reportRow[CSV_HEADERS[1]]='Error'
    else:
        reportRow[CSV_HEADERS[1]]='Pass'
    
    reportCSV.append(reportRow)
  csvFile.close()   #close the file


with open('KDE-simple-report-{}.csv'.format(str(int(datetime.now().timestamp()))), 'w') as output_file:
    csv_out = csv.DictWriter(output_file, fieldnames=CSV_HEADERS)
    csv_out.writeheader()
    csv_out.writerows(reportCSV)
