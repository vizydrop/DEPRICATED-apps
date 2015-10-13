from vizydrop.sdk.application import Application

from .authentication import TargetprocessBasicAuth, TargetproessTokenAuth
from .assignables import *


class Targetprocess(Application):
    class Meta:
        version = "1.0"
        name = "Targetprocess"
        website = "https://www.targetprocess.com/"
        color = "#000000"
        description = "Targetprocess.com, an expert in agile project management software for Agile programming needs." \
                      " Manage projects in Scrum or Kanban easily with agile and lean project management tools."
        tags = ['pm', 'project tracker', 'kanban', 'scrum', ]

        authentication = [TargetprocessBasicAuth, TargetproessTokenAuth, ]

        sources = [TargetprocessAssignablesSource, TargetprocessUserStoriesSource, TargetprocessBugsSource,
                   TargetprocessRequestsSource, TargetprocessFeaturesSource, TargetprocessTasksSource]
