#!/usr/bin/env python
"""
Example client for the Summary Service API.

This script demonstrates how to:
1. Generate a summary
2. Check job status
3. Retrieve the completed summary
"""

import requests
import time
import json
from typing import Dict, Any, Optional


class SummaryServiceClient:
    """Client for interacting with the Summary Service API."""

    def __init__(self, base_url: str = "http://localhost:8002"):
        """
        Initialize the client.

        Args:
            base_url: Base URL of the summary service
        """
        self.base_url = base_url.rstrip('/')
        self.api_url = f"{self.base_url}/api"

    def generate_summary(
        self,
        document_ids: list[str],
        project_id: str,
        stakeholder_role: str,
        focus_areas: Optional[list[str]] = None,
        max_length: int = 500
    ) -> Dict[str, Any]:
        """
        Generate a new summary.

        Args:
            document_ids: List of document IDs to summarize
            project_id: Project identifier
            stakeholder_role: Target stakeholder role
            focus_areas: Optional focus areas
            max_length: Maximum summary length in words

        Returns:
            API response dictionary
        """
        url = f"{self.api_url}/summaries/generate/"

        payload = {
            "document_ids": document_ids,
            "project_id": project_id,
            "stakeholder_role": stakeholder_role,
            "focus_areas": focus_areas or [],
            "max_length": max_length
        }

        print(f"Generating summary for {stakeholder_role}...")
        print(f"Documents: {len(document_ids)}")
        print(f"Focus areas: {focus_areas or 'None'}")

        response = requests.post(url, json=payload)
        response.raise_for_status()

        return response.json()

    def get_job(self, job_id: str) -> Dict[str, Any]:
        """
        Get summary job details.

        Args:
            job_id: Job identifier

        Returns:
            Job details dictionary
        """
        url = f"{self.api_url}/summaries/{job_id}/"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()

    def get_summary_result(self, job_id: str) -> Dict[str, Any]:
        """
        Get the generated summary result.

        Args:
            job_id: Job identifier

        Returns:
            Summary result dictionary
        """
        url = f"{self.api_url}/summaries/{job_id}/result/"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()

    def wait_for_completion(
        self,
        job_id: str,
        timeout: int = 300,
        poll_interval: int = 2
    ) -> Dict[str, Any]:
        """
        Wait for a summary job to complete.

        Args:
            job_id: Job identifier
            timeout: Maximum wait time in seconds
            poll_interval: Seconds between status checks

        Returns:
            Completed summary result

        Raises:
            TimeoutError: If job doesn't complete in time
            RuntimeError: If job fails
        """
        start_time = time.time()

        while True:
            elapsed = time.time() - start_time
            if elapsed > timeout:
                raise TimeoutError(f"Job {job_id} did not complete in {timeout}s")

            try:
                result = self.get_summary_result(job_id)

                # Check status
                if result.get('status') == 'failed':
                    error = result.get('error', 'Unknown error')
                    raise RuntimeError(f"Job failed: {error}")

                elif result.get('status') in ['pending', 'processing']:
                    print(f"Job status: {result['status']} (elapsed: {elapsed:.1f}s)")
                    time.sleep(poll_interval)
                    continue

                else:
                    # Completed
                    print(f"Job completed in {elapsed:.1f}s")
                    return result

            except requests.HTTPError as e:
                if e.response.status_code == 202:
                    # Still processing
                    print(f"Processing... (elapsed: {elapsed:.1f}s)")
                    time.sleep(poll_interval)
                else:
                    raise

    def list_summaries(
        self,
        project_id: Optional[str] = None,
        stakeholder_role: Optional[str] = None,
        status: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List summaries with optional filters.

        Args:
            project_id: Filter by project
            stakeholder_role: Filter by role
            status: Filter by status

        Returns:
            Paginated list of summaries
        """
        url = f"{self.api_url}/summaries/"

        params = {}
        if project_id:
            params['project_id'] = project_id
        if stakeholder_role:
            params['stakeholder_role'] = stakeholder_role
        if status:
            params['status'] = status

        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()

    def list_project_summaries(
        self,
        project_id: str,
        stakeholder_role: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List all summaries for a project.

        Args:
            project_id: Project identifier
            stakeholder_role: Optional role filter

        Returns:
            List of summaries
        """
        url = f"{self.api_url}/summaries/by_project/{project_id}/"

        params = {}
        if stakeholder_role:
            params['stakeholder_role'] = stakeholder_role

        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()


def print_summary(summary: Dict[str, Any]):
    """Pretty print a summary result."""
    print("\n" + "=" * 80)
    print(f"SUMMARY: {summary['summary_id']}")
    print("=" * 80)
    print(f"Project: {summary['project_id']}")
    print(f"Role: {summary['stakeholder_role']}")
    print(f"Generated: {summary['generated_at']}")
    print("\n" + "-" * 80)

    # Print sections
    for section in summary.get('sections', []):
        print(f"\n## {section['title']}")
        print(section['content'])

        if section.get('key_points'):
            print("\nKey Points:")
            for point in section['key_points']:
                print(f"  - {point}")

        if section.get('evidence_ids'):
            print(f"\nEvidence: {', '.join(section['evidence_ids'])}")

    print("\n" + "-" * 80)
    print("\nFull Summary:")
    print(summary['full_summary'])
    print("\n" + "=" * 80 + "\n")


def example_1_simple_summary():
    """Example 1: Generate a simple developer summary."""
    print("\n### Example 1: Simple Developer Summary ###\n")

    client = SummaryServiceClient()

    # Generate summary
    response = client.generate_summary(
        document_ids=["doc-1", "doc-2", "doc-3"],
        project_id="example-project-1",
        stakeholder_role="developer",
        focus_areas=["technical", "quality"],
        max_length=500
    )

    job_id = response['job_id']
    print(f"Job ID: {job_id}")
    print(f"Status: {response['status']}")

    # If completed immediately, print result
    if response.get('summary'):
        print_summary(response['summary'])


def example_2_wait_for_completion():
    """Example 2: Generate and wait for completion."""
    print("\n### Example 2: Generate and Wait ###\n")

    client = SummaryServiceClient()

    # Generate summary
    response = client.generate_summary(
        document_ids=["doc-10", "doc-11"],
        project_id="example-project-2",
        stakeholder_role="executive",
        max_length=750
    )

    job_id = response['job_id']

    # Wait for completion
    try:
        result = client.wait_for_completion(job_id, timeout=60)
        print_summary(result)
    except TimeoutError as e:
        print(f"Timeout: {e}")
    except RuntimeError as e:
        print(f"Error: {e}")


def example_3_multiple_stakeholders():
    """Example 3: Generate summaries for multiple stakeholders."""
    print("\n### Example 3: Multiple Stakeholders ###\n")

    client = SummaryServiceClient()

    project_id = "example-project-3"
    document_ids = ["doc-20", "doc-21", "doc-22"]

    roles = ["developer", "client", "executive"]

    for role in roles:
        print(f"\nGenerating {role} summary...")

        response = client.generate_summary(
            document_ids=document_ids,
            project_id=project_id,
            stakeholder_role=role,
            max_length=500
        )

        print(f"Job ID: {response['job_id']}")
        print(f"Status: {response['status']}")


def example_4_list_summaries():
    """Example 4: List existing summaries."""
    print("\n### Example 4: List Summaries ###\n")

    client = SummaryServiceClient()

    # List all summaries
    summaries = client.list_summaries()
    print(f"Total summaries: {summaries['count']}")

    # List by project
    project_summaries = client.list_project_summaries("example-project-1")
    print(f"Project summaries: {project_summaries['count']}")

    # List by role
    dev_summaries = client.list_summaries(stakeholder_role="developer")
    print(f"Developer summaries: {dev_summaries['count']}")


def main():
    """Run all examples."""
    print("\n" + "=" * 80)
    print("Summary Service API Examples")
    print("=" * 80)

    try:
        # Run examples
        example_1_simple_summary()
        # example_2_wait_for_completion()
        # example_3_multiple_stakeholders()
        # example_4_list_summaries()

    except requests.exceptions.ConnectionError:
        print("\nError: Could not connect to summary service.")
        print("Make sure the service is running on http://localhost:8002")
    except requests.exceptions.HTTPError as e:
        print(f"\nHTTP Error: {e}")
        print(f"Response: {e.response.text}")
    except Exception as e:
        print(f"\nError: {e}")


if __name__ == "__main__":
    main()
