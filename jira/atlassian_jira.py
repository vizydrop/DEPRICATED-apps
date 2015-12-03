from vizydrop.sdk.application import Application
from .authentication import JIRABasicAuth
from .issues import JIRAIssuesSource


class AtlassianJIRA(Application):
    class Meta:
        version = "1.0"
        name = "JIRA"
        website = "https://www.atlassian.com/software/jira"
        color = "#FFFFFF"
        description = "JIRA is the tracker for teams planning and building great products. Thousands of teams choose " \
                      "JIRA to capture and organize issues, assign work, and follow team activity. At your desk or " \
                      "on the go with the new mobile interface, JIRA helps your team get the job done."
        tags = ['pm', 'project tracker', ]

        authentication = [JIRABasicAuth, ]

        sources = [JIRAIssuesSource, ]
