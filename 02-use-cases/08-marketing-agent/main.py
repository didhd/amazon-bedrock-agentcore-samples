import os
import json
import logging
import glob
from dotenv import load_dotenv
from typing import Optional, List, Dict, Any

from rich.table import Table

# --- Pre-computation and Configuration ---
# Must be set before importing strands to enable rich output for tools
os.environ["STRANDS_TOOL_CONSOLE_MODE"] = "enabled"
# Bypass the confirmation prompt for potentially risky tools like python_repl
os.environ["BYPASS_TOOL_CONSENT"] = "true"

from strands import Agent
from strands_tools import python_repl, file_write, editor, mem0_memory

# Import custom tools and agent configurations
from tools.tavily_tool import web_search, web_extract, web_crawl
from tools.knowledge_base_tool import get_schema
from tools.sqllite_tool import run_sqlite_query
import agents.planner_agent as planner_config
import agents.researcher_agent as researcher_config
import agents.text2sql_agent as text2sql_config
import agents.python_agent as python_config
import agents.report_agent as report_config
import agents.reflection_agent as reflection_config
import agents.memory_agent as memory_config
from constants import BEDROCK_MODEL

from bedrock_agentcore.runtime import BedrockAgentCoreApp
from bedrock_agentcore_starter_toolkit import Runtime

# Ignore deprecation warnings
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

# Load environment variables from .env file
load_dotenv()

# --- Global Configurations ---
app = BedrockAgentCoreApp()
user_id = "marketing_user"

class Config:
    """Manages application configuration and environment validation."""

    def __init__(self):
        self.tavily_api_key: Optional[str] = os.getenv("TAVILY_API_KEY")
        self.otel_exporter_endpoint: Optional[str] = os.getenv(
            "OTEL_EXPORTER_OTLP_ENDPOINT"
        )

        # Map agent names from the planner to their configuration modules.
        self.agent_configs = {
            "researcher_agent": researcher_config,
            "text2sql_agent": text2sql_config,
            "python_agent": python_config,
            "report_agent": report_config,
            "reflection_agent": reflection_config,
        }

config = Config()

def generate_query_from_memories(query: str, memories: List[Dict]) -> str:
    # Format memories into a string for the LLM
    memories_str = "\n".join([f"- {mem['memory']}" for mem in memories])

    # Create a prompt that includes user context
    prompt = f"""
User ID: "{user_id}"
User question: "{query}"

Relevant memories for user "{user_id}":
{memories_str}

Generate a helpful query using the memories as context.
"""

    return prompt

def run_planner(query: str) -> Optional[list]:
    """Runs the planner agent to generate a task list."""
    # Create a fresh planner agent for each execution to avoid state conflicts
    planner_agent = Agent(
        model=BEDROCK_MODEL, system_prompt=planner_config.system_prompt, messages=[]
    )

    try:
        raw_output = str(
            planner_agent(f"Create a plan for the following user request: {query}")
        )

        json_start = raw_output.find("{")
        json_end = raw_output.rfind("}") + 1
        if json_start == -1 or json_end == 0:
            raise json.JSONDecodeError(
                "No JSON object found in planner's output.", raw_output, 0
            )

        plan_str = raw_output[json_start:json_end]
        plan = json.loads(plan_str)
        return plan.get("tasks")
    except (json.JSONDecodeError, KeyError) as e:
        print(f"[bold red]❌ Failed to parse plan:[/bold red] {e}")
        print(f"[dim]LLM Output:\n{raw_output}[/dim]")
        return None
    except Exception as e:
        print(f"[bold red]❌ Planner execution failed:[/bold red] {e}")
        return None

def execute_plan(tasks: list, user_query: str) -> str:
    """Executes the generated plan by running agents with parallel execution and reflection."""
    completed_tasks = {}
    task_results = {}
    max_retries = 2

    for retry_count in range(max_retries + 1):
        if retry_count == 0:
            print(
                f"\n[bold blue]🚀 Starting workflow execution[/bold blue]"
            )
        else:
            print(
                f"\n[bold blue]🔄 Retry attempt {retry_count + 1}/{max_retries + 1}[/bold blue]"
            )

        # Reset for retry
        if retry_count > 0:
            completed_tasks = {}
            task_results = {}
            execution_order = []

        # Sort tasks by dependencies (simple topological sort)
        remaining_tasks = tasks.copy()
        execution_order = []

        while remaining_tasks:
            # Find tasks with no unmet dependencies
            ready_tasks = []
            for task in remaining_tasks:
                deps = task.get("dependencies", [])
                if all(dep in completed_tasks for dep in deps):
                    ready_tasks.append(task)

            if not ready_tasks:
                print(
                    "[bold red]❌ Circular dependency detected or invalid dependencies![/bold red]"
                )
                return

            # Execute ready tasks in parallel if there are multiple
            if len(ready_tasks) > 1:
                print(
                    f"[bold cyan]⚡ Executing {len(ready_tasks)} tasks in parallel[/bold cyan]"
                )
                import concurrent.futures

                with concurrent.futures.ThreadPoolExecutor(
                    max_workers=min(len(ready_tasks), 3)
                ) as executor:
                    future_to_task = {}
                    for task in ready_tasks:
                        future = executor.submit(
                            execute_single_task,
                            task,
                            task_results,
                            user_query,
                            tasks,
                        )
                        future_to_task[future] = task

                    for future in concurrent.futures.as_completed(future_to_task):
                        task = future_to_task[future]
                        try:
                            result = future.result()
                            task_results[task["task_id"]] = result
                            completed_tasks[task["task_id"]] = "COMPLETED"
                            execution_order.append(task)
                            remaining_tasks.remove(task)
                            print(
                                f"[bold green]✅ Completed:[/bold green] {task['task_id']}"
                            )
                        except Exception as e:
                            print(
                                f"[bold red]❌ Failed:[/bold red] {task['task_id']} - {e}"
                            )
                            completed_tasks[task["task_id"]] = "FAILED"
                            task_results[task["task_id"]] = f"Error: {e}"
                            execution_order.append(task)
                            remaining_tasks.remove(task)
            else:
                # Single task execution
                task = ready_tasks[0]
                execution_order.append(task)
                remaining_tasks.remove(task)

                try:
                    result = execute_single_task(
                        task, task_results, user_query, tasks
                    )
                    task_results[task["task_id"]] = result
                    completed_tasks[task["task_id"]] = "COMPLETED"
                    print(
                        f"[bold green]✅ Completed:[/bold green] {task['task_id']}"
                    )
                except Exception as e:
                    print(
                        f"[bold red]❌ Failed:[/bold red] {task['task_id']} - {e}"
                    )
                    completed_tasks[task["task_id"]] = "FAILED"
                    task_results[task["task_id"]] = f"Error: {e}"

        # Run reflection after all tasks complete
        if should_run_reflection(tasks):
            reflection_result = run_reflection(
                user_query, task_results, execution_order
            )
            if "PROCEED" in reflection_result.upper():
                print(
                    "[bold green]🎯 Reflection: Quality approved - PROCEED[/bold green]"
                )
                break
            elif "RETRY" in reflection_result.upper() and retry_count < max_retries:
                print(
                    f"[bold yellow]🔄 Reflection: Quality needs improvement - RETRY (attempt {retry_count + 2}/{max_retries + 1})[/bold yellow]"
                )
                print(
                    "[bold cyan]🔄 Restarting workflow from the beginning...[/bold cyan]"
                )
                # Clear execution order for clean restart display
                execution_order = []
                continue  # This will restart the for loop with retry_count + 1
            else:
                if retry_count >= max_retries:
                    print(
                        "[bold red]⚠️ Max retries reached - proceeding with current results[/bold red]"
                    )
                else:
                    print(
                        "[bold red]⚠️ Reflection result unclear - proceeding with current results[/bold red]"
                    )
                break
        else:
            # No reflection needed, proceed
            break

    # Show final summary
    print("\n[bold green]🎉 Plan Execution Complete![/bold green]")

    summary_table = Table(
        title="Task Execution Summary",
        show_header=True,
        header_style="bold magenta",
    )
    summary_table.add_column("Task ID", style="cyan")
    summary_table.add_column("Agent", style="yellow")
    summary_table.add_column("Status", style="green")

    passed = "Success"

    for task in execution_order:
        status = completed_tasks.get(task["task_id"], "UNKNOWN")
        if status == "COMPLETED":
            status_style = "green"
        elif status == "TIMEOUT":
            status_style = "yellow"
        else:
            status_style = "red"
            passed = "Failure"
        summary_table.add_row(
            task["task_id"],
            task["agent"],
            f"[{status_style}]{status}[/{status_style}]",
        )

    print(summary_table)

    return passed

def execute_single_task(task: dict, task_results: dict, user_query: str, all_tasks: list) -> str:
    """Execute a single task and return the result."""
    agent_name = task.get("agent")
    if agent_name not in config.agent_configs:
        raise Exception(f"Unknown agent: '{agent_name}'")

    print(
        f"[bold blue]🔄 Executing:[/bold blue] {task['task_id']} ({agent_name})"
    )

    # Create agent with appropriate tools
    agent_cfg = config.agent_configs[agent_name]

    # Determine which tools this agent needs
    agent_tools = []
    if agent_name == "researcher_agent":
        agent_tools = [web_search, web_extract, web_crawl]
    elif agent_name == "python_agent":
        agent_tools = [python_repl]
    elif agent_name == "report_agent":
        agent_tools = [file_write, editor]
    elif agent_name == "text2sql_agent":
        agent_tools = [get_schema, run_sqlite_query]
    elif agent_name == "reflection_agent":
        agent_tools = []  # No special tools needed

    # Create fresh agent instance with configured Bedrock model
    agent = Agent(
        model=BEDROCK_MODEL,
        system_prompt=agent_cfg.system_prompt,
        tools=agent_tools,
        messages=[],  # Fresh message history
    )

    # Build context from dependent tasks with better structure
    context_parts = []
    for dep_id in task.get("dependencies", []):
        if dep_id in task_results:
            # Find the original task info for better context
            dep_task_info = next(
                (t for t in all_tasks if t["task_id"] == dep_id), None
            )
            if dep_task_info:
                context_parts.append(
                    f"=== RESULTS FROM: {str(dep_id).upper()} ({str(dep_task_info.get('agent', 'unknown'))}) ===\n"
                    f"Task Description: {str(dep_task_info.get('description', 'N/A'))}\n"
                    f"Results:\n{str(task_results[dep_id])}\n"
                    f"{'='*60}"
                )
            else:
                context_parts.append(
                    f"Results from {str(dep_id)}:\n{str(task_results[dep_id])}"
                )

    # Create the prompt with better structure
    if context_parts:
        task_prompt = (
            f"CONTEXT FROM PREVIOUS TASKS:\n"
            f"{'='*80}\n"
            f"\n\n".join(context_parts) + f"\n\n{'='*80}\n"
            f"YOUR CURRENT TASK:\n"
            f"{str(task['description'])}\n\n"
            f"IMPORTANT: Use the context above to inform your work. "
            f"Reference specific findings and build upon previous results."
        )
    else:
        task_prompt = task["description"]

    # Execute the task with additional context for report agent
    if agent_name == "report_agent":
        # For report agent, also pass the original user query for context
        full_prompt = f"ORIGINAL USER REQUEST: {user_query}\n\n{task_prompt}"
        result = agent(full_prompt)
    else:
        result = agent(task_prompt)

    # Show a preview of the result
    result_preview = (
        str(result)[:200] + "..." if len(str(result)) > 200 else str(result)
    )
    print(f"[dim]Result preview: {result_preview}[/dim]")

    return str(result)

def should_run_reflection(tasks: list) -> bool:
    """Determine if reflection should be run based on task types."""
    # Run reflection if there are multiple research/analysis tasks
    research_tasks = [
        t
        for t in tasks
        if t.get("agent") in ["researcher_agent", "python_agent", "text2sql_agent"]
    ]
    return len(research_tasks) >= 2

def run_reflection(user_query: str, task_results: dict, execution_order: list) -> str:
    """Run the reflection agent to evaluate task quality."""
    print(
        "[bold purple]🔍 Running quality reflection...[/bold purple]"
    )

    # Create reflection agent
    reflection_agent = Agent(
        model=BEDROCK_MODEL,
        system_prompt=reflection_config.system_prompt,
        tools=[],
        messages=[],
    )

    # Build reflection prompt
    results_summary = "\n\n".join(
        [
            f"Task: {task['task_id']} ({task.get('agent', 'unknown')})\nResult: {task_results.get(task['task_id'], 'No result')}"
            for task in execution_order
        ]
    )

    reflection_prompt = f"""Original Request: {user_query}

Task Results:
{results_summary}

Please evaluate the quality and completeness of these results."""

    result = reflection_agent(reflection_prompt)
    print(f"[dim]Reflection result: {str(result)[:300]}...[/dim]")
    return str(result)

@app.entrypoint
def run(payload):
    mem0agent = memory_config.create_memory_agent()

    user_query = payload.get("prompt", "No prompt entered.")

    # Automatically analyze and store valuable information
    try:
        was_stored = memory_config.analyze_and_store_if_valuable(
            mem0agent, user_query, user_id
        )
        if was_stored:
            print(
                "\n[dim]💾 Stored valuable information from your input[/dim]\n"
            )
    except Exception as e:
        print(f"\n[dim]⚠️ Memory analysis failed: {e}[/dim]\n")
    
    # Retrieve relevant memories for context
    try:
        relevant_memories = memory_config.retrieve_memories(
            mem0agent, user_query, user_id
        )

        if relevant_memories:
            print(
                f"[bold cyan]🧠 Found {len(relevant_memories)} relevant memories[/bold cyan]"
            )
            user_query = generate_query_from_memories(
                user_query, relevant_memories
            )
        else:
            print(
                "[dim]No relevant memories found for this query[/dim]"
            )
    except Exception as e:
        print(
            f"[bold yellow]⚠️ Memory retrieval failed: {e}[/bold yellow]"
        )
        # Continue without memories if retrieval fails
    
    planned_tasks = run_planner(user_query)

    if planned_tasks:
        print(
            f"[bold green]✅ Plan Generated:[/bold green] {len(planned_tasks)} tasks."
        )

        status = execute_plan(planned_tasks, user_query)

        # get report
        result_files = glob.glob("/tmp/reports/marketing_report_*.md")
        logging.debug(result_files) 

        print("Status of execution: " + status)
    
    return {"status": status}
        
if __name__ == "__main__":
    app.run()
