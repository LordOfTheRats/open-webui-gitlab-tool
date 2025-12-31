from typing import Any, Dict
from urllib.parse import quote_plus
from flock_gitlab.agents.base import BaseAgent
from flock_gitlab.utils.gitlab_api import gitlab_api
from flock_gitlab.utils.ollama_api import ollama_api

class PipelineTriageAgent(BaseAgent):
    """
    An agent that helps triage failed CI/CD pipelines.
    """

    def get_tool_def(self) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "gitlab_pipeline_triage",
                "description": "Analyzes a failed pipeline and suggests potential causes.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "project_id": {
                            "type": "string",
                            "description": "The ID or URL-encoded path of the project."
                        },
                        "pipeline_id": {
                            "type": "integer",
                            "description": "The ID of the pipeline."
                        }
                    },
                    "required": ["project_id", "pipeline_id"]
                }
            }
        }

    async def execute(
        self,
        project_id: str,
        pipeline_id: int,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Fetches failed jobs from a pipeline and uses an LLM to analyze the logs.
        """
        try:
            encoded_project_id = quote_plus(project_id, safe="")
            
            # 1. Fetch the jobs for the pipeline, filtering for failed ones
            jobs_path = f"/projects/{encoded_project_id}/pipelines/{pipeline_id}/jobs"
            jobs = await gitlab_api.request("GET", jobs_path, params={"scope": "failed"})

            if not jobs:
                return {"result": "No failed jobs found in this pipeline."}

            analysis_results = []

            for job in jobs:
                job_id = job.get("id")
                job_name = job.get("name")
                
                # 2. Fetch the trace (log) for each failed job
                trace_path = f"/projects/{encoded_project_id}/jobs/{job_id}/trace"
                # The trace is plain text, so we need a different kind of request
                async with httpx.AsyncClient(headers=gitlab_api.headers) as client:
                    response = await client.get(f"{gitlab_api.api_url}{trace_path}")
                
                if response.status_code != 200:
                    analysis_results.append(f"Could not fetch log for job: {job_name} (ID: {job_id})")
                    continue
                
                trace = response.text

                # 3. Create a prompt for the LLM
                prompt = f"""A CI/CD job named '{job_name}' has failed.
                Please analyze the following log and identify the likely cause of the failure.
                Provide a concise explanation and suggest a possible solution.

                Log:
                {trace[-4000:]} 
                """ # Use last 4000 characters to avoid being too long

                # 4. Generate the analysis with Ollama
                analysis_response = await ollama_api.generate(prompt)
                analysis_results.append({
                    "job_name": job_name,
                    "analysis": analysis_response.get("response")
                })
            
            return {"result": analysis_results}

        except Exception as e:
            return {"error": str(e)}
