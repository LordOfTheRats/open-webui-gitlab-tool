"""Pipeline triage agent."""

from gitlab_tool.agents.base import BaseGitLabAgent
from gitlab_tool.artifacts.gitlab import PipelineAnalysis
from gitlab_tool.artifacts.requests import TriagePipelineRequest


class PipelineTriageAgent(BaseGitLabAgent[TriagePipelineRequest, PipelineAnalysis]):
    """Agent that analyzes failed pipelines and identifies root causes."""

    def __init__(self, *args, **kwargs):
        """Initialize pipeline triage agent."""
        super().__init__(name="pipeline_triage", *args, **kwargs)

    def create_prompt(self, context: dict) -> str:
        """Create prompt for pipeline triage."""
        pipeline = context["pipeline"]
        failed_jobs = context.get("failed_jobs", [])
        job_logs = context.get("job_logs", {})

        prompt = f"""Analyze this failed GitLab CI/CD pipeline and identify the root cause.

**Pipeline Details:**
ID: {pipeline.get('id')}
Status: {pipeline.get('status')}
Ref: {pipeline.get('ref')}
SHA: {pipeline.get('sha')}
Created: {pipeline.get('created_at')}
"""

        if failed_jobs:
            prompt += f"\n\n**Failed Jobs ({len(failed_jobs)}):**\n"
            for job in failed_jobs:
                prompt += f"\n- {job.get('name')} (stage: {job.get('stage')})\n"
                prompt += f"  Status: {job.get('status')}\n"
                
                # Include log snippet if available
                job_id = job.get('id')
                if job_id in job_logs:
                    log = job_logs[job_id]
                    # Get last 20 lines
                    lines = log.split('\n')[-20:]
                    prompt += f"  Last log lines:\n"
                    prompt += '\n'.join(f"    {line}" for line in lines)
                    prompt += "\n"

        prompt += """

Analyze the failures and provide:
1. Root cause of the pipeline failure
2. Specific recommendations to fix the issue
3. Whether this appears to be a flaky test, environment issue, or code issue

Format your response as JSON with keys: root_cause, recommendations (array), issue_type
"""
        return prompt

    async def process(self, request: TriagePipelineRequest) -> PipelineAnalysis:
        """Process pipeline triage request."""
        # Fetch pipeline details
        pipeline = await self.gitlab_client.get_pipeline(request.project, request.pipeline_id)

        # Fetch failed jobs
        all_jobs = await self.gitlab_client.list_pipeline_jobs(
            request.project, request.pipeline_id, per_page=100
        )
        failed_jobs = [j for j in all_jobs if j.get("status") == "failed"]

        # Optionally fetch job logs
        job_logs = {}
        if request.include_logs and failed_jobs:
            # Limit to first 3 failed jobs to avoid token overload
            for job in failed_jobs[:3]:
                try:
                    log = await self.gitlab_client.get_job_trace(
                        request.project, job["id"]
                    )
                    job_logs[job["id"]] = log
                except Exception:
                    # Job log might not be available
                    pass

        # Create prompt and call LLM
        prompt = self.create_prompt({
            "pipeline": pipeline,
            "failed_jobs": failed_jobs,
            "job_logs": job_logs,
        })
        response = await self.call_llm(prompt, temperature=0.3)

        # Parse LLM response (simplified)
        return PipelineAnalysis(
            pipeline_id=request.pipeline_id,
            project=request.project,
            status=pipeline.get("status", "failed"),
            failed_jobs=[j.get("name", "") for j in failed_jobs],
            root_cause=f"Analysis: {response[:200]}",
            recommendations=[
                "Check the job logs for specific error messages",
                "Verify dependencies are up to date",
            ],
        )
