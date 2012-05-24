from django.core.cache import cache
from dateutil.parser import parse
from django.core.exceptions import ImproperlyConfigured
from django.template.defaultfilters import slugify
from django.views.generic.base import TemplateResponseMixin, View


class DateBasedMixin(object):
    date_field = None
    start_date = None
    end_date = None

    def get_date_field(self):
        if self.date_field is None:
            raise ImproperlyConfigured("To use 'DateBasedMixin', you must define a 'date_field' on %s." % self.__class__.__name__)

        return self.date_field

    def get_start_date(self):
        start_date = self.start_date

        if self.request.GET.get('start_date'):
            try:
                start_date = parse(self.request.GET.get('start_date'))
            except AttributeError:
                # TODO: Warning? Log? Silently fail?
                pass

        return start_date

    def get_end_date(self):
        end_date = self.end_date

        if self.request.GET.get('end_date'):
            try:
                end_date = parse(self.request.GET.get('end_date'))
            except AttributeError:
                # TODO: Warning? Log? Silently fail?
                pass

        return end_date

    def determine_range(self):
        return {
            'start_date': self.get_start_date(),
            'end_date': self.get_end_date(),
        }

    def get_data(self):
        queryset = self.get_queryset()
        valid_range = self.determine_range()
        date_field = self.get_date_field()
        filters = {}

        if valid_range.get('start_date') and valid_range.get('end_date'):
            filters['%s__range' % date_field] = (valid_range['start_date'], valid_range['end_date'])
        elif valid_range.get('start_date') and not valid_range.get('end_date'):
            filters['%s__gte' % date_field] = valid_range['start_date']
        elif valid_range.get('end_date') and not valid_range.get('start_date'):
            filters['%s__lt' % date_field] = valid_range['end_date']

        if filters:
            queryset = queryset.filter(**filters)

        return queryset


class GraphMixin(object):
    pass


class TableMixin(object):
    # This should be a three-tuple of (fieldname, HeadingTitle, should_be_aggregated)
    table_fields = None

    def get_table_fields(self):
        if self.table_fields is None:
            raise ImproperlyConfigured("To use 'TableMixin', you must define a 'table_fields' on %s." % self.__class__.__name__)

        return self.table_fields

    def get_fieldnames(self):
        return [field_info[0] for field_info in self.get_table_fields()]

    def get_headings(self):
        return [field_info[1] for field_info in self.get_table_fields()]

    def get_data(self):
        # FIXME: This kinda sucks, since ``Report.get_cached_data`` is expecting
        #        just the raw data, not includeing the headings/aggregation.
        return {
            'headings': self.get_headings(),
            'data': self.get_queryset().values_list(*self.get_fieldnames()),
        }


class Report(TemplateResponseMixin, View):
    title = None
    slug = None
    cache_timeout = 60
    cacke_key = None
    # FIXME: Need to handle templating better.

    def get_title(self):
        return self.title

    def get_slug(self):
        if self.slug is not None:
            return self.slug

        title = self.get_title()

        if isinstance(title, basestring):
            return slugify(title)

        raise ImproperlyConfigured("Neither '%s.title' nor '%s.slug' is defined." % (self.__class__.__name__, self.__class__.__name__))

    def get_queryset(self):
        raise ImproperlyConfigured("You must implement a 'get_queryset' method on %s." % self.__class__.__name__)

    def get_cache_timeout(self):
        return self.cache_timeout

    def cache_key(self):
        if self.cache_key is not None:
            return self.cache_key

        return slugify(self.get_title())

    def get_cached_data(self):
        cache_timeout = self.get_cache_timeout()

        if cache_timeout <= 0:
            return super(Report, self).get_data()

        # Wrap it in some caching, so that if the query is expensive
        # (and let's face it, most reports are), we're not slamming the DB.
        cache_key = self.cache_key()
        data = cache.get(cache_key)

        if data is None:
            # It's not there.
            data = super(Report, self).get_data()
            cache.set(cache_key, data, cache_timeout)

        return data

    def get_context_data(self, **kwargs):
        kwargs.update({
            'title': self.get_title(),
            'data': self.get_cached_data(),
        })
        return kwargs

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)
