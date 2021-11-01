from django.core.management.base import BaseCommand

from leasing.enums import AreaType, DetailedPlanClass
from leasing.models import Area, DetailedPlan


class Command(BaseCommand):
    help = "Update detailed plans"

    def handle(self, *args, **options):  # noqa: C901 TODO
        from auditlog.registry import auditlog

        # Unregister all models from auditlog when importing
        for model in list(auditlog._registry.keys()):
            auditlog.unregister(model)

        detailed_plans = Area.objects.filter(type=AreaType.DETAILED_PLAN)

        if not detailed_plans:
            self.stdout.write("Detailed plan: No detailed plans found in area table")
            return

        for detailed_plan in detailed_plans:
            match_data = {
                "identifier": detailed_plan.identifier,
            }

            detailed_plan_class = None
            if detailed_plan.metadata.get("state_name") == "Vireillä":
                detailed_plan_class = DetailedPlanClass.PENDING
            if detailed_plan.metadata.get("state_name") == "Voimassa":
                detailed_plan_class = DetailedPlanClass.EFFECTIVE
            lawfulness_date = detailed_plan.metadata.get("final_date")

            acceptor = ""
            plan_stage = ""
            diary_number = ""
            pre_detailed_plan = Area.objects.filter(
                type=AreaType.PRE_DETAILED_PLAN, identifier=detailed_plan.identifier
            )
            if pre_detailed_plan:
                acceptor = pre_detailed_plan.metadata.get("acceptor")
                plan_stage = pre_detailed_plan.metadata.get("plan_stage")
                diary_number = pre_detailed_plan.metadata.get("diary_number")

            other_data = {
                "acceptor": acceptor,
                "detailed_plan_class": detailed_plan_class,
                "plan_stage": plan_stage,
                "diary_number": diary_number,
                "lawfulness_date": lawfulness_date,
            }

            DetailedPlan.objects.update_or_create(defaults=other_data, **match_data)
