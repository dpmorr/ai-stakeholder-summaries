"""Management command to generate a test summary."""

from django.core.management.base import BaseCommand
from summary.models import SummaryJob
from summary.services import get_summary_service


class Command(BaseCommand):
    """Generate a test summary for development."""

    help = 'Generate a test summary for development/testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--project-id',
            type=str,
            default='test-project',
            help='Project ID'
        )
        parser.add_argument(
            '--role',
            type=str,
            default='developer',
            choices=[
                'developer', 'contractor', 'architect', 'client',
                'project_manager', 'legal', 'finance', 'executive'
            ],
            help='Stakeholder role'
        )
        parser.add_argument(
            '--documents',
            type=str,
            nargs='+',
            default=['test-doc-1', 'test-doc-2'],
            help='Document IDs'
        )

    def handle(self, *args, **options):
        """Execute the command."""
        project_id = options['project_id']
        role = options['role']
        document_ids = options['documents']

        self.stdout.write(f'Creating summary job for project {project_id}...')

        # Create job
        job = SummaryJob.objects.create(
            id=f'test-{project_id}-{role}',
            project_id=project_id,
            stakeholder_role=role,
            document_ids=document_ids,
            focus_areas=['costs', 'timeline'],
            max_length=500
        )

        self.stdout.write(f'Job created: {job.id}')
        self.stdout.write('Generating summary...')

        # Generate summary
        try:
            service = get_summary_service()
            summary = service.generate_summary(job)

            self.stdout.write(self.style.SUCCESS(
                f'Summary generated successfully: {summary.id}'
            ))
            self.stdout.write(f'\nFull Summary:\n{summary.full_summary}')
            self.stdout.write(f'\nSections: {summary.sections.count()}')

            for section in summary.sections.all():
                self.stdout.write(f'\n  - {section.title}')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))
