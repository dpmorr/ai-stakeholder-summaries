"""Django admin configuration for summary service."""

from django.contrib import admin
from .models import SummaryJob, GeneratedSummary, SummarySection, DocumentContext


@admin.register(SummaryJob)
class SummaryJobAdmin(admin.ModelAdmin):
    """Admin interface for SummaryJob."""

    list_display = [
        'id',
        'project_id',
        'stakeholder_role',
        'status',
        'document_count',
        'created_at',
        'completed_at',
    ]
    list_filter = [
        'status',
        'stakeholder_role',
        'created_at',
    ]
    search_fields = [
        'id',
        'project_id',
        'document_ids',
    ]
    readonly_fields = [
        'id',
        'created_at',
        'updated_at',
        'completed_at',
    ]
    fieldsets = (
        ('Job Information', {
            'fields': (
                'id',
                'project_id',
                'stakeholder_role',
                'status',
            )
        }),
        ('Request Parameters', {
            'fields': (
                'document_ids',
                'focus_areas',
                'max_length',
            )
        }),
        ('Processing Details', {
            'fields': (
                'model_used',
                'tokens_used',
                'processing_time',
                'error_message',
            )
        }),
        ('Timestamps', {
            'fields': (
                'created_at',
                'updated_at',
                'completed_at',
            )
        }),
    )

    def document_count(self, obj):
        """Return the number of documents."""
        return len(obj.document_ids)
    document_count.short_description = 'Documents'


class SummarySectionInline(admin.TabularInline):
    """Inline admin for summary sections."""

    model = SummarySection
    extra = 0
    fields = ['order', 'title', 'content', 'key_points']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(GeneratedSummary)
class GeneratedSummaryAdmin(admin.ModelAdmin):
    """Admin interface for GeneratedSummary."""

    list_display = [
        'id',
        'project_id',
        'stakeholder_role',
        'section_count',
        'created_at',
    ]
    list_filter = [
        'stakeholder_role',
        'created_at',
    ]
    search_fields = [
        'id',
        'project_id',
        'full_summary',
    ]
    readonly_fields = [
        'id',
        'job',
        'created_at',
        'updated_at',
    ]
    inlines = [SummarySectionInline]

    fieldsets = (
        ('Summary Information', {
            'fields': (
                'id',
                'job',
                'project_id',
                'stakeholder_role',
            )
        }),
        ('Content', {
            'fields': (
                'full_summary',
            )
        }),
        ('Timestamps', {
            'fields': (
                'created_at',
                'updated_at',
            )
        }),
    )

    def section_count(self, obj):
        """Return the number of sections."""
        return obj.sections.count()
    section_count.short_description = 'Sections'


@admin.register(SummarySection)
class SummarySectionAdmin(admin.ModelAdmin):
    """Admin interface for SummarySection."""

    list_display = [
        'id',
        'summary',
        'title',
        'order',
        'key_point_count',
    ]
    list_filter = [
        'created_at',
    ]
    search_fields = [
        'title',
        'content',
    ]
    readonly_fields = [
        'created_at',
        'updated_at',
    ]

    fieldsets = (
        ('Section Information', {
            'fields': (
                'summary',
                'title',
                'order',
            )
        }),
        ('Content', {
            'fields': (
                'content',
                'key_points',
                'evidence_ids',
            )
        }),
        ('Timestamps', {
            'fields': (
                'created_at',
                'updated_at',
            )
        }),
    )

    def key_point_count(self, obj):
        """Return the number of key points."""
        return len(obj.key_points)
    key_point_count.short_description = 'Key Points'


@admin.register(DocumentContext)
class DocumentContextAdmin(admin.ModelAdmin):
    """Admin interface for DocumentContext."""

    list_display = [
        'id',
        'job',
        'document_id',
        'document_type',
        'relevance_score',
        'created_at',
    ]
    list_filter = [
        'document_type',
        'created_at',
    ]
    search_fields = [
        'document_id',
        'extracted_text',
    ]
    readonly_fields = [
        'created_at',
    ]

    fieldsets = (
        ('Context Information', {
            'fields': (
                'job',
                'document_id',
                'document_type',
                'relevance_score',
            )
        }),
        ('Content', {
            'fields': (
                'extracted_text',
                'metadata',
            )
        }),
        ('Timestamps', {
            'fields': (
                'created_at',
            )
        }),
    )
