import csv
import sys


def find_longest_commit(csv_filename):
    longest_commit_hash = None
    longest_commit_length = 0

    last_commit_index = 0
    last_commit_hash = None

    with open(csv_filename, 'r') as csv_in:
        reader = csv.DictReader(csv_in)
        for idx, row in enumerate(reader):
            if row['change_cmake'] == 'True':
                if idx - last_commit_index > longest_commit_length:
                    longest_commit_length = idx - last_commit_index
                    prev_longest_commit_hash = last_commit_hash
                    longest_commit_hash = row['commit_id']
                last_commit_index = idx
                last_commit_hash = row['commit_id']

    print("Longest length is {} from {} to {}".format(longest_commit_length,
                                                      prev_longest_commit_hash,
                                                      longest_commit_hash))


if __name__ == '__main__':
    filename = sys.argv[1]
    find_longest_commit(filename)

