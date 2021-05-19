import os
import re


regex = '-c .*\/src(\/\S*)'
found_files = []
with open('a2.txt', 'r') as file_in:
    for line in file_in:
        found_files += re.findall(regex, line)