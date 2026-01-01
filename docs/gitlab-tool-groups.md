# GitLab MCP Tool Groups

Grouped GitLab MCP tools for agent assignment. All 95 tools from `docs/gitlab-mcp.md` are covered. Adjust names as needed for specialized agents.

## Projects and Namespaces
- list_namespaces, get_namespace, verify_namespace, list_projects, get_project, list_group_projects, list_project_members, search_repositories, create_repository, fork_repository

## Repos and Files
- get_repository_tree, get_file_contents, create_or_update_file, push_files, create_branch, list_commits, get_commit, get_commit_diff

## Merge Requests and Reviews
- list_merge_requests, get_merge_request, create_merge_request, update_merge_request, merge_merge_request, get_merge_request_diffs, list_merge_request_diffs, get_branch_diffs, create_merge_request_thread, mr_discussions, create_merge_request_note, update_merge_request_note, get_draft_note, list_draft_notes, create_draft_note, update_draft_note, delete_draft_note, publish_draft_note, bulk_publish_draft_notes

## Issues and Collaboration
- list_issues, my_issues, get_issue, create_issue, update_issue, delete_issue, list_issue_links, get_issue_link, create_issue_link, delete_issue_link, list_issue_discussions, create_issue_note, update_issue_note, create_note

## Labels
- list_labels, get_label, create_label, update_label, delete_label

## Planning: Milestones and Iterations
- list_milestones, get_milestone, create_milestone, edit_milestone, delete_milestone, get_milestone_issue, get_milestone_merge_requests, promote_milestone, get_milestone_burndown_events, list_group_iterations

## Pipelines and Jobs
- list_pipelines, get_pipeline, list_pipeline_jobs, list_pipeline_trigger_jobs, get_pipeline_job, get_pipeline_job_output, create_pipeline, retry_pipeline, cancel_pipeline, play_pipeline_job, retry_pipeline_job, cancel_pipeline_job

## Releases
- list_releases, get_release, create_release, update_release, delete_release, create_release_evidence, download_release_asset

## Wiki and Docs
- list_wiki_pages, get_wiki_page, create_wiki_page, update_wiki_page, delete_wiki_page, upload_markdown, download_attachment

## Events and Users
- get_users, list_events, get_project_events

