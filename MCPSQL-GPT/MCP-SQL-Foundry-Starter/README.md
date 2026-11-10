# On-prem SQL Server + MCP + Microsoft Foundry GPT-5

## How this demo works

1. The user asks a question in the Python console app.
2. Python sends the question and function-tool definitions to GPT-5 in Foundry.
3. GPT-5 returns a function-call request.
4. Python invokes the local MCP server over STDIO.
5. The MCP server connects to on-premises SQL Server and executes an approved read-only tool.
6. Python sends the MCP tool result back to GPT-5.
7. GPT-5 produces the natural-language answer.

GPT-5 does not connect to SQL directly. Python orchestrates the tool call; the MCP server owns the SQL connection.

## Prerequisites

- Python 3.10+
- SQL Server reachable from the machine running this MCP server
- Microsoft ODBC Driver 18 for SQL Server installed on that machine
- Foundry GPT-5 deployment, endpoint and API key
- Outbound HTTPS access from the Python app to Foundry
- Network access from the MCP host to SQL Server's configured TCP port

## Folder structure

```text
MCP-SQL-Foundry-Starter/
  app/chat_with_foundry.py
  mcp_sql/server.py
  mcp_sql/.env.example
  .env.example
  requirements.txt
```

## 1. Install ODBC Driver 18

Install Microsoft ODBC Driver 18 for SQL Server on the Windows machine that runs the MCP process. Then verify:

```powershell
python -c "import pyodbc; print(pyodbc.drivers())"
```

The output must include `ODBC Driver 18 for SQL Server`.

## 2. Create a least-privilege SQL login

Ask your DBA to create a dedicated SQL login/user and grant only the required permissions. Example, to be run by a DBA after creating the server login:

```sql
USE SalesDB;
CREATE USER [ai_readonly] FOR LOGIN [ai_readonly];
ALTER ROLE db_datareader ADD MEMBER [ai_readonly];
```

For tighter security, grant SELECT only on approved views/tables rather than all tables. Never use a sysadmin account.

## 3. Configure SQL connection

Copy and edit the MCP server's environment file:

```powershell
Copy-Item .\mcp_sql\.env.example .\mcp_sql\.env
```

Example values:

```env
SQL_AUTH_MODE=sql
SQL_SERVER=192.168.1.100
SQL_PORT=1433
SQL_DATABASE=SalesDB
SQL_USERNAME=ai_readonly
SQL_PASSWORD=YOUR_REAL_PASSWORD
SQL_DRIVER=ODBC Driver 18 for SQL Server
SQL_ENCRYPT=yes
SQL_TRUST_SERVER_CERTIFICATE=no
```

Use a DNS hostname or IP reachable from the MCP host. Do not use `localhost` unless SQL Server is on the same machine.

For Windows Authentication, set `SQL_AUTH_MODE=windows`, run the MCP process under a domain/Windows account granted database access, and omit SQL username/password.

Do not turn off certificate validation to work around TLS errors in production. Trust the correct SQL Server certificate.

## 4. Configure Foundry

Copy the project-root example:

```powershell
Copy-Item .\.env.example .\.env
```

Set the exact endpoint, API key, deployment name and API version for your Foundry resource:

```env
AZURE_OPENAI_ENDPOINT=https://YOUR-RESOURCE.openai.azure.com/
AZURE_OPENAI_API_KEY=YOUR_API_KEY
AZURE_OPENAI_DEPLOYMENT=YOUR_GPT5_DEPLOYMENT_NAME
AZURE_OPENAI_API_VERSION=2025-04-01-preview
```

This sample uses `AzureOpenAI` and the Responses API. Confirm that the endpoint and API version shown in your Foundry deployment's API instructions support Responses API. If your Foundry project provides a different endpoint or authentication method, adapt client initialization accordingly.

## 5. Install Python packages

From the project root in PowerShell:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If script activation is blocked in this PowerShell window:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## 6. Check network reachability

From the MCP host:

```powershell
Test-NetConnection 192.168.1.100 -Port 1433
```

Replace the example IP and port with your SQL Server details. `TcpTestSucceeded` should be `True`.

## 7. Run the complete demo

From the project root:

```powershell
python .\app\chat_with_foundry.py
```

Try:

- `Test the SQL connection.`
- `List the tables in dbo.`
- `Describe the Customers table.`
- `Show the top five customers by total sales. First inspect the available tables and columns.`

Type `exit` to quit.

## Available MCP tools

- `test_sql_connection`: test connectivity and identify the database/login.
- `list_tables`: list base tables in a schema.
- `describe_table`: inspect columns and SQL types.
- `run_readonly_query`: run one SELECT query, capped at 100 rows.

## Troubleshooting

- Login failed: check credentials, SQL authentication mode, login status and database grants.
- TCP test failed: check SQL Server TCP/IP, port, firewall, VPN and routing.
- Driver not found: install ODBC Driver 18 on the MCP host.
- TLS/certificate error: install/trust the SQL Server certificate.
- Foundry error: verify endpoint, API key, deployment name, API version and Responses API availability.
- MCP import error: activate the venv where `requirements.txt` was installed.

## Security

This is a learning/demo starter, not a production security boundary. The SQL keyword checks are basic guardrails, not a full SQL parser. The dedicated read-only database account is essential. For production, prefer approved parameterized query tools or stored procedures/views rather than arbitrary model-generated SQL. Apply least privilege, row/column security, audit logging, timeouts, result caps, secret rotation and data minimization. Never put SQL credentials in prompts, model tool arguments, source code or screenshots.
