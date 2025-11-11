"""Tests for summary generation service."""

from django.test import TestCase
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from unittest.mock import patch, MagicMock

from .models import SummaryJob, GeneratedSummary, SummarySection
from .services import SummaryGenerationService


class SummaryJobModelTest(TestCase):
    """Test SummaryJob model."""

    def test_create_summary_job(self):
        """Test creating a summary job."""
        job = SummaryJob.objects.create(
            id='test-job-1',
            project_id='project-1',
            stakeholder_role='developer',
            document_ids=['doc1', 'doc2'],
            focus_areas=['costs', 'timeline'],
            max_length=500
        )

        self.assertEqual(job.status, 'pending')
        self.assertEqual(len(job.document_ids), 2)
        self.assertEqual(len(job.focus_areas), 2)

    def test_mark_processing(self):
        """Test marking job as processing."""
        job = SummaryJob.objects.create(
            id='test-job-2',
            project_id='project-1',
            stakeholder_role='developer',
            document_ids=['doc1']
        )
        job.mark_processing()

        job.refresh_from_db()
        self.assertEqual(job.status, 'processing')

    def test_mark_completed(self):
        """Test marking job as completed."""
        job = SummaryJob.objects.create(
            id='test-job-3',
            project_id='project-1',
            stakeholder_role='developer',
            document_ids=['doc1']
        )
        job.mark_completed(model_used='gpt-4', tokens_used=1000, processing_time=5.5)

        job.refresh_from_db()
        self.assertEqual(job.status, 'completed')
        self.assertEqual(job.model_used, 'gpt-4')
        self.assertEqual(job.tokens_used, 1000)
        self.assertEqual(job.processing_time, 5.5)
        self.assertIsNotNone(job.completed_at)

    def test_mark_failed(self):
        """Test marking job as failed."""
        job = SummaryJob.objects.create(
            id='test-job-4',
            project_id='project-1',
            stakeholder_role='developer',
            document_ids=['doc1']
        )
        job.mark_failed('Test error message')

        job.refresh_from_db()
        self.assertEqual(job.status, 'failed')
        self.assertEqual(job.error_message, 'Test error message')
        self.assertIsNotNone(job.completed_at)


class GeneratedSummaryModelTest(TestCase):
    """Test GeneratedSummary model."""

    def test_create_summary_with_sections(self):
        """Test creating a summary with sections."""
        job = SummaryJob.objects.create(
            id='test-job-5',
            project_id='project-1',
            stakeholder_role='developer',
            document_ids=['doc1']
        )

        summary = GeneratedSummary.objects.create(
            id='sum_test-job-5',
            job=job,
            project_id='project-1',
            stakeholder_role='developer',
            full_summary='This is a test summary.'
        )

        section = SummarySection.objects.create(
            summary=summary,
            title='Test Section',
            content='Test content',
            order=0,
            key_points=['Point 1', 'Point 2'],
            evidence_ids=['doc1']
        )

        self.assertEqual(summary.sections.count(), 1)
        self.assertEqual(section.title, 'Test Section')
        self.assertEqual(len(section.key_points), 2)


class SummaryAPITest(APITestCase):
    """Test summary API endpoints."""

    def setUp(self):
        """Set up test client."""
        self.client = APIClient()

    @patch('summary.services.SummaryGenerationService.generate_summary')
    def test_generate_summary(self, mock_generate):
        """Test summary generation endpoint."""
        # Mock the service response
        job = SummaryJob.objects.create(
            id='test-job-6',
            project_id='project-1',
            stakeholder_role='developer',
            document_ids=['doc1', 'doc2']
        )
        summary = GeneratedSummary.objects.create(
            id='sum_test-job-6',
            job=job,
            project_id='project-1',
            stakeholder_role='developer',
            full_summary='Generated summary'
        )
        mock_generate.return_value = summary

        # Make request
        response = self.client.post('/api/summaries/generate/', {
            'document_ids': ['doc1', 'doc2'],
            'project_id': 'project-1',
            'stakeholder_role': 'developer',
            'focus_areas': ['costs'],
            'max_length': 500
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('job_id', response.data)
        self.assertEqual(response.data['status'], 'completed')

    def test_generate_summary_validation(self):
        """Test validation on generate endpoint."""
        response = self.client.post('/api/summaries/generate/', {
            'document_ids': [],  # Empty list should fail
            'project_id': 'project-1',
            'stakeholder_role': 'developer'
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_summary_job(self):
        """Test getting a summary job."""
        job = SummaryJob.objects.create(
            id='test-job-7',
            project_id='project-1',
            stakeholder_role='developer',
            document_ids=['doc1']
        )

        response = self.client.get(f'/api/summaries/{job.id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], job.id)
        self.assertEqual(response.data['status'], 'pending')

    def test_get_summary_result_pending(self):
        """Test getting result for pending job."""
        job = SummaryJob.objects.create(
            id='test-job-8',
            project_id='project-1',
            stakeholder_role='developer',
            document_ids=['doc1'],
            status='pending'
        )

        response = self.client.get(f'/api/summaries/{job.id}/result/')

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertEqual(response.data['status'], 'pending')

    def test_get_summary_result_completed(self):
        """Test getting result for completed job."""
        job = SummaryJob.objects.create(
            id='test-job-9',
            project_id='project-1',
            stakeholder_role='developer',
            document_ids=['doc1'],
            status='completed'
        )
        summary = GeneratedSummary.objects.create(
            id='sum_test-job-9',
            job=job,
            project_id='project-1',
            stakeholder_role='developer',
            full_summary='Generated summary'
        )

        response = self.client.get(f'/api/summaries/{job.id}/result/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['summary_id'], summary.id)
        self.assertIn('full_summary', response.data)

    def test_list_summaries_by_project(self):
        """Test listing summaries by project."""
        job1 = SummaryJob.objects.create(
            id='test-job-10',
            project_id='project-1',
            stakeholder_role='developer',
            document_ids=['doc1']
        )
        job2 = SummaryJob.objects.create(
            id='test-job-11',
            project_id='project-1',
            stakeholder_role='client',
            document_ids=['doc1']
        )
        job3 = SummaryJob.objects.create(
            id='test-job-12',
            project_id='project-2',
            stakeholder_role='developer',
            document_ids=['doc1']
        )

        response = self.client.get('/api/summaries/by_project/project-1/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)


class SummaryGenerationServiceTest(TestCase):
    """Test SummaryGenerationService."""

    def setUp(self):
        """Set up test service."""
        self.service = SummaryGenerationService()

    def test_stakeholder_prompts_defined(self):
        """Test that all stakeholder roles have prompts."""
        roles = [
            'developer', 'contractor', 'architect', 'client',
            'project_manager', 'legal', 'finance', 'executive'
        ]

        for role in roles:
            self.assertIn(role, self.service.STAKEHOLDER_PROMPTS)
            config = self.service.STAKEHOLDER_PROMPTS[role]
            self.assertIn('focus', config)
            self.assertIn('sections', config)

    @patch('summary.services.ChatOpenAI')
    def test_service_initialization(self, mock_llm):
        """Test service initialization."""
        service = SummaryGenerationService()
        self.assertIsNotNone(service.llm)
        self.assertIsNotNone(service.text_splitter)
