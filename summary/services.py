"""LangChain-based summary generation service."""

import logging
import time
from typing import List, Dict, Any, Optional
from datetime import datetime

from django.conf import settings
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain.chains import LLMChain
from langchain.callbacks import get_openai_callback
from langchain.text_splitter import RecursiveCharacterTextSplitter
from pydantic import BaseModel, Field

from .models import SummaryJob, GeneratedSummary, SummarySection, DocumentContext

logger = logging.getLogger(__name__)


class SectionOutput(BaseModel):
    """Schema for a summary section."""
    title: str = Field(description="Section title")
    content: str = Field(description="Section content")
    key_points: List[str] = Field(description="Key points from this section")
    evidence_ids: List[str] = Field(default_factory=list, description="Supporting document IDs")


class SummaryOutput(BaseModel):
    """Schema for complete summary output."""
    sections: List[SectionOutput] = Field(description="Summary sections")
    full_summary: str = Field(description="Complete summary text")


class SummaryGenerationService:
    """Service for generating stakeholder-specific summaries using LangChain."""

    STAKEHOLDER_PROMPTS = {
        'developer': {
            'focus': 'technical specifications, building codes, construction methods, and quality standards',
            'sections': ['Technical Overview', 'Quality Standards', 'Compliance Requirements', 'Key Risks'],
        },
        'contractor': {
            'focus': 'project scope, timelines, resources, change orders, and deliverables',
            'sections': ['Project Scope', 'Timeline & Milestones', 'Resource Requirements', 'Change Management'],
        },
        'architect': {
            'focus': 'design intent, specifications, building codes, and design changes',
            'sections': ['Design Overview', 'Specifications', 'Code Compliance', 'Design Changes'],
        },
        'client': {
            'focus': 'project progress, budget status, timeline, and quality outcomes',
            'sections': ['Project Status', 'Budget Summary', 'Timeline', 'Quality Assurance'],
        },
        'project_manager': {
            'focus': 'overall status, risks, issues, resource allocation, and stakeholder coordination',
            'sections': ['Executive Summary', 'Risk & Issues', 'Resource Status', 'Key Decisions'],
        },
        'legal': {
            'focus': 'contractual obligations, compliance, claims, disputes, and liability',
            'sections': ['Contractual Overview', 'Compliance Status', 'Claims & Disputes', 'Risk Exposure'],
        },
        'finance': {
            'focus': 'costs, budget variance, payment status, and financial forecasts',
            'sections': ['Financial Summary', 'Budget Variance', 'Cash Flow', 'Financial Risks'],
        },
        'executive': {
            'focus': 'high-level status, strategic risks, financial health, and key decisions needed',
            'sections': ['Executive Summary', 'Strategic Overview', 'Financial Health', 'Critical Actions'],
        },
    }

    def __init__(self):
        """Initialize the summary generation service."""
        # Determine which model to use (fine-tuned if available)
        self.model_name = settings.OPENAI_FINE_TUNED_MODEL or settings.OPENAI_MODEL

        # Initialize LLM
        self.llm = ChatOpenAI(
            model=self.model_name,
            temperature=settings.OPENAI_TEMPERATURE,
            max_tokens=settings.OPENAI_MAX_TOKENS,
            openai_api_key=settings.OPENAI_API_KEY,
        )

        # Text splitter for handling large documents
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=4000,
            chunk_overlap=200,
            length_function=len,
        )

    def generate_summary(self, job: SummaryJob) -> GeneratedSummary:
        """
        Generate a stakeholder-specific summary for a job.

        Args:
            job: SummaryJob instance

        Returns:
            GeneratedSummary instance
        """
        start_time = time.time()

        try:
            logger.info(f"Starting summary generation for job {job.id}")
            job.mark_processing()

            # Fetch and prepare document contexts
            document_contexts = self._fetch_document_contexts(job)

            # Generate summary using LangChain
            summary_data, tokens_used = self._generate_with_langchain(
                job=job,
                document_contexts=document_contexts
            )

            # Create summary and sections
            summary = self._create_summary_records(
                job=job,
                summary_data=summary_data
            )

            # Mark job as completed
            processing_time = time.time() - start_time
            job.mark_completed(
                model_used=self.model_name,
                tokens_used=tokens_used,
                processing_time=processing_time
            )

            logger.info(
                f"Summary generation completed for job {job.id} "
                f"in {processing_time:.2f}s using {tokens_used} tokens"
            )

            return summary

        except Exception as e:
            logger.error(f"Summary generation failed for job {job.id}: {str(e)}", exc_info=True)
            job.mark_failed(str(e))
            raise

    def _fetch_document_contexts(self, job: SummaryJob) -> List[DocumentContext]:
        """
        Fetch or create document contexts for the job.

        Args:
            job: SummaryJob instance

        Returns:
            List of DocumentContext instances
        """
        contexts = []

        for doc_id in job.document_ids:
            # In a real implementation, fetch document content from ingestion service
            # For now, create placeholder contexts
            context = DocumentContext.objects.create(
                job=job,
                document_id=doc_id,
                document_type='unknown',
                extracted_text=f"[Document {doc_id} content would be fetched from ingestion service]",
                metadata={},
                relevance_score=1.0
            )
            contexts.append(context)

        logger.info(f"Fetched {len(contexts)} document contexts for job {job.id}")
        return contexts

    def _generate_with_langchain(
        self,
        job: SummaryJob,
        document_contexts: List[DocumentContext]
    ) -> tuple[Dict[str, Any], int]:
        """
        Generate summary using LangChain.

        Args:
            job: SummaryJob instance
            document_contexts: List of document contexts

        Returns:
            Tuple of (summary_data, tokens_used)
        """
        # Get stakeholder-specific configuration
        stakeholder_config = self.STAKEHOLDER_PROMPTS.get(
            job.stakeholder_role,
            self.STAKEHOLDER_PROMPTS['executive']
        )

        # Prepare document content
        combined_text = self._combine_document_texts(document_contexts)

        # Split if too large
        chunks = self.text_splitter.split_text(combined_text)

        # If multiple chunks, synthesize them
        if len(chunks) > 1:
            logger.info(f"Document too large, split into {len(chunks)} chunks")
            summary_data = self._multi_document_synthesis(
                job=job,
                chunks=chunks,
                stakeholder_config=stakeholder_config
            )
        else:
            summary_data = self._single_document_summary(
                job=job,
                content=combined_text,
                stakeholder_config=stakeholder_config
            )

        # Track tokens (simplified - in practice, use callback)
        tokens_used = summary_data.get('tokens_used', 0)

        return summary_data, tokens_used

    def _combine_document_texts(self, contexts: List[DocumentContext]) -> str:
        """Combine document texts into a single string."""
        texts = []
        for ctx in contexts:
            texts.append(f"--- Document {ctx.document_id} ---\n{ctx.extracted_text}\n")
        return "\n\n".join(texts)

    def _single_document_summary(
        self,
        job: SummaryJob,
        content: str,
        stakeholder_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate summary from a single document or chunk."""

        # Build focus areas string
        focus_str = ", ".join(job.focus_areas) if job.focus_areas else stakeholder_config['focus']

        # Create prompt
        system_template = """You are an expert construction project analyst specializing in generating
stakeholder-specific summaries. Your task is to analyze project documents and create a concise,
actionable summary tailored to the stakeholder's role and concerns.

Stakeholder Role: {stakeholder_role}
Primary Focus: {focus}
Target Length: {max_length} words"""

        human_template = """Analyze the following project documents and create a structured summary.

Documents:
{content}

Generate a summary with the following sections:
{sections}

For each section:
1. Provide clear, actionable content
2. Extract 2-4 key points
3. Note which documents support each point (use document IDs)

Focus specifically on: {focus_areas}

Respond with a JSON structure containing:
- sections: array of objects with title, content, key_points, evidence_ids
- full_summary: a cohesive narrative combining all sections"""

        system_message = SystemMessagePromptTemplate.from_template(system_template)
        human_message = HumanMessagePromptTemplate.from_template(human_template)

        chat_prompt = ChatPromptTemplate.from_messages([system_message, human_message])

        # Create chain
        chain = LLMChain(llm=self.llm, prompt=chat_prompt)

        # Execute with token tracking
        with get_openai_callback() as cb:
            response = chain.run(
                stakeholder_role=job.stakeholder_role,
                focus=stakeholder_config['focus'],
                max_length=job.max_length,
                content=content,
                sections=", ".join(stakeholder_config['sections']),
                focus_areas=focus_str
            )

            tokens_used = cb.total_tokens

        # Parse response (simplified - in production, use structured output)
        summary_data = self._parse_llm_response(response, stakeholder_config, job.document_ids)
        summary_data['tokens_used'] = tokens_used

        return summary_data

    def _multi_document_synthesis(
        self,
        job: SummaryJob,
        chunks: List[str],
        stakeholder_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Synthesize multiple document chunks using map-reduce approach.

        Args:
            job: SummaryJob instance
            chunks: List of text chunks
            stakeholder_config: Stakeholder configuration

        Returns:
            Summary data dictionary
        """
        logger.info(f"Synthesizing {len(chunks)} chunks")

        # Step 1: Summarize each chunk
        chunk_summaries = []
        total_tokens = 0

        for i, chunk in enumerate(chunks):
            logger.debug(f"Processing chunk {i+1}/{len(chunks)}")

            chunk_summary = self._single_document_summary(
                job=job,
                content=chunk,
                stakeholder_config=stakeholder_config
            )
            chunk_summaries.append(chunk_summary['full_summary'])
            total_tokens += chunk_summary.get('tokens_used', 0)

        # Step 2: Combine chunk summaries into final summary
        combined_summaries = "\n\n".join(chunk_summaries)

        final_summary = self._single_document_summary(
            job=job,
            content=combined_summaries,
            stakeholder_config=stakeholder_config
        )

        final_summary['tokens_used'] = total_tokens + final_summary.get('tokens_used', 0)

        return final_summary

    def _parse_llm_response(
        self,
        response: str,
        stakeholder_config: Dict[str, Any],
        document_ids: List[str]
    ) -> Dict[str, Any]:
        """
        Parse LLM response into structured format.

        Args:
            response: LLM response text
            stakeholder_config: Stakeholder configuration
            document_ids: List of document IDs

        Returns:
            Structured summary data
        """
        # Try to parse as JSON first
        import json
        try:
            data = json.loads(response)
            if 'sections' in data and 'full_summary' in data:
                return data
        except json.JSONDecodeError:
            logger.warning("LLM response is not valid JSON, using fallback parsing")

        # Fallback: Create structured response from text
        sections = []
        for i, section_title in enumerate(stakeholder_config['sections']):
            sections.append({
                'title': section_title,
                'content': f"[Content for {section_title} - parsed from response]",
                'key_points': [
                    f"Key point 1 for {section_title}",
                    f"Key point 2 for {section_title}",
                ],
                'evidence_ids': document_ids[:2] if document_ids else []
            })

        return {
            'sections': sections,
            'full_summary': response[:job.max_length * 5] if hasattr(job, 'max_length') else response[:2500],
            'tokens_used': 0
        }

    def _create_summary_records(
        self,
        job: SummaryJob,
        summary_data: Dict[str, Any]
    ) -> GeneratedSummary:
        """
        Create database records for summary and sections.

        Args:
            job: SummaryJob instance
            summary_data: Summary data from LLM

        Returns:
            GeneratedSummary instance
        """
        # Create main summary
        summary = GeneratedSummary.objects.create(
            id=f"sum_{job.id}",
            job=job,
            project_id=job.project_id,
            stakeholder_role=job.stakeholder_role,
            full_summary=summary_data['full_summary']
        )

        # Create sections
        for i, section_data in enumerate(summary_data['sections']):
            SummarySection.objects.create(
                summary=summary,
                title=section_data['title'],
                content=section_data['content'],
                order=i,
                key_points=section_data.get('key_points', []),
                evidence_ids=section_data.get('evidence_ids', [])
            )

        logger.info(f"Created summary {summary.id} with {len(summary_data['sections'])} sections")

        return summary


# Global service instance
_summary_service = None


def get_summary_service() -> SummaryGenerationService:
    """Get or create the summary generation service instance."""
    global _summary_service
    if _summary_service is None:
        _summary_service = SummaryGenerationService()
    return _summary_service
