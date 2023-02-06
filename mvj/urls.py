import rest_framework.urls
from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions, routers

from credit_integration import urls as credit_integration_urls
from forms.viewsets.form import (
    AnswerViewSet,
    AttachmentViewSet,
    FormViewSet,
    MeetingMemoViewset,
    TargetStatusViewset,
)
from leasing.api_functions import CalculateIncreaseWith360DayCalendar
from leasing.report.viewset import ReportViewSet
from leasing.views import CloudiaProxy, VirreProxy, ktj_proxy
from leasing.viewsets.area_note import AreaNoteViewSet
from leasing.viewsets.auditlog import AuditLogView
from leasing.viewsets.basis_of_rent import BasisOfRentViewSet
from leasing.viewsets.batchrun import (
    JobRunLogEntryViewSet,
    JobRunViewSet,
    JobViewSet,
    ScheduledJobViewSet,
)
from leasing.viewsets.comment import CommentTopicViewSet, CommentViewSet
from leasing.viewsets.contact import ContactViewSet
from leasing.viewsets.contact_additional_views import ContactExistsView
from leasing.viewsets.debt_collection import (
    CollectionCourtDecisionViewSet,
    CollectionLetterTemplateViewSet,
    CollectionLetterViewSet,
    CollectionNoteViewSet,
)
from leasing.viewsets.decision import DecisionCopyToLeasesView, DecisionViewSet
from leasing.viewsets.email import SendEmailView
from leasing.viewsets.infill_development_compensation import (
    InfillDevelopmentCompensationAttachmentViewSet,
    InfillDevelopmentCompensationViewSet,
)
from leasing.viewsets.inspection import InspectionAttachmentViewSet
from leasing.viewsets.invoice import (
    InvoiceNoteViewSet,
    InvoiceRowViewSet,
    InvoiceSetViewSet,
    InvoiceViewSet,
    ReceivableTypeViewSet,
)
from leasing.viewsets.invoice_additional_views import (
    InvoiceCalculatePenaltyInterestView,
    InvoiceCreditView,
    InvoiceExportToLaskeView,
    InvoiceRowCreditView,
    InvoiceSetCreditView,
)
from leasing.viewsets.land_area import (
    CustomDetailedPlanListWithIdentifiersViewSet,
    CustomDetailedPlanViewSet,
    LeaseAreaAttachmentViewSet,
    PlanUnitListWithIdentifiersViewSet,
    PlanUnitViewSet,
    PlotMasterIdentifierList,
)
from leasing.viewsets.land_use_agreement import (
    LandUseAgreementAttachmentViewSet,
    LandUseAgreementInvoiceCreditView,
    LandUseAgreementInvoiceExportToLaskeView,
    LandUseAgreementInvoiceRowCreditView,
    LandUseAgreementInvoiceRowViewSet,
    LandUseAgreementInvoiceSetCreditView,
    LandUseAgreementInvoiceSetViewSet,
    LandUseAgreementInvoiceViewSet,
    LandUseAgreementViewSet,
)
from leasing.viewsets.lease import (
    DistrictViewSet,
    FinancingViewSet,
    HitasViewSet,
    IntendedUseViewSet,
    LeaseTypeViewSet,
    LeaseViewSet,
    ManagementViewSet,
    MunicipalityViewSet,
    NoticePeriodViewSet,
    RegulationViewSet,
    RelatedLeaseViewSet,
    ReservationProcedureViewSet,
    SpecialProjectViewSet,
    StatisticalUseViewSet,
    SupportiveHousingViewSet,
)
from leasing.viewsets.lease_additional_views import (
    LeaseBillingPeriodsView,
    LeaseCopyAreasToContractView,
    LeaseCreateChargeViewSet,
    LeaseCreateCollectionLetterDocumentViewSet,
    LeasePreviewInvoicesForYearView,
    LeaseRentForPeriodView,
    LeaseSetInvoicingStateView,
    LeaseSetRentInfoCompletionStateView,
)
from leasing.viewsets.leasehold_transfer import LeaseholdTransferViewSet
from leasing.viewsets.rent import IndexViewSet
from leasing.viewsets.ui_data import UiDataViewSet
from leasing.viewsets.vat import VatViewSet
from plotsearch.views.plot_search import (
    AreaSearchViewSet,
    FavouriteViewSet,
    GeneratePDF,
    InformationCheckViewSet,
    IntendedSubUseViewSet,
)
from plotsearch.views.plot_search import IntendedUseViewSet as IntendedUsePSViewSet
from plotsearch.views.plot_search import (
    PlotSearchStageViewSet,
    PlotSearchSubtypeViewSet,
    PlotSearchTypeViewSet,
    PlotSearchViewSet,
)
from users.views import UsersPermissions
from users.viewsets import UserViewSet

router = routers.DefaultRouter()
router.register(r"area_note", AreaNoteViewSet)
router.register(r"area_search", AreaSearchViewSet)
router.register(r"attachment", AttachmentViewSet)
router.register(r"basis_of_rent", BasisOfRentViewSet)
router.register(r"collection_court_decision", CollectionCourtDecisionViewSet)
router.register(r"collection_letter", CollectionLetterViewSet)
router.register(r"collection_letter_template", CollectionLetterTemplateViewSet)
router.register(r"collection_note", CollectionNoteViewSet)
router.register(r"comment", CommentViewSet)
router.register(r"comment_topic", CommentTopicViewSet)
router.register(r"contact", ContactViewSet)
router.register(r"custom_detailed_plan", CustomDetailedPlanViewSet)
router.register(r"decision", DecisionViewSet)
router.register(r"district", DistrictViewSet)
router.register(r"favourite", FavouriteViewSet)
router.register(r"financing", FinancingViewSet)
router.register(r"form", FormViewSet, basename="form")
router.register(r"answer", AnswerViewSet)
router.register(r"hitas", HitasViewSet)
router.register(r"index", IndexViewSet)
router.register(
    r"infill_development_compensation", InfillDevelopmentCompensationViewSet
)
router.register(
    r"infill_development_compensation_attachment",
    InfillDevelopmentCompensationAttachmentViewSet,
)
router.register(r"information_check", InformationCheckViewSet)
router.register(r"inspection_attachment", InspectionAttachmentViewSet)
router.register(r"invoice", InvoiceViewSet)
router.register(r"invoice_note", InvoiceNoteViewSet)
router.register(r"invoice_row", InvoiceRowViewSet)
router.register(r"invoice_set", InvoiceSetViewSet)
router.register(r"intended_use", IntendedUseViewSet)
router.register(r"intended_psuse", IntendedUsePSViewSet)
router.register(r"intended_subuse", IntendedSubUseViewSet)
router.register(r"lease", LeaseViewSet, basename="lease")
router.register(r"lease_area_attachment", LeaseAreaAttachmentViewSet)
router.register(
    r"lease_create_charge", LeaseCreateChargeViewSet, basename="lease_create_charge"
)
router.register(
    r"lease_create_collection_letter",
    LeaseCreateCollectionLetterDocumentViewSet,
    basename="lease_create_collection_letter",
)
router.register(r"lease_type", LeaseTypeViewSet)
router.register(r"leasehold_transfer", LeaseholdTransferViewSet)
router.register(r"management", ManagementViewSet)
router.register(r"meeting_memo", MeetingMemoViewset)
router.register(r"municipality", MunicipalityViewSet)
router.register(r"notice_period", NoticePeriodViewSet)
router.register(r"plan_unit", PlanUnitViewSet)
router.register(
    r"plan_unit_list_with_identifiers",
    PlanUnitListWithIdentifiersViewSet,
    basename="planunitlistwithidentifiers",
)
router.register(
    r"custom_detailed_plan_list_with_identifiers",
    CustomDetailedPlanListWithIdentifiersViewSet,
    basename="customdetailedplanlistwithidentifiers",
)
router.register(r"plot_master_identifier_list", PlotMasterIdentifierList)
router.register(r"plot_search", PlotSearchViewSet)
router.register(r"plot_search_stage", PlotSearchStageViewSet)
router.register(r"plot_search_type", PlotSearchTypeViewSet)
router.register(r"plot_search_subtype", PlotSearchSubtypeViewSet)
router.register(r"regulation", RegulationViewSet)
router.register(r"receivable_type", ReceivableTypeViewSet)
router.register(r"related_lease", RelatedLeaseViewSet)
router.register(r"report", ReportViewSet, basename="report")
router.register(r"special_project", SpecialProjectViewSet)
router.register(r"reservation_procedure", ReservationProcedureViewSet)
router.register(r"statistical_use", StatisticalUseViewSet)
router.register(r"supportive_housing", SupportiveHousingViewSet)
router.register(r"target_status", TargetStatusViewset)
router.register(r"ui_data", UiDataViewSet, basename="ui_data")
router.register(r"user", UserViewSet)
router.register(r"vat", VatViewSet)

router.register(r"land_use_agreement", LandUseAgreementViewSet)
router.register(r"land_use_agreement_attachment", LandUseAgreementAttachmentViewSet)
router.register(r"land_use_agreement_invoice", LandUseAgreementInvoiceViewSet)
router.register(r"land_use_agreement_invoice_row", LandUseAgreementInvoiceRowViewSet)
router.register(r"land_use_agreement_invoice_set", LandUseAgreementInvoiceSetViewSet)

pub_router = routers.DefaultRouter()

pub_router.register(r"answer", AnswerViewSet, basename="pub_answer")
pub_router.register(r"area_search", AreaSearchViewSet, basename="pub_area_search")
pub_router.register(r"favourite", FavouriteViewSet, basename="pub_favourite")
pub_router.register(r"form", FormViewSet, basename="pub_form")
pub_router.register(r"intended_use", IntendedUsePSViewSet, basename="pub_intended_use")
pub_router.register(
    r"intended_subuse", IntendedSubUseViewSet, basename="pub_intended_sub_use"
)
pub_router.register(r"plot_search", PlotSearchViewSet, basename="pub_plot_search")
pub_router.register(
    r"plot_search_type", PlotSearchTypeViewSet, basename="pub_plot_search_type"
)
pub_router.register(
    r"plot_search_subtype",
    PlotSearchSubtypeViewSet,
    basename="pub_plot_search_subtype",
)

# Batchrun
router.register("scheduled_job", ScheduledJobViewSet)
router.register("job", JobViewSet)
router.register("job_run", JobRunViewSet)
router.register("job_run_log_entry", JobRunLogEntryViewSet)

additional_api_paths = [
    path("target_status_pdf/", GeneratePDF.as_view(), name="target_status-pdf"),
    path("auditlog/", AuditLogView.as_view(), name="auditlog"),
    path("contact_exists/", ContactExistsView.as_view(), name="contact-exists"),
    path(
        "decision_copy_to_leases/",
        DecisionCopyToLeasesView.as_view(),
        name="decision-copy-to-leases",
    ),
    path(
        "invoice_calculate_penalty_interest/",
        InvoiceCalculatePenaltyInterestView.as_view(),
        name="invoice-calculate-penalty-interest",
    ),
    path("invoice_credit/", InvoiceCreditView.as_view(), name="invoice-credit"),
    path(
        "invoice_export_to_laske/",
        InvoiceExportToLaskeView.as_view(),
        name="invoice-export-to-laske",
    ),
    path(
        "invoice_row_credit/", InvoiceRowCreditView.as_view(), name="invoice-row-credit"
    ),
    path(
        "invoice_set_credit/", InvoiceSetCreditView.as_view(), name="invoice-set-credit"
    ),
    path(
        "land_use_agreement_invoice_credit/",
        LandUseAgreementInvoiceCreditView.as_view(),
        name="land_use_agreement_invoice-credit",
    ),
    path(
        "land_use_agreement_invoice_export_to_laske/",
        LandUseAgreementInvoiceExportToLaskeView.as_view(),
        name="land_use_agreement_invoice-export-to-laske",
    ),
    path(
        "land_use_agreement_invoice_row_credit/",
        LandUseAgreementInvoiceRowCreditView.as_view(),
        name="land_use_agreement_invoice-row-credit",
    ),
    path(
        "land_use_agreement_invoice_set_credit/",
        LandUseAgreementInvoiceSetCreditView.as_view(),
        name="land_use_agreement_invoice-set-credit",
    ),
    path(
        "lease_billing_periods/",
        LeaseBillingPeriodsView.as_view(),
        name="lease-billing-periods",
    ),
    path(
        "lease_copy_areas_to_contract/",
        LeaseCopyAreasToContractView.as_view(),
        name="lease-copy-areas-to-contract",
    ),
    path(
        "lease_preview_invoices_for_year/",
        LeasePreviewInvoicesForYearView.as_view(),
        name="lease-preview-invoices-for-year",
    ),
    path(
        "lease_rent_for_period/",
        LeaseRentForPeriodView.as_view(),
        name="lease-rent-for-period",
    ),
    path(
        "lease_set_invoicing_state/",
        LeaseSetInvoicingStateView.as_view(),
        name="lease-set-invoicing-state",
    ),
    path(
        "lease_set_rent_info_completion_state/",
        LeaseSetRentInfoCompletionStateView.as_view(),
        name="lease-set-rent-info-completion-state",
    ),
    path("send_email/", SendEmailView.as_view(), name="send-email"),
    path("users_permissions/", UsersPermissions.as_view(), name="users-permissions"),
    path(
        "functions/calculate_increase_with_360_day_calendar",
        CalculateIncreaseWith360DayCalendar.as_view(),
    ),
]

schema_view = get_schema_view(
    openapi.Info(
        title="MVJ API",
        default_version="v1",
        description="Test description",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@snippets.local"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    path("v1/", include(router.urls + additional_api_paths)),
    path("v1/pub/", include(pub_router.urls)),
    path(
        "v1/", include((credit_integration_urls, "credit_integration"), namespace="v1"),
    ),
    re_path(r"(?P<base_type>ktjki[ir])/tuloste/(?P<print_type>[\w/]+)/pdf", ktj_proxy),
    path("contract_file/<contract_id>/", CloudiaProxy.as_view()),
    path("contract_file/<contract_id>/<file_id>/", CloudiaProxy.as_view()),
    path("trade_register/<service>/<business_id>/", VirreProxy.as_view()),
    path("admin/", admin.site.urls),
    path("auth/", include(rest_framework.urls)),
    re_path(
        r"^swagger(?P<format>\.json|\.yaml)$",
        schema_view.without_ui(cache_timeout=0),
        name="schema-json",
    ),
    re_path(
        r"^docs/$",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
    re_path(
        r"^redoc/$", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"
    ),
]

if settings.DEBUG and "debug_toolbar" in settings.INSTALLED_APPS:
    import debug_toolbar

    urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
