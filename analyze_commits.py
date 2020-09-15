import sys
from git import Repo

FIX_RELATED_WORDS = ['fix', 'address', 'issue', 'problem', 'bug']
CSV_HEADERS = ['project_name', 'commit_']


def main(repo_dir, start_commit, end_commit='master'):
    repo = Repo(repo_dir)
    assert not repo.bare
    # Start from a release commit, until reaching to master, we iterate over commits
    prev_commit = start_commit
    current_commit = None
    commits_to_analyse = list(repo.iter_commits("{}...{}".format(start_commit, end_commit)))
    for idx, commit in enumerate(reversed(commits_to_analyse)):
        current_commit = commit
        if any(word in commit.message.lower() for word in FIX_RELATED_WORDS):
            print("Current")
            print(commit.message)
            diffs = repo.git.diff('{}..{}'.format(prev_commit, current_commit), name_only=True)
            print(diffs)
            break
        prev_commit = commit



if __name__ == "__main__":
    argv = sys.argv
    project_dir = argv[1]
    release_commit = argv[2]
    main(project_dir, release_commit)
