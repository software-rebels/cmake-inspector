import sys
import csv
from datetime import datetime
from git import Repo

FIX_RELATED_WORDS = ['fix', 'address', 'issue', 'problem', 'bug']
CSV_HEADERS = ['project_name', 'commit_id', 'commit_message', 'changed_files', 'bug_fix',
               'change_cmake']


def main(repo_dir, start_commit, end_commit='master'):
    repo = Repo(repo_dir)
    assert not repo.bare
    csv_rows = []
    # Start from a release commit, until reaching to master, we iterate over commits
    prev_commit = start_commit
    current_commit = None
    commits_to_analyse = list(repo.iter_commits("{}...{}".format(start_commit, end_commit)))
    for idx, commit in enumerate(reversed(commits_to_analyse)):
        current_commit = commit
        diffs = repo.git.diff('{}..{}'.format(prev_commit, current_commit), name_only=True)
        diffs = diffs.split('\n')
        if any(word in commit.message.lower() for word in FIX_RELATED_WORDS):
            csv_rows.append({
                'project_name': 'Etlegacy',
                'commit_id': current_commit.hexsha,
                'commit_message': current_commit.message,
                'changed_files': diffs,
                'bug_fix': True,
                'change_cmake': any('.cmake' in item for item in diffs)
            })
        elif any('.cmake' in item.lower() for item in diffs) or any('CMakeLists.txt' in item for item in diffs):
            csv_rows.append({
                'project_name': 'Etlegacy',
                'commit_id': current_commit.hexsha,
                'commit_message': current_commit.message,
                'changed_files': diffs,
                'bug_fix': False,
                'change_cmake': True
            })
        prev_commit = commit

    with open('output-{}.csv'.format(str(int(datetime.now().timestamp()))), 'w') as output_file:
        csv_out = csv.DictWriter(output_file, fieldnames=CSV_HEADERS)
        csv_out.writeheader()
        csv_out.writerows(csv_rows)


if __name__ == "__main__":
    argv = sys.argv
    project_dir = argv[1]
    release_commit = argv[2]
    main(project_dir, release_commit)
