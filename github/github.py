from .authentication import GitHubOAuth
from .commits import GitHubCommitsSource
from .issues import GitHubIssuesSource
from .contributors import GitHubContributorsStatsSource
from vizydrop.sdk.application import Application

class GitHub(Application):
    class Meta:
        version = "1.1"
        name = "GitHub"
        website = "https://www.github.com"
        color = "#F5F5F5"
        description = "Build software better, together.  Powerful collaboration, code review, and code management for " \
                      "open source and private projects."
        tags = ['scm', 'github', 'code review', ]

        authentication = [GitHubOAuth, ]

        sources = [GitHubCommitsSource, GitHubIssuesSource, GitHubContributorsStatsSource, ]
