from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _


class DashboardReport(models.Model):
    user = models.ForeignKey(User, related_name='dashboards', blank=True, null=True)
    dashboard_slug = models.SlugField()
    report_slug = models.SlugField()
    order = models.PositiveIntegerField(default=0)
    created = models.DateTimeField(default=timezone.now)
    updated = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = _('Dashboard Report')
        verbose_name_plural = _('Dashboard Reports')
        ordering = ['dashboard_slug', 'report_slug', 'user']

    def __unicode__(self):
        return self.slug

    def save(self, *args, **kwargs):
        self.updated = timezone.now()
        return super(DashboardReport, self).save(*args, **kwargs)
