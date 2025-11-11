"""DRF serializers for summary service."""

from rest_framework import serializers
from .models import SummaryJob, GeneratedSummary, SummarySection, DocumentContext


class SummaryRequestSerializer(serializers.Serializer):
    """Serializer for summary generation requests."""

    document_ids = serializers.ListField(
        child=serializers.CharField(max_length=100),
        min_length=1,
        help_text="List of document IDs to summarize"
    )
    project_id = serializers.CharField(max_length=100)
    stakeholder_role = serializers.ChoiceField(
        choices=[
            'developer',
            'contractor',
            'architect',
            'client',
            'project_manager',
            'legal',
            'finance',
            'executive'
        ]
    )
    focus_areas = serializers.ListField(
        child=serializers.CharField(max_length=100),
        required=False,
        default=list,
        help_text="Specific focus areas (e.g., costs, timeline, risks)"
    )
    max_length = serializers.IntegerField(
        default=500,
        min_value=100,
        max_value=2000,
        help_text="Maximum length of summary in words"
    )


class SummarySectionSerializer(serializers.ModelSerializer):
    """Serializer for summary sections."""

    class Meta:
        model = SummarySection
        fields = [
            'id',
            'title',
            'content',
            'order',
            'key_points',
            'evidence_ids',
        ]


class GeneratedSummarySerializer(serializers.ModelSerializer):
    """Serializer for generated summaries."""

    sections = SummarySectionSerializer(many=True, read_only=True)

    class Meta:
        model = GeneratedSummary
        fields = [
            'id',
            'project_id',
            'stakeholder_role',
            'full_summary',
            'sections',
            'created_at',
        ]


class SummaryJobSerializer(serializers.ModelSerializer):
    """Serializer for summary jobs."""

    summary = GeneratedSummarySerializer(read_only=True)

    class Meta:
        model = SummaryJob
        fields = [
            'id',
            'project_id',
            'stakeholder_role',
            'document_ids',
            'focus_areas',
            'max_length',
            'status',
            'error_message',
            'model_used',
            'tokens_used',
            'processing_time',
            'created_at',
            'updated_at',
            'completed_at',
            'summary',
        ]
        read_only_fields = [
            'id',
            'status',
            'error_message',
            'model_used',
            'tokens_used',
            'processing_time',
            'created_at',
            'updated_at',
            'completed_at',
        ]


class DocumentContextSerializer(serializers.ModelSerializer):
    """Serializer for document context."""

    class Meta:
        model = DocumentContext
        fields = [
            'id',
            'document_id',
            'document_type',
            'extracted_text',
            'metadata',
            'relevance_score',
            'created_at',
        ]


class SummaryResponseSerializer(serializers.Serializer):
    """Serializer for API summary response (matches shared schema)."""

    summary_id = serializers.CharField()
    project_id = serializers.CharField()
    stakeholder_role = serializers.CharField()
    sections = SummarySectionSerializer(many=True)
    full_summary = serializers.CharField()
    generated_at = serializers.DateTimeField()
