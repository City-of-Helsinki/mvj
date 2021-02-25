from decimal import Decimal

from django.utils.dateparse import parse_date
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from leasing.utils import calculate_increase_with_360_day_calendar


class CalculateIncreaseWith360DayCalendar(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        return self.process_request(request, request.data)

    def get(self, request, format=None):
        return self.process_request(request, request.query_params)

    def process_request(self, request, data):
        start_date = parse_date(data.get("start_date"))
        end_date = parse_date(data.get("end_date"))
        percentage = Decimal(data.get("percentage"))
        amount = Decimal(data.get("amount"))

        result_dict = {}
        result_dict["result"] = calculate_increase_with_360_day_calendar(
            start_date, end_date, percentage, amount
        )

        return Response(result_dict)
