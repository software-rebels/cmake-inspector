import os
import re


def find_in_log(file_path):
    regex = r'-c .*\/src(\/\S*)'
    found_files = []
    with open(file_path, 'r') as file_in:
        for line in file_in:
            found_files += re.findall(regex, line)
    return set(found_files)


def find_in_tool_output(flattened: dict):
    regex = r'.*\/src(\/\S*)'
    found_files = []
    for key, value_set in flattened.items():
        for item in value_set:
            found_files += re.findall(regex, item)
    return set(found_files)


def compare_results(tool_files: set, make_files: set):
    not_found_files = []
    for item in make_files:
        if item not in tool_files:
            not_found_files.append(item)
    return not_found_files
