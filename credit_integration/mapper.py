from django.utils import timezone

from credit_integration.enums import CreditDecisionStatus


def map_credit_decision_status(code):
    status = CreditDecisionStatus.NO
    if code == "1":
        status = CreditDecisionStatus.CONSIDERATION
    if code == "2":
        status = CreditDecisionStatus.YES
    return status


def map_consumer_response(json_data, request):
    result = [
        {
            "status": map_credit_decision_status(
                json_data["consumerResponse"]["decisionProposalData"][
                    "decisionProposal"
                ]["proposal"]["code"]
            ),
            "official_name": json_data["consumerResponse"]["decisionProposalData"][
                "customerData"
            ]["name"],
            "claimant": request.user,
            "created_at": timezone.now(),
            "reasons": [],
        }
    ]

    for factor in json_data["consumerResponse"]["decisionProposalData"][
        "decisionProposal"
    ]["proposal"]["factorRow"]:
        result[0]["reasons"].append(
            {"reason_code": factor["code"], "reason": factor["text"]}
        )

    return result
