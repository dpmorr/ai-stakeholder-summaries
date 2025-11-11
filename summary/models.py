"""Django models for summary generation service."""

from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.utils import timezone


class SummaryJob(models.Model):
    """Tracks summary generation jobs."""

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    STAKEHOLDER_ROLES = [
        ('developer', 'Developer'),
        ('contractor', 'Contractor'),
        ('architect', 'Architect'),
        ('client', 'Client'),
        ('project_manager', 'Project Manager'),
        ('legal', 'Legal'),
        ('finance', 'Finance'),
        ('executive', 'Executive'),
    ]

    id = models.CharField(max_length=100, primary_key=True)
    project_id = models.CharField(max_length=100, db_index=True)
    stakeholder_role = models.CharField(max_length=50, choices=STAKEHOLDER_ROLES)

    # Request parameters
    document_ids = ArrayField(
        models.CharField(max_length=100),
        default=list,
        help_text="List of document IDs to summarize"
    )
    focus_areas = ArrayField(
        models.CharField(max_length=100),
        default=list,
        blank=True,
        help_text="Specific focus areas (e.g., costs, timeline, risks)"
    )
    max_length = models.IntegerField(default=500)

    # Job status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', db_index=True)
    error_message = models.TextField(blank=True, null=True)

    # Metadata
    model_used = models.CharField(max_length=100, blank=True, null=True, help_text="LLM model used")
    tokens_used = models.IntegerField(null=True, blank=True)
    processing_time = models.FloatField(null=True, blank=True, help_text="Processing time in seconds")

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'summary_jobs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['project_id', '-created_at']),
            models.Index(fields=['stakeholder_role', '-created_at']),
            models.Index(fields=['status', '-created_at']),
        ]

    def __str__(self):
        return f"SummaryJob {self.id} - {self.stakeholder_role} - {self.status}"

    def mark_processing(self):
        """Mark job as processing."""
        self.status = 'processing'
        self.save(update_fields=['status', 'updated_at'])

    def mark_completed(self, model_used=None, tokens_used=None, processing_time=None):
        """Mark job as completed."""
        self.status = 'completed'
        self.completed_at = timezone.now()
        if model_used:
            self.model_used = model_used
        if tokens_used:
            self.tokens_used = tokens_used
        if processing_time:
            self.processing_time = processing_time
        self.save()

    def mark_failed(self, error_message):
        """Mark job as failed."""
        self.status = 'failed'
        self.error_message = error_message
        self.completed_at = timezone.now()
        self.save()


class GeneratedSummary(models.Model):
    """Stores generated summaries."""

    id = models.CharField(max_length=100, primary_key=True)
    job = models.OneToOneField(
        SummaryJob,
        on_delete=models.CASCADE,
        related_name='summary'
    )

    project_id = models.CharField(max_length=100, db_index=True)
    stakeholder_role = models.CharField(max_length=50, db_index=True)

    # Summary content
    full_summary = models.TextField(help_text="Complete summary text")

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'generated_summaries'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['project_id', '-created_at']),
            models.Index(fields=['stakeholder_role', '-created_at']),
        ]

    def __str__(self):
        return f"Summary {self.id} - {self.stakeholder_role}"


class SummarySection(models.Model):
    """Individual sections within a generated summary."""

    id = models.AutoField(primary_key=True)
    summary = models.ForeignKey(
        GeneratedSummary,
        on_delete=models.CASCADE,
        related_name='sections'
    )

    # Section content
    title = models.CharField(max_length=200)
    content = models.TextField()
    order = models.IntegerField(default=0, help_text="Display order")

    # Key points extracted from section
    key_points = ArrayField(
        models.TextField(),
        default=list,
        blank=True
    )

    # Evidence linking
    evidence_ids = ArrayField(
        models.CharField(max_length=100),
        default=list,
        blank=True,
        help_text="Document/extraction IDs supporting this section"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'summary_sections'
        ordering = ['summary', 'order']
        indexes = [
            models.Index(fields=['summary', 'order']),
        ]

    def __str__(self):
        return f"{self.summary.id} - {self.title}"


class DocumentContext(models.Model):
    """Stores document context used for summary generation."""

    id = models.AutoField(primary_key=True)
    job = models.ForeignKey(
        SummaryJob,
        on_delete=models.CASCADE,
        related_name='document_contexts'
    )

    document_id = models.CharField(max_length=100, db_index=True)

    # Context information
    document_type = models.CharField(max_length=50, blank=True)
    extracted_text = models.TextField(blank=True, help_text="Relevant extracted text")
    metadata = models.JSONField(default=dict, blank=True)

    # Relevance scoring
    relevance_score = models.FloatField(
        null=True,
        blank=True,
        help_text="Relevance score for this document (0-1)"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'document_contexts'
        indexes = [
            models.Index(fields=['job', 'document_id']),
            models.Index(fields=['document_id']),
        ]

    def __str__(self):
        return f"Context for {self.document_id} in job {self.job_id}"
