"""Pipeline tools for GitLab LangChain toolkit."""

from __future__ import annotations

import asyncio
from typing import Any, Optional

import gitlab
from langchain_core.tools import BaseTool
from pydantic import BaseModel

from ..models import (
    CancelJobInput,
    GetJobTraceInput,
    GetPipelineInput,
    ListPipelineJobsInput,
    ListPipelinesInput,
    RetryJobInput,
    RunPipelineInput,
)
from .common import (
    _gitlab_error_to_message,
    _maybe_compact,
    _project_id_or_path,
    _run_async,
)


class ListPipelinesTool(BaseTool):
    """List pipelines in a project."""

    name: str = "gitlab_list_pipelines"
    description: str = (
        "List CI/CD pipelines in a project with optional filters by ref and status. "
        "Returns a list of pipelines."
    )
    args_schema: type[BaseModel] = ListPipelinesInput

    gitlab: gitlab.Gitlab
    compact_default: bool = True

    def _run(
        self,
        project: int | str,
        ref: Optional[str] = None,
        status: Optional[str] = None,
        offset: int = 0,
        page_count: int = 1,
        compact: Optional[bool] = None,
    ) -> str:
        """List pipelines (sync wrapper)."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                self._arun(
                    project=project,
                    ref=ref,
                    status=status,
                    offset=offset,
                    page_count=page_count,
                    compact=compact,
                )
            )
        finally:
            loop.close()

    async def _arun(
        self,
        project: int | str,
        ref: Optional[str] = None,
        status: Optional[str] = None,
        offset: int = 0,
        page_count: int = 1,
        compact: Optional[bool] = None,
    ) -> str:
        """List pipelines (async)."""
        try:
            pid = _project_id_or_path(project)

            def _list_pipelines():
                pipelines = []
                for page in range(offset + 1, offset + page_count + 1):
                    params = {
                        "page": page,
                        "per_page": 20,
                    }
                    if ref:
                        params["ref"] = ref
                    if status:
                        params["status"] = status

                    page_pipelines = self.gitlab.projects.get(pid).pipelines.list(
                        as_list=False, **params
                    )
                    for pipeline in page_pipelines:
                        pipelines.append(pipeline.asdict())

                return pipelines

            pipelines = await _run_async(_list_pipelines)
            use_compact = self.compact_default if compact is None else compact
            result = _maybe_compact("pipeline", pipelines, use_compact)
            return str(result)
        except gitlab.exceptions.GitlabError as e:
            raise Exception(_gitlab_error_to_message(e))
        except Exception as e:
            raise Exception(f"Error listing pipelines: {str(e)}")


class GetPipelineTool(BaseTool):
    """Get a single pipeline."""

    name: str = "gitlab_get_pipeline"
    description: str = (
        "Get details of a single pipeline by its ID. Returns full pipeline information."
    )
    args_schema: type[BaseModel] = GetPipelineInput

    gitlab: gitlab.Gitlab
    compact_default: bool = True

    def _run(
        self,
        project: int | str,
        pipeline_id: int,
        compact: Optional[bool] = None,
    ) -> str:
        """Get pipeline (sync wrapper)."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                self._arun(project=project, pipeline_id=pipeline_id, compact=compact)
            )
        finally:
            loop.close()

    async def _arun(
        self,
        project: int | str,
        pipeline_id: int,
        compact: Optional[bool] = None,
    ) -> str:
        """Get pipeline (async)."""
        try:
            pid = _project_id_or_path(project)

            def _get_pipeline():
                pipeline = self.gitlab.projects.get(pid).pipelines.get(pipeline_id)
                return pipeline.asdict()

            pipeline_data = await _run_async(_get_pipeline)
            use_compact = self.compact_default if compact is None else compact
            result = _maybe_compact("pipeline", pipeline_data, use_compact)
            return str(result)
        except gitlab.exceptions.GitlabError as e:
            raise Exception(_gitlab_error_to_message(e))
        except Exception as e:
            raise Exception(f"Error getting pipeline: {str(e)}")


class ListPipelineJobsTool(BaseTool):
    """List jobs in a pipeline."""

    name: str = "gitlab_list_pipeline_jobs"
    description: str = (
        "List all jobs in a pipeline with optional filter by job status. "
        "Returns a list of jobs."
    )
    args_schema: type[BaseModel] = ListPipelineJobsInput

    gitlab: gitlab.Gitlab
    compact_default: bool = True

    def _run(
        self,
        project: int | str,
        pipeline_id: int,
        scope: Optional[str] = None,
        offset: int = 0,
        page_count: int = 1,
        compact: Optional[bool] = None,
    ) -> str:
        """List pipeline jobs (sync wrapper)."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                self._arun(
                    project=project,
                    pipeline_id=pipeline_id,
                    scope=scope,
                    offset=offset,
                    page_count=page_count,
                    compact=compact,
                )
            )
        finally:
            loop.close()

    async def _arun(
        self,
        project: int | str,
        pipeline_id: int,
        scope: Optional[str] = None,
        offset: int = 0,
        page_count: int = 1,
        compact: Optional[bool] = None,
    ) -> str:
        """List pipeline jobs (async)."""
        try:
            pid = _project_id_or_path(project)

            def _list_jobs():
                jobs = []
                for page in range(offset + 1, offset + page_count + 1):
                    params = {
                        "page": page,
                        "per_page": 20,
                    }
                    if scope:
                        params["scope"] = scope

                    pipeline = self.gitlab.projects.get(pid).pipelines.get(pipeline_id)
                    page_jobs = pipeline.jobs.list(as_list=False, **params)
                    for job in page_jobs:
                        jobs.append(job.asdict())

                return jobs

            jobs = await _run_async(_list_jobs)
            use_compact = self.compact_default if compact is None else compact
            result = _maybe_compact("job", jobs, use_compact)
            return str(result)
        except gitlab.exceptions.GitlabError as e:
            raise Exception(_gitlab_error_to_message(e))
        except Exception as e:
            raise Exception(f"Error listing pipeline jobs: {str(e)}")


class GetJobTraceTool(BaseTool):
    """Get job trace/log output."""

    name: str = "gitlab_get_job_trace"
    description: str = (
        "Get the trace/log output of a job. Returns the raw log output."
    )
    args_schema: type[BaseModel] = GetJobTraceInput

    gitlab: gitlab.Gitlab

    def _run(
        self,
        project: int | str,
        job_id: int,
    ) -> str:
        """Get job trace (sync wrapper)."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                self._arun(project=project, job_id=job_id)
            )
        finally:
            loop.close()

    async def _arun(
        self,
        project: int | str,
        job_id: int,
    ) -> str:
        """Get job trace (async)."""
        try:
            pid = _project_id_or_path(project)

            def _get_trace():
                job = self.gitlab.projects.get(pid).jobs.get(job_id)
                trace = job.trace()
                # Trace is bytes, decode to string
                if isinstance(trace, bytes):
                    return trace.decode("utf-8")
                return str(trace)

            trace = await _run_async(_get_trace)
            return trace
        except gitlab.exceptions.GitlabError as e:
            raise Exception(_gitlab_error_to_message(e))
        except Exception as e:
            raise Exception(f"Error getting job trace: {str(e)}")


class RunPipelineTool(BaseTool):
    """Trigger/run a pipeline."""

    name: str = "gitlab_run_pipeline"
    description: str = (
        "Trigger a new pipeline on a specific ref (branch/tag/commit). "
        "Optionally pass variables to the pipeline. Returns the created pipeline."
    )
    args_schema: type[BaseModel] = RunPipelineInput

    gitlab: gitlab.Gitlab
    compact_default: bool = True

    def _run(
        self,
        project: int | str,
        ref: str,
        variables: Optional[dict[str, str]] = None,
        compact: Optional[bool] = None,
    ) -> str:
        """Run pipeline (sync wrapper)."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                self._arun(
                    project=project,
                    ref=ref,
                    variables=variables,
                    compact=compact,
                )
            )
        finally:
            loop.close()

    async def _arun(
        self,
        project: int | str,
        ref: str,
        variables: Optional[dict[str, str]] = None,
        compact: Optional[bool] = None,
    ) -> str:
        """Run pipeline (async)."""
        try:
            pid = _project_id_or_path(project)

            def _run_pipeline():
                data = {"ref": ref}
                if variables:
                    data["variables"] = variables

                pipeline = self.gitlab.projects.get(pid).pipelines.create(data)
                return pipeline.asdict()

            pipeline_data = await _run_async(_run_pipeline)
            use_compact = self.compact_default if compact is None else compact
            result = _maybe_compact("pipeline", pipeline_data, use_compact)
            return str(result)
        except gitlab.exceptions.GitlabError as e:
            raise Exception(_gitlab_error_to_message(e))
        except Exception as e:
            raise Exception(f"Error running pipeline: {str(e)}")


class RetryJobTool(BaseTool):
    """Retry a failed job."""

    name: str = "gitlab_retry_job"
    description: str = (
        "Retry a failed job. The job must be in a failed state. "
        "Returns the job details."
    )
    args_schema: type[BaseModel] = RetryJobInput

    gitlab: gitlab.Gitlab
    compact_default: bool = True

    def _run(
        self,
        project: int | str,
        job_id: int,
        compact: Optional[bool] = None,
    ) -> str:
        """Retry job (sync wrapper)."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                self._arun(project=project, job_id=job_id, compact=compact)
            )
        finally:
            loop.close()

    async def _arun(
        self,
        project: int | str,
        job_id: int,
        compact: Optional[bool] = None,
    ) -> str:
        """Retry job (async)."""
        try:
            pid = _project_id_or_path(project)

            def _retry():
                job = self.gitlab.projects.get(pid).jobs.get(job_id)
                job.retry()
                return job.asdict()

            job_data = await _run_async(_retry)
            use_compact = self.compact_default if compact is None else compact
            result = _maybe_compact("job", job_data, use_compact)
            return str(result)
        except gitlab.exceptions.GitlabError as e:
            raise Exception(_gitlab_error_to_message(e))
        except Exception as e:
            raise Exception(f"Error retrying job: {str(e)}")


class CancelJobTool(BaseTool):
    """Cancel a running job."""

    name: str = "gitlab_cancel_job"
    description: str = (
        "Cancel a running or pending job. Returns the job details."
    )
    args_schema: type[BaseModel] = CancelJobInput

    gitlab: gitlab.Gitlab
    compact_default: bool = True

    def _run(
        self,
        project: int | str,
        job_id: int,
        compact: Optional[bool] = None,
    ) -> str:
        """Cancel job (sync wrapper)."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                self._arun(project=project, job_id=job_id, compact=compact)
            )
        finally:
            loop.close()

    async def _arun(
        self,
        project: int | str,
        job_id: int,
        compact: Optional[bool] = None,
    ) -> str:
        """Cancel job (async)."""
        try:
            pid = _project_id_or_path(project)

            def _cancel():
                job = self.gitlab.projects.get(pid).jobs.get(job_id)
                job.cancel()
                return job.asdict()

            job_data = await _run_async(_cancel)
            use_compact = self.compact_default if compact is None else compact
            result = _maybe_compact("job", job_data, use_compact)
            return str(result)
        except gitlab.exceptions.GitlabError as e:
            raise Exception(_gitlab_error_to_message(e))
        except Exception as e:
            raise Exception(f"Error canceling job: {str(e)}")
