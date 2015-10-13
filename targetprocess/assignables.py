from targetprocess.sourcebase import TargetprocessSourceBase

from vizydrop.fields import *
from .filter import TargetprocessAssignablesFilter


class TargetprocessAssignablesSource(TargetprocessSourceBase):
    class Meta:
        identifier = "assignables"
        name = "All Entities"
        tags = ["Assignables", "Bugs", "User Stories", "Features", "Tasks"]
        description = "List of all entities (bugs, stories, features, and tasks)"
        filter = TargetprocessAssignablesFilter

        tp_api_call = "Assignables"

    class Schema(TargetprocessSourceBase.Schema):
        # shim EntityType in there...
        EntityType = TextField(name="Entity Type", description="Type of entity e.g. Bug, Feature, Task, etc.",
                               response_loc="EntityType-Name")


class TargetprocessUserStoriesSource(TargetprocessAssignablesSource):
    class Meta:
        identifier = "userstories"
        name = "User Stories"
        tags = ["User Stories", "Stories", ]
        description = "List of user stories"
        filter = TargetprocessAssignablesFilter

        tp_api_call = "UserStories"

    class Schema(TargetprocessSourceBase.Schema):
        # Shims!
        Feature = TextField(name="Feature", description="Feature where this User story is found",
                            response_loc="Feature-Name")


class TargetprocessBugsSource(TargetprocessAssignablesSource):
    class Meta:
        identifier = "bugs"
        name = "Bugs"
        tags = ["Bugs", "Defects", ]
        description = "List of bugs"
        filter = TargetprocessAssignablesFilter

        tp_api_call = "Bugs"

    class Schema(TargetprocessSourceBase.Schema):
        # Shims!
        Severity = TextField(name="Severity", description="Bug Severity", response_loc="Severity-Name")
        UserStory = TextField(name="User Story", description="User story where this bug is found",
                               response_loc="UserStory-Name")
        Feature = TextField(name="Feature", description="Feature where this bug is found", response_loc="Feature-Name")


class TargetprocessFeaturesSource(TargetprocessAssignablesSource):
    class Meta:
        identifier = "features"
        name = "Features"
        tags = ["Features", ]
        description = "List of features"
        filter = TargetprocessAssignablesFilter

        tp_api_call = "Features"


class TargetprocessRequestsSource(TargetprocessAssignablesSource):
    class Meta:
        identifier = "requests"
        name = "Requests"
        tags = ["Requests", "Ideas", ]
        description = "List of requests"
        filter = TargetprocessAssignablesFilter

        tp_api_call = "Requests"


class TargetprocessTasksSource(TargetprocessAssignablesSource):
    class Meta:
        identifier = "tasks"
        name = "Tasks"
        tags = ["Tasks", ]
        description = "List of tasks"
        filter = TargetprocessAssignablesFilter

        tp_api_call = "Tasks"
