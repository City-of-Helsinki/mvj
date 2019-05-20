import rest_framework.urls
from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from rest_framework import routers
from rest_framework_swagger.views import get_swagger_view

from batchrun.api.urls import router as batchrun_router
from leasing.views import CloudiaProxy, VirreProxy, ktj_proxy
from leasing.viewsets.area_note import AreaNoteViewSet
from leasing.viewsets.auditlog import AuditLogView
from leasing.viewsets.basis_of_rent import BasisOfRentViewSet
from leasing.viewsets.comment import CommentTopicViewSet, CommentViewSet
from leasing.viewsets.contact import ContactViewSet
from leasing.viewsets.contact_additional_views import ContactExistsView
from leasing.viewsets.debt_collection import (
    CollectionCourtDecisionViewSet, CollectionLetterTemplateViewSet, CollectionLetterViewSet, CollectionNoteViewSet)
from leasing.viewsets.decision import DecisionCopyToLeasesView, DecisionViewSet
from leasing.viewsets.email import SendEmailView
from leasing.viewsets.infill_development_compensation import (
    InfillDevelopmentCompensationAttachmentViewSet, InfillDevelopmentCompensationViewSet)
from leasing.viewsets.inspection import InspectionAttachmentViewSet
from leasing.viewsets.invoice import InvoiceNoteViewSet, InvoiceRowViewSet, InvoiceSetViewSet, InvoiceViewSet
from leasing.viewsets.invoice_additional_views import (
    InvoiceCalculatePenaltyInterestView, InvoiceCreditView, InvoiceExportToLaskeView, InvoiceRowCreditView,
    InvoiceSetCreditView)
from leasing.viewsets.land_area import LeaseAreaAttachmentViewSet
from leasing.viewsets.lease import (
    DistrictViewSet, FinancingViewSet, HitasViewSet, IntendedUseViewSet, LeaseTypeViewSet, LeaseViewSet,
    ManagementViewSet, MunicipalityViewSet, NoticePeriodViewSet, RegulationViewSet, RelatedLeaseViewSet,
    SpecialProjectViewSet, StatisticalUseViewSet, SupportiveHousingViewSet)
from leasing.viewsets.lease_additional_views import (
    LeaseBillingPeriodsView, LeaseCopyAreasToContractView, LeaseCreateChargeViewSet,
    LeaseCreateCollectionLetterDocumentViewSet, LeasePreviewInvoicesForYearView, LeaseRentForPeriodView,
    LeaseSetInvoicingStateView, LeaseSetRentInfoCompletionStateView)
from leasing.viewsets.leasehold_transfer import LeaseholdTransferViewSet
from leasing.viewsets.rent import IndexViewSet
from leasing.viewsets.ui_data import UiDataViewSet
from leasing.viewsets.vat import VatViewSet
from users.views import UsersPermissions
from users.viewsets import UserViewSet

router = routers.DefaultRouter()
router.register(r'area_note', AreaNoteViewSet)
router.register(r'basis_of_rent', BasisOfRentViewSet)
router.register(r'collection_court_decision', CollectionCourtDecisionViewSet)
router.register(r'collection_letter', CollectionLetterViewSet)
router.register(r'collection_letter_template', CollectionLetterTemplateViewSet)
router.register(r'collection_note', CollectionNoteViewSet)
router.register(r'comment', CommentViewSet)
router.register(r'comment_topic', CommentTopicViewSet)
router.register(r'contact', ContactViewSet)
router.register(r'decision', DecisionViewSet)
router.register(r'district', DistrictViewSet)
router.register(r'financing', FinancingViewSet)
router.register(r'hitas', HitasViewSet)
router.register(r'index', IndexViewSet)
router.register(r'infill_development_compensation', InfillDevelopmentCompensationViewSet)
router.register(r'infill_development_compensation_attachment', InfillDevelopmentCompensationAttachmentViewSet)
router.register(r'inspection_attachment', InspectionAttachmentViewSet)
router.register(r'invoice', InvoiceViewSet)
router.register(r'invoice_note', InvoiceNoteViewSet)
router.register(r'invoice_row', InvoiceRowViewSet)
router.register(r'invoice_set', InvoiceSetViewSet)
router.register(r'intended_use', IntendedUseViewSet)
router.register(r'lease', LeaseViewSet, basename='lease')
router.register(r'lease_area_attachment', LeaseAreaAttachmentViewSet)
router.register(r'lease_create_charge', LeaseCreateChargeViewSet, basename='lease_create_charge')
router.register(r'lease_create_collection_letter', LeaseCreateCollectionLetterDocumentViewSet,
                basename='lease_create_collection_letter')
router.register(r'lease_type', LeaseTypeViewSet)
router.register(r'leasehold_transfer', LeaseholdTransferViewSet)
router.register(r'management', ManagementViewSet)
router.register(r'municipality', MunicipalityViewSet)
router.register(r'notice_period', NoticePeriodViewSet)
router.register(r'regulation', RegulationViewSet)
router.register(r'related_lease', RelatedLeaseViewSet)
router.register(r'special_project', SpecialProjectViewSet)
router.register(r'statistical_use', StatisticalUseViewSet)
router.register(r'supportive_housing', SupportiveHousingViewSet)
router.register(r'ui_data', UiDataViewSet, basename='ui_data')
router.register(r'user', UserViewSet)
router.register(r'vat', VatViewSet)

additional_api_paths = [
    path('auditlog/', AuditLogView.as_view(), name='auditlog'),
    path('contact_exists/', ContactExistsView.as_view(), name='contact-exists'),
    path('decision_copy_to_leases/', DecisionCopyToLeasesView.as_view(), name='decision-copy-to-leases'),
    path('invoice_calculate_penalty_interest/', InvoiceCalculatePenaltyInterestView.as_view(),
         name='invoice-calculate-penalty-interest'),
    path('invoice_credit/', InvoiceCreditView.as_view(), name='invoice-credit'),
    path('invoice_export_to_laske/', InvoiceExportToLaskeView.as_view(), name='invoice-export-to-laske'),
    path('invoice_row_credit/', InvoiceRowCreditView.as_view(), name='invoice-row-credit'),
    path('invoice_set_credit/', InvoiceSetCreditView.as_view(), name='invoice-set-credit'),
    path('lease_billing_periods/', LeaseBillingPeriodsView.as_view(), name='lease-billing-periods'),
    path('lease_copy_areas_to_contract/', LeaseCopyAreasToContractView.as_view(), name='lease-copy-areas-to-contract'),
    path('lease_preview_invoices_for_year/', LeasePreviewInvoicesForYearView.as_view(),
         name='lease-preview-invoices-for-year'),
    path('lease_rent_for_period/', LeaseRentForPeriodView.as_view(), name='lease-rent-for-period'),
    path('lease_set_invoicing_state/', LeaseSetInvoicingStateView.as_view(), name='lease-set-invoicing-state'),
    path('lease_set_rent_info_completion_state/', LeaseSetRentInfoCompletionStateView.as_view(),
         name='lease-set-rent-info-completion-state'),
    path('send_email/', SendEmailView.as_view(), name='send-email'),
    path('users_permissions/', UsersPermissions.as_view(), name='users-permissions'),
]

urlpatterns = [
    path('v1/', include(router.urls + additional_api_paths)),
    path('v1/batchrun/', include(batchrun_router.urls)),
    re_path(r'(?P<base_type>ktjki[ir])/tuloste/(?P<print_type>[\w/]+)/pdf', ktj_proxy),
    path('contract_file/<contract_id>/', CloudiaProxy.as_view()),
    path('contract_file/<contract_id>/<file_id>/', CloudiaProxy.as_view()),
    path('trade_register/<service>/<business_id>/', VirreProxy.as_view()),
    path('admin/', admin.site.urls),
    path('auth/', include(rest_framework.urls)),
    path('docs/', get_swagger_view(title='MVJ API')),
]

if settings.DEBUG and 'debug_toolbar' in settings.INSTALLED_APPS:
    import debug_toolbar

    urlpatterns = [path('__debug__/', include(debug_toolbar.urls)), ] + urlpatterns
