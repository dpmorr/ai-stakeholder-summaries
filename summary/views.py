"""DRF views for summary generation API."""

import uuid
import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from .models import SummaryJob, GeneratedSummary
from .serializers import (
    SummaryRequestSerializer,
    SummaryJobSerializer,
    GeneratedSummarySerializer,
    SummaryResponseSerializer
)
from .services import get_summary_service

logger = logging.getLogger(__name__)


class SummaryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for summary generation and retrieval.

    Endpoints:
    - POST /api/summaries/generate/ - Generate a new summary
    - GET /api/summaries/ - List all summary jobs
    - GET /api/summaries/{id}/ - Get a specific summary job
    - GET /api/summaries/{id}/result/ - Get the generated summary
    - GET /api/summaries/by_project/{project_id}/ - List summaries for a project
    """

    queryset = SummaryJob.objects.all()
    serializer_class = SummaryJobSerializer

    def get_queryset(self):
        """Filter queryset based on query parameters."""
        queryset = SummaryJob.objects.all().select_related('summary')

        # Filter by project
        project_id = self.request.query_params.get('project_id')
        if project_id:
            queryset = queryset.filter(project_id=project_id)

        # Filter by stakeholder role
        stakeholder_role = self.request.query_params.get('stakeholder_role')
        if stakeholder_role:
            queryset = queryset.filter(stakeholder_role=stakeholder_role)

        # Filter by status
        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status)

        return queryset

    @action(detail=False, methods=['post'])
    def generate(self, request):
        """
        Generate a new stakeholder-specific summary.

        Request Body:
        {
            "document_ids": ["doc1", "doc2"],
            "project_id": "project123",
            "stakeholder_role": "developer",
            "focus_areas": ["costs", "timeline"],  # optional
            "max_length": 500  # optional, defaults to 500
        }

        Returns:
        {
            "job_id": "uuid",
            "status": "processing",
            "message": "Summary generation started"
        }
        """
        serializer = SummaryRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Create job
        job_id = str(uuid.uuid4())
        job = SummaryJob.objects.create(
            id=job_id,
            project_id=serializer.validated_data['project_id'],
            stakeholder_role=serializer.validated_data['stakeholder_role'],
            document_ids=serializer.validated_data['document_ids'],
            focus_areas=serializer.validated_data.get('focus_areas', []),
            max_length=serializer.validated_data.get('max_length', 500),
            status='pending'
        )

        logger.info(f"Created summary job {job_id} for project {job.project_id}")

        # Generate summary asynchronously (in production, use Celery)
        # For now, generate synchronously
        try:
            service = get_summary_service()
            summary = service.generate_summary(job)

            return Response({
                'job_id': job.id,
                'status': 'completed',
                'message': 'Summary generated successfully',
                'summary': GeneratedSummarySerializer(summary).data
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Summary generation failed: {str(e)}", exc_info=True)
            return Response({
                'job_id': job.id,
                'status': 'failed',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'])
    def result(self, request, pk=None):
        """
        Get the generated summary for a completed job.

        Returns:
        {
            "summary_id": "sum_uuid",
            "project_id": "project123",
            "stakeholder_role": "developer",
            "sections": [...],
            "full_summary": "...",
            "generated_at": "2024-01-01T00:00:00Z"
        }
        """
        job = self.get_object()

        if job.status == 'pending':
            return Response({
                'status': 'pending',
                'message': 'Summary generation is pending'
            }, status=status.HTTP_202_ACCEPTED)

        elif job.status == 'processing':
            return Response({
                'status': 'processing',
                'message': 'Summary is being generated'
            }, status=status.HTTP_202_ACCEPTED)

        elif job.status == 'failed':
            return Response({
                'status': 'failed',
                'error': job.error_message
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        elif job.status == 'completed':
            try:
                summary = job.summary
                serializer = GeneratedSummarySerializer(summary)

                # Transform to match shared schema format
                response_data = {
                    'summary_id': summary.id,
                    'project_id': summary.project_id,
                    'stakeholder_role': summary.stakeholder_role,
                    'sections': serializer.data['sections'],
                    'full_summary': summary.full_summary,
                    'generated_at': summary.created_at
                }

                return Response(response_data, status=status.HTTP_200_OK)

            except GeneratedSummary.DoesNotExist:
                return Response({
                    'status': 'error',
                    'message': 'Summary not found for completed job'
                }, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['get'], url_path='by_project/(?P<project_id>[^/.]+)')
    def by_project(self, request, project_id=None):
        """
        List all summaries for a specific project.

        Query params:
        - stakeholder_role: Filter by role
        - status: Filter by status
        """
        queryset = self.get_queryset().filter(project_id=project_id)

        # Apply additional filters
        stakeholder_role = request.query_params.get('stakeholder_role')
        if stakeholder_role:
            queryset = queryset.filter(stakeholder_role=stakeholder_role)

        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        # Paginate
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='by_role/(?P<role>[^/.]+)')
    def by_role(self, request, role=None):
        """
        List all summaries for a specific stakeholder role.

        Query params:
        - project_id: Filter by project
        - status: Filter by status
        """
        queryset = self.get_queryset().filter(stakeholder_role=role)

        # Apply additional filters
        project_id = request.query_params.get('project_id')
        if project_id:
            queryset = queryset.filter(project_id=project_id)

        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        # Paginate
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class GeneratedSummaryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing generated summaries directly.

    Endpoints:
    - GET /api/generated-summaries/ - List all generated summaries
    - GET /api/generated-summaries/{id}/ - Get a specific summary
    """

    queryset = GeneratedSummary.objects.all().prefetch_related('sections')
    serializer_class = GeneratedSummarySerializer

    def get_queryset(self):
        """Filter queryset based on query parameters."""
        queryset = GeneratedSummary.objects.all().prefetch_related('sections')

        # Filter by project
        project_id = self.request.query_params.get('project_id')
        if project_id:
            queryset = queryset.filter(project_id=project_id)

        # Filter by stakeholder role
        stakeholder_role = self.request.query_params.get('stakeholder_role')
        if stakeholder_role:
            queryset = queryset.filter(stakeholder_role=stakeholder_role)

        return queryset
