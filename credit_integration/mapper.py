from credit_integration.enums import CreditDecisionStatus


def map_credit_decision_status(code):
    status = CreditDecisionStatus.NO
    if code == "1":
        status = CreditDecisionStatus.CONSIDERATION
    if code == "2":
        status = CreditDecisionStatus.YES
    return status
