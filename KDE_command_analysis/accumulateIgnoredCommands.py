from collections import Counter
import csv
from datetime import datetime

f = open("ignored_commands.txt", "r")
allIgnored = f.read()
allIgnored = allIgnored.replace("[enterCommand_invocation] Command ignored: ","").splitlines()
command_numbers = Counter(allIgnored)
with open('KDE-ignored-commands-report-{}.csv'.format(str(int(datetime.now().timestamp()))), 'w') as output_file:
    csv_out = csv.writer(output_file, delimiter=',')
    for command in command_numbers:
        csv_out.writerow([command,command_numbers[command]])
