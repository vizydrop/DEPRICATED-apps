from targetprocess.sourcebase import TargetprocessAssignable, TargetprocessGeneral

from vizydrop.fields import *
from .filter import TargetprocessAssignablesFilter


class TargetprocessAssignablesSource(TargetprocessAssignable):
    class Meta:
        identifier = "assignables"
        name = "All Entities"
        tags = ["Assignables", "Bugs", "User Stories", "Features", "Tasks"]
        description = "List of all entities (bugs, stories, features, and tasks)"
        filter = TargetprocessAssignablesFilter

        tp_api_call = "Assignables"

    class Schema(TargetprocessAssignable.Schema):
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

    class Schema(TargetprocessAssignable.Schema):
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

    class Schema(TargetprocessAssignable.Schema):
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

    class Schema(TargetprocessAssignable.Schema):
        # Shim
        Epic = TextField(name="Epic", description="Epic where this feature is found", response_loc="Epic-Name")


class TargetprocessEpicsSource(TargetprocessAssignablesSource):
    class Meta:
        identifier = "epics"
        name = "Epics"
        tags = ["Epics", ]
        description = "List of epics"
        filter = TargetprocessAssignablesFilter

        tp_api_call = "Epics"

    class Schema(TargetprocessGeneral.Schema):
        # We're removing iteration/team iteration from our assignable schema, so this closely mirrors that
        Project = TextField(name="Project", description="Project where entity is found", response_loc="Project-Name")
        Effort = DecimalField(name="Effort", description="Total efforts for assignable")
        EffortCompleted = DecimalField(name="Effort Completed", description="Effort spent on assignment")
        EffortToDo = DecimalField(name="Effort ToDo", description="Effort required to complete assignment")
        Progress = DecimalField(name="Progress", description="Percent done for assignable")
        TimeSpent = DecimalField(name="Time Spent", description="Total time spent on assignment")
        TimeRemain = DecimalField(name="Time Remain",
                                  description="Total time remaining to complete assignment for Role")
        PlannedStartDate = DateField(name="Planned Start Date",
                                     description="Planned Start date for time-boxed entities such as Iteration, Project, Release")
        PlannedEndDate = DateField(name="Planned End Date",
                                   description="Planned End date for time-boxed entities such as Iteration, Project, Release")
        Assignments = TextField(name="Assignment", description="User assigned to this item",
                                response_loc="Assignments-GeneralUser-LastName")
        LeadTime = NumberField(name="Lead Time",
                               description="Number of days between assignable create date and end date")
        CycleTime = NumberField(name="Cycle Time",
                                description="Number of days between assignable start date and end date")
        ForecastEndDate = DateField(name="Forecast End Date", description="End date predicted on current progress")
        Release = TextField(name="Release",
                            description="Assignable entity can be assigned to Release or can be in project Backlog (Release is not defined in this case)",
                            response_loc="Release-Name")
        EntityState = TextField(name="Entity State", description="State of Assignable",
                                response_loc="EntityState-Name")
        Priority = TextField(name="Priority", description="Priority of Assignable", response_loc="Priority-Name")
        Teams = TextField(name="Teams", description="Assigned Team(s)", response_loc="AssignedTeams-Team-Name")


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
