from rest_framework.routers import DefaultRouter

from . import viewsets

router = DefaultRouter()

router.register('job', viewsets.JobViewSet)
router.register('job_run', viewsets.JobRunViewSet)
router.register('job_run_log_entry', viewsets.JobRunLogEntryViewSet)
