from git import Repo, InvalidGitRepositoryError

from server import logger

try:
    repo = Repo('..')
except InvalidGitRepositoryError as e:
    logger.error("Trying to get server version, but no git repo found. Make sure it's included!")
    exit(1)

tags = sorted(repo.tags, key=lambda t: t.commit.committed_datetime)

if tags:
    __version__ = tags[-1]
else:
    logger.error("Trying to get server version, but there are no tags to derive version from!")
    exit(1)
