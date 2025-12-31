"""
Example usage of the GitLab LangChain Toolkit.

This example demonstrates how to use the toolkit with LangChain agents.
"""

import os
from langchain_openai import ChatOpenAI
from langchain.agents import initialize_agent, AgentType
from tools.gitlab import GitLabToolkit

# Initialize the toolkit with your GitLab instance
toolkit = GitLabToolkit(
    gitlab_url=os.getenv("GITLAB_URL", "https://gitlab.example.com"),
    token=os.getenv("GITLAB_TOKEN"),
    verify_ssl=True,
    compact_results_default=True,
    allow_repo_writes=False,  # Set to True to enable file operations
)

# Get all tools
tools = toolkit.get_tools()

# Initialize LangChain agent
llm = ChatOpenAI(
    model="gpt-4",
    api_key=os.getenv("OPENAI_API_KEY"),
)

agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.OPENAI_FUNCTIONS,
    verbose=True,
)


def example_1_list_projects():
    """Example 1: List all projects you're a member of."""
    print("\n=== Example 1: List Projects ===")
    result = agent.run("List the top 5 projects I'm a member of")
    print(result)


def example_2_list_and_filter_issues():
    """Example 2: List issues in a project."""
    print("\n=== Example 2: List Issues ===")
    result = agent.run(
        "List all open issues in project 'acme/api' with the 'bug' label"
    )
    print(result)


def example_3_create_issue():
    """Example 3: Create an issue."""
    print("\n=== Example 3: Create Issue ===")
    result = agent.run(
        """Create a new issue in project 'acme/api' with:
        - Title: 'Add user authentication'
        - Description: 'Implement OAuth2 authentication for API'
        - Labels: 'feature,authentication'
        """
    )
    print(result)


def example_4_manage_merge_requests():
    """Example 4: List and manage merge requests."""
    print("\n=== Example 4: Manage Merge Requests ===")
    result = agent.run(
        """In project 'acme/frontend':
        1. List all open merge requests
        2. Find any that target the 'main' branch
        3. Get the latest one
        """
    )
    print(result)


def example_5_check_pipelines():
    """Example 5: Check pipeline status."""
    print("\n=== Example 5: Check Pipelines ===")
    result = agent.run(
        """For project 'acme/api':
        1. List the latest pipelines on 'main' branch
        2. Get details of the most recent one
        3. If it failed, list the failed jobs
        """
    )
    print(result)


def example_6_search_users():
    """Example 6: Search for users."""
    print("\n=== Example 6: Search Users ===")
    result = agent.run(
        "Search for users with 'john' in their username or name"
    )
    print(result)


def example_7_list_project_helpers():
    """Example 7: List labels and milestones."""
    print("\n=== Example 7: List Labels and Milestones ===")
    result = agent.run(
        """In project 'acme/api':
        1. List all available labels
        2. List all active milestones
        """
    )
    print(result)


def example_8_get_file_content():
    """Example 8: Get file content from repository."""
    print("\n=== Example 8: Get File Content ===")
    result = agent.run(
        "Get the content of README.md from 'acme/docs' on main branch"
    )
    print(result)


def example_9_compare_refs():
    """Example 9: Compare two branches."""
    print("\n=== Example 9: Compare Branches ===")
    result = agent.run(
        """In project 'acme/api':
        Compare 'main' branch with 'develop' branch to see what changes
        would be included in a merge
        """
    )
    print(result)


def example_10_wiki_operations():
    """Example 10: List wiki pages."""
    print("\n=== Example 10: Wiki Operations ===")
    result = agent.run(
        """In project 'acme/docs':
        1. List all wiki pages
        2. Get the content of the 'Getting Started' page
        """
    )
    print(result)


if __name__ == "__main__":
    # Run examples
    # Note: Uncomment to run individual examples
    # Make sure your GitLab credentials are set in environment variables

    print("GitLab LangChain Toolkit Examples")
    print("=" * 40)

    # Uncomment examples to run:
    # example_1_list_projects()
    # example_2_list_and_filter_issues()
    # example_3_create_issue()
    # example_4_manage_merge_requests()
    # example_5_check_pipelines()
    # example_6_search_users()
    # example_7_list_project_helpers()
    # example_8_get_file_content()
    # example_9_compare_refs()
    # example_10_wiki_operations()

    print("\nExamples are available. Uncomment in the script to run.")
    print("\nRequired environment variables:")
    print("  - GITLAB_URL: Your GitLab instance URL")
    print("  - GITLAB_TOKEN: Your GitLab Personal Access Token")
    print("  - OPENAI_API_KEY: Your OpenAI API key")
