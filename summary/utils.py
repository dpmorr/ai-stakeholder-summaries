"""Utility functions for summary service."""

import uuid
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


def generate_job_id() -> str:
    """Generate a unique job ID."""
    return str(uuid.uuid4())


def generate_summary_id(job_id: str) -> str:
    """Generate a summary ID from a job ID."""
    return f"sum_{job_id}"


def validate_document_ids(document_ids: List[str]) -> bool:
    """
    Validate document IDs.

    Args:
        document_ids: List of document IDs

    Returns:
        True if valid, False otherwise
    """
    if not document_ids:
        return False

    if len(document_ids) > 50:  # Max documents
        return False

    return all(isinstance(doc_id, str) and doc_id for doc_id in document_ids)


def calculate_relevance_score(
    document_content: str,
    focus_areas: List[str],
    stakeholder_role: str
) -> float:
    """
    Calculate relevance score for a document based on focus areas and role.

    Args:
        document_content: Document text content
        focus_areas: List of focus areas
        stakeholder_role: Stakeholder role

    Returns:
        Relevance score between 0 and 1
    """
    # Simple keyword-based relevance (in production, use embeddings)
    score = 0.5  # Base score

    # Check for focus area keywords
    content_lower = document_content.lower()
    for area in focus_areas:
        if area.lower() in content_lower:
            score += 0.1

    # Role-specific keywords
    role_keywords = {
        'developer': ['technical', 'specification', 'code', 'quality'],
        'contractor': ['scope', 'timeline', 'resource', 'deliverable'],
        'architect': ['design', 'specification', 'code', 'compliance'],
        'client': ['progress', 'budget', 'timeline', 'quality'],
        'project_manager': ['status', 'risk', 'resource', 'stakeholder'],
        'legal': ['contract', 'compliance', 'claim', 'dispute'],
        'finance': ['cost', 'budget', 'payment', 'forecast'],
        'executive': ['status', 'risk', 'financial', 'decision'],
    }

    keywords = role_keywords.get(stakeholder_role, [])
    for keyword in keywords:
        if keyword in content_lower:
            score += 0.05

    return min(score, 1.0)


def estimate_tokens(text: str) -> int:
    """
    Estimate the number of tokens in a text.

    Args:
        text: Input text

    Returns:
        Estimated token count
    """
    # Rough estimation: 1 token ≈ 4 characters for English
    return len(text) // 4


def truncate_text(text: str, max_tokens: int = 8000) -> str:
    """
    Truncate text to fit within token limit.

    Args:
        text: Input text
        max_tokens: Maximum number of tokens

    Returns:
        Truncated text
    """
    estimated_tokens = estimate_tokens(text)

    if estimated_tokens <= max_tokens:
        return text

    # Calculate character limit
    char_limit = max_tokens * 4

    # Truncate and add ellipsis
    return text[:char_limit] + "..."


def format_summary_sections(sections: List[Dict[str, Any]]) -> str:
    """
    Format summary sections into a readable text.

    Args:
        sections: List of section dictionaries

    Returns:
        Formatted text
    """
    formatted_parts = []

    for section in sections:
        formatted_parts.append(f"## {section['title']}\n")
        formatted_parts.append(f"{section['content']}\n")

        if section.get('key_points'):
            formatted_parts.append("\n**Key Points:**\n")
            for point in section['key_points']:
                formatted_parts.append(f"- {point}\n")

        formatted_parts.append("\n")

    return "\n".join(formatted_parts)


def extract_key_metrics(content: str, stakeholder_role: str) -> Dict[str, Any]:
    """
    Extract key metrics from content based on stakeholder role.

    Args:
        content: Document content
        stakeholder_role: Stakeholder role

    Returns:
        Dictionary of extracted metrics
    """
    # This would use NLP/LLM in production
    # For now, return placeholders
    metrics = {
        'document_length': len(content),
        'word_count': len(content.split()),
    }

    # Role-specific metrics
    if stakeholder_role in ['finance', 'executive']:
        metrics['has_financial_data'] = any(
            word in content.lower()
            for word in ['budget', 'cost', 'dollar', '$', 'payment']
        )

    if stakeholder_role in ['project_manager', 'contractor']:
        metrics['has_timeline_data'] = any(
            word in content.lower()
            for word in ['timeline', 'schedule', 'deadline', 'milestone', 'date']
        )

    if stakeholder_role in ['legal', 'executive']:
        metrics['has_risk_data'] = any(
            word in content.lower()
            for word in ['risk', 'issue', 'problem', 'concern', 'claim']
        )

    return metrics


def merge_summaries(summaries: List[str], max_length: int = 500) -> str:
    """
    Merge multiple summaries into one, respecting length limit.

    Args:
        summaries: List of summary texts
        max_length: Maximum word count

    Returns:
        Merged summary
    """
    if not summaries:
        return ""

    if len(summaries) == 1:
        return summaries[0]

    # Join summaries
    combined = " ".join(summaries)

    # Truncate to max length
    words = combined.split()
    if len(words) <= max_length:
        return combined

    truncated_words = words[:max_length]
    return " ".join(truncated_words) + "..."


def sanitize_input(text: str) -> str:
    """
    Sanitize user input text.

    Args:
        text: Input text

    Returns:
        Sanitized text
    """
    # Remove null bytes
    text = text.replace('\x00', '')

    # Strip excessive whitespace
    text = ' '.join(text.split())

    return text.strip()
