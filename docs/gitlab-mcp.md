# GitLab MCP Server

> **New Feature**: Dynamic GitLab API URL support with connection pooling! See [Dynamic API URL Documentation](docs/dynamic-api-url.md) for details.

[![Star History Chart](https://api.star-history.com/svg?repos=zereight/gitlab-mcp&type=Date)](https://www.star-history.com/#zereight/gitlab-mcp&Date)

## @zereight/mcp-gitlab

[![smithery badge](https://smithery.ai/badge/@zereight/gitlab-mcp)](https://smithery.ai/server/@zereight/gitlab-mcp)

GitLab MCP(Model Context Protocol) Server. **Includes bug fixes and improvements over the original GitLab MCP server.**

<a href="https://glama.ai/mcp/servers/7jwbk4r6d7"><img width="380" height="200" src="https://glama.ai/mcp/servers/7jwbk4r6d7/badge" alt="gitlab mcp MCP server" /></a>

## Tools 🛠️

<details>
<summary>Click to expand</summary>

<!-- TOOLS-START -->

1. `merge_merge_request` - Merge a merge request in a GitLab project
2. `create_or_update_file` - Create or update a single file in a GitLab project
3. `search_repositories` - Search for GitLab projects
4. `create_repository` - Create a new GitLab project
5. `get_file_contents` - Get the contents of a file or directory from a GitLab project
6. `push_files` - Push multiple files to a GitLab project in a single commit
7. `create_issue` - Create a new issue in a GitLab project
8. `create_merge_request` - Create a new merge request in a GitLab project
9. `fork_repository` - Fork a GitLab project to your account or specified namespace
10. `create_branch` - Create a new branch in a GitLab project
11. `get_merge_request` - Get details of a merge request (Either mergeRequestIid or branchName must be provided)
12. `get_merge_request_diffs` - Get the changes/diffs of a merge request (Either mergeRequestIid or branchName must be provided)
13. `list_merge_request_diffs` - List merge request diffs with pagination support (Either mergeRequestIid or branchName must be provided)
14. `get_branch_diffs` - Get the changes/diffs between two branches or commits in a GitLab project
15. `update_merge_request` - Update a merge request (Either mergeRequestIid or branchName must be provided)
16. `create_note` - Create a new note (comment) to an issue or merge request
17. `create_merge_request_thread` - Create a new thread on a merge request
18. `mr_discussions` - List discussion items for a merge request
19. `update_merge_request_note` - Modify an existing merge request thread note
20. `create_merge_request_note` - Add a new note to an existing merge request thread
21. `get_draft_note` - Get a single draft note from a merge request
22. `list_draft_notes` - List draft notes for a merge request
23. `create_draft_note` - Create a draft note for a merge request
24. `update_draft_note` - Update an existing draft note
25. `delete_draft_note` - Delete a draft note
26. `publish_draft_note` - Publish a single draft note
27. `bulk_publish_draft_notes` - Publish all draft notes for a merge request
28. `update_issue_note` - Modify an existing issue thread note
29. `create_issue_note` - Add a new note to an existing issue thread
30. `list_issues` - List issues (default: created by current user only; use scope='all' for all accessible issues)
31. `my_issues` - List issues assigned to the authenticated user (defaults to open issues)
32. `get_issue` - Get details of a specific issue in a GitLab project
33. `update_issue` - Update an issue in a GitLab project
34. `delete_issue` - Delete an issue from a GitLab project
35. `list_issue_links` - List all issue links for a specific issue
36. `list_issue_discussions` - List discussions for an issue in a GitLab project
37. `get_issue_link` - Get a specific issue link
38. `create_issue_link` - Create an issue link between two issues
39. `delete_issue_link` - Delete an issue link
40. `list_namespaces` - List all namespaces available to the current user
41. `get_namespace` - Get details of a namespace by ID or path
42. `verify_namespace` - Verify if a namespace path exists
43. `get_project` - Get details of a specific project
44. `list_projects` - List projects accessible by the current user
45. `list_project_members` - List members of a GitLab project
46. `list_labels` - List labels for a project
47. `get_label` - Get a single label from a project
48. `create_label` - Create a new label in a project
49. `update_label` - Update an existing label in a project
50. `delete_label` - Delete a label from a project
51. `list_group_projects` - List projects in a GitLab group with filtering options
52. `list_wiki_pages` - List wiki pages in a GitLab project
53. `get_wiki_page` - Get details of a specific wiki page
54. `create_wiki_page` - Create a new wiki page in a GitLab project
55. `update_wiki_page` - Update an existing wiki page in a GitLab project
56. `delete_wiki_page` - Delete a wiki page from a GitLab project
57. `get_repository_tree` - Get the repository tree for a GitLab project (list files and directories)
58. `list_pipelines` - List pipelines in a GitLab project with filtering options
59. `get_pipeline` - Get details of a specific pipeline in a GitLab project
60. `list_pipeline_jobs` - List all jobs in a specific pipeline
61. `list_pipeline_trigger_jobs` - List all trigger jobs (bridges) in a specific pipeline that trigger downstream pipelines
62. `get_pipeline_job` - Get details of a GitLab pipeline job number
63. `get_pipeline_job_output` - Get the output/trace of a GitLab pipeline job with optional pagination to limit context window usage
64. `create_pipeline` - Create a new pipeline for a branch or tag
65. `retry_pipeline` - Retry a failed or canceled pipeline
66. `cancel_pipeline` - Cancel a running pipeline
67. `play_pipeline_job` - Run a manual pipeline job
68. `retry_pipeline_job` - Retry a failed or canceled pipeline job
69. `cancel_pipeline_job` - Cancel a running pipeline job
70. `list_merge_requests` - List merge requests in a GitLab project with filtering options
71. `list_milestones` - List milestones in a GitLab project with filtering options
72. `get_milestone` - Get details of a specific milestone
73. `create_milestone` - Create a new milestone in a GitLab project
74. `edit_milestone` - Edit an existing milestone in a GitLab project
75. `delete_milestone` - Delete a milestone from a GitLab project
76. `get_milestone_issue` - Get issues associated with a specific milestone
77. `get_milestone_merge_requests` - Get merge requests associated with a specific milestone
78. `promote_milestone` - Promote a milestone to the next stage
79. `get_milestone_burndown_events` - Get burndown events for a specific milestone
80. `get_users` - Get GitLab user details by usernames
81. `list_commits` - List repository commits with filtering options
82. `get_commit` - Get details of a specific commit
83. `get_commit_diff` - Get changes/diffs of a specific commit
84. `list_group_iterations` - List group iterations with filtering options
85. `upload_markdown` - Upload a file to a GitLab project for use in markdown content
86. `download_attachment` - Download an uploaded file from a GitLab project by secret and filename
87. `list_events` - List all events for the currently authenticated user
88. `get_project_events` - List all visible events for a specified project
89. `list_releases` - List all releases for a project
90. `get_release` - Get a release by tag name
91. `create_release` - Create a new release in a GitLab project
92. `update_release` - Update an existing release in a GitLab project
93. `delete_release` - Delete a release from a GitLab project (does not delete the associated tag)
94. `create_release_evidence` - Create release evidence for an existing release (GitLab Premium/Ultimate only)
95. `download_release_asset` - Download a release asset file by direct asset path
<!-- TOOLS-END -->

</details>
