from targetprocess.sourcebase import TargetprocessGeneral
from targetprocess.filter import TargetprocessBaseFilter
from vizydrop.fields import DecimalField, DateTimeField, NumberField, TextField


class TargetprocessProject(TargetprocessGeneral):
    class Meta:
        identifier = "project"
        name = "Projects"
        tags = ["PM", "Projects"]
        description = "Project"
        filter = TargetprocessBaseFilter

        tp_api_call = "Projects"

    class Schema(TargetprocessGeneral.Schema):
        Progress = DecimalField(name='Progress', description='Percent done for project')
        PlannedStartDate = DateTimeField(name='Planned Start Date', description='Planned start date')
        PlannedEndDate = DateTimeField(name='Planned End Date', description='Planned end date')
        ForecastEndDate = DateTimeField(name='Forecasted End Date', description='End date predicted on current progress')
        AnticipatedEndDate = DateTimeField(name='Anticipated End Date', description='End date predicted on planned duration')
        LeadTime = NumberField(name='Lead Time', description='Number of days between project create date and end date')
        CycleTime = NumberField(name='Cycle Time', description='Number of days between project start date and end date')
        Program = TextField(name='Program', response_loc='Program-Name', description='Program associated with the project')


class TargetprocessProgram(TargetprocessGeneral):
    class Meta:
        identifier = "program"
        name = "Programs"
        tags = ["PM", "Programs"]
        description = "Program"
        filter = TargetprocessBaseFilter

        tp_api_call = "Programs"

    class Schema(TargetprocessGeneral.Schema):
        pass