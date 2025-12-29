# Open WebUI Zammad Tool

This repository contains two Open WebUI tools:

1. **GitLab Tool** (`gitlab.py`) - Comprehensive GitLab integration
2. **Zammad Tool** (`zammad.py`) - Zammad ticket system integration

## Zammad Tool

A comprehensive Open WebUI integration for Zammad ticket systems. Enables AI assistants to manage tickets, articles, users, and organizations through natural language.

### Features

- ✅ **Ticket Management**: Create, read, update, and list tickets with advanced filtering
- ✅ **Article Operations**: Add and view ticket comments, notes, and emails
- ✅ **User Management**: Search and retrieve user information
- ✅ **Organization Management**: Search and manage customer organizations
- ✅ **Helper Endpoints**: Access ticket states, groups, and priorities
- ✅ **Compact Mode**: Reduce response size while preserving essential data
- ✅ **Retry Logic**: Automatic retry with exponential backoff for reliability
- ✅ **Flexible Authentication**: Support for API tokens or HTTP Basic auth

### Installation

1. Copy `zammad.py` to your Open WebUI tools directory
2. Restart Open WebUI
3. Configure the tool through the admin interface

### Configuration

Configure the following in Open WebUI's tool settings:

**Required Settings:**
- `base_url`: Your Zammad instance URL (e.g., `https://zammad.example.com`)
- `token`: API Token (recommended) OR
- `username` + `password`: HTTP Basic authentication credentials

**Optional Settings:**
- `verify_ssl`: Enable/disable SSL verification (default: true)
- `timeout_seconds`: Request timeout (default: 30.0)
- `per_page`: Default page size for lists (default: 20)
- `compact_results_default`: Enable compact mode by default (default: true)
- `max_retries`: Maximum retry attempts (default: 3)
- `backoff_initial_seconds`: Initial retry delay (default: 0.8)
- `backoff_max_seconds`: Maximum retry delay (default: 10.0)
- `retry_jitter`: Jitter for retry delays (default: 0.2)

### Authentication

**Recommended: API Token**

1. Log into your Zammad instance
2. Go to Profile → Token Access
3. Create a new token with appropriate permissions
4. Copy the token to the `token` field in Open WebUI

**Alternative: HTTP Basic Auth**

1. Use your Zammad username in the `username` field
2. Use your Zammad password in the `password` field
3. Leave `token` empty

### Usage Examples

Once configured, you can interact with Zammad through natural language:

**List Tickets:**
```
"Show me all open tickets in the Support group"
"List all new tickets"
"Find tickets assigned to user@example.com"
```

**Create Tickets:**
```
"Create a ticket titled 'Login issue' for customer@example.com in the Support group"
"Open a new high priority ticket for 'Server down' in the IT group"
```

**View Ticket Details:**
```
"Show me ticket 42"
"What are the comments on ticket 123?"
```

**Update Tickets:**
```
"Assign ticket 42 to agent@example.com"
"Change ticket 123 state to closed"
"Update ticket 42 priority to high"
```

**Search Users:**
```
"Find user john@example.com"
"Search for agent Alice Smith"
```

**Manage Organizations:**
```
"List all organizations"
"Find organization 'Acme Corp'"
```

### Available Methods

#### Ticket Operations
- `zammad_list_tickets()` - List tickets with optional filtering
- `zammad_get_ticket()` - Get a single ticket by ID
- `zammad_create_ticket()` - Create a new ticket
- `zammad_update_ticket()` - Update an existing ticket

#### Article Operations
- `zammad_list_ticket_articles()` - List articles for a ticket
- `zammad_create_ticket_article()` - Add a comment/note to a ticket

#### User Operations
- `zammad_search_users()` - Search users by name, email, or login
- `zammad_get_user()` - Get a user by ID
- `zammad_list_users()` - List all users

#### Organization Operations
- `zammad_list_organizations()` - List all organizations
- `zammad_get_organization()` - Get an organization by ID
- `zammad_search_organizations()` - Search organizations by name

#### Helper Operations
- `zammad_list_ticket_states()` - List available ticket states
- `zammad_list_groups()` - List ticket groups
- `zammad_list_priorities()` - List ticket priorities

### Compact Mode

By default, responses are returned in compact mode to reduce token usage while preserving essential information:

- **Ticket**: Includes ID, number, title, state, priority, group, customer, owner, timestamps, tags
- **Article**: Includes ID, ticket_id, type, sender, body, timestamps (body is always preserved)
- **User**: Includes ID, login, name, email, organization, active status
- **Organization**: Includes ID, name, note, active status, timestamps

Set `compact=False` in method calls or change `compact_results_default` to disable.

### Documentation

- **Zammad Design Specification**: See `ZAMMAD_DESIGN_SPECIFICATION.md` for detailed architecture and API documentation
- **Zammad API Docs**: https://docs.zammad.org/en/latest/api/intro.html

### Requirements

- Python 3.9+
- `httpx` - Async HTTP client
- `pydantic` - Data validation
- Open WebUI 0.4.0+

### Troubleshooting

**Authentication Error:**
- Verify your token or username/password are correct
- Ensure your Zammad user has appropriate permissions
- Check that the token hasn't expired

**Connection Error:**
- Verify `base_url` is correct and accessible
- Check network connectivity to your Zammad instance
- Try disabling `verify_ssl` for self-signed certificates (not recommended for production)

**404 Not Found:**
- Verify the ticket/user/organization ID exists
- Check that your user has permission to access the resource

### License

MIT License - See LICENSE file for details

### Credits

Adapted from the GitLab Tool for Open WebUI by René Vögeli.

---

## GitLab Tool

See `DESIGN_SPECIFICATION.md` for GitLab tool documentation.

The GitLab tool (`gitlab.py`) provides comprehensive access to GitLab instances including:
- Projects, Issues, and Merge Requests
- Repository browsing and file operations
- CI/CD pipeline management
- Wiki operations
- And much more

Refer to the original documentation for full details.
