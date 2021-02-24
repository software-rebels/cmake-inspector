import sys
import os
import csv
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap

commands_freq = dict()
commands_support = []
show_number = 50
colorHeat = False


def main(argv):
    number_of_commands = int(argv[1]) if argv[1] else 100;
    color_heat = (argv[2].lower() != "false") if argv[2] else False;

    if os.path.exists("commandsfreq.csv"):
        with open('commandsfreq.csv', 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                commands_freq[row['command']] = int(row['freq'])
    if os.path.exists("supportedCommands.csv"):
        with open('supportedCommands.csv', 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                commands_support.append(row['command'].lower())

    df = []
    for cmd in commands_freq:
        print(cmd.lower(),' in commands_support',cmd.lower() in commands_support)
        if cmd.lower() not in list(map(lambda x: x['command'], df)):
            df.append({
                'command': cmd.lower(),
                'frequency': commands_freq[cmd],
                'support': cmd.lower() in commands_support,
            })
        else:
            df = list(map(lambda x: {
                'command': x['command'],
                'frequency': x['frequency'] if cmd.lower() != x['command'] else x['frequency'] + commands_freq[cmd],
                'support': x['support'],
            }, df))
    df = pd.DataFrame(df)
    df = df.sort_values(by=['frequency'], ascending=False)

    fig, ax = plt.subplots()
    money = df['frequency'].tolist()[:number_of_commands]
    x = np.arange(len(money))

    if color_heat:
        min_val = np.min(df['frequency'].to_numpy()[:number_of_commands])
        max_val = np.max(df['frequency'].to_numpy()[:number_of_commands])
        color_map = LinearSegmentedColormap.from_list('rg', ["r", "g"], N=max_val - min_val + 1)
        allColors = color_map(np.linspace(0, 1, max_val - min_val + 1))
        bar_colors = []
        for i in range(len(money)):
            bar_colors.append(allColors[max_val - money[i]])
        bar_colors = bar_colors
    else:
        color_map = LinearSegmentedColormap.from_list('rg', ["r", "g"], N=len(money))
        bar_colors = color_map(np.linspace(0, 1, len(money)))
    bar_list = plt.bar(x, money, color=bar_colors)
    plt.xticks(x, df['command'].tolist()[:len(money)])
    ax.tick_params(axis='x', rotation=90)
    ax.set_yscale('log')
    print("\n---------------------------\n")
    for i in range(len(bar_list)):
        # print(df.iloc[[i]]['support'].values[0])
        if df.iloc[[i]]['support'].values[0]:
            bar_list[i].set_hatch('//')
        else:
            print(df.iloc[[i]]['command'].values[0].lower())
    plt.show()


if __name__ == "__main__":
    main(sys.argv)
