class MockFastMCPServer:
    """
    A lightweight mock of a FastMCP server to demonstrate the middleware pipeline
    without needing a full FastMCP/MCP SDK installation in the demo.
    """
    def __init__(self):
        self.middlewares = []
        self.tools = {}

    def add_middleware(self, middleware):
        self.middlewares.append(middleware)
        
    def register_tool(self, name: str, func):
        self.tools[name] = func

    async def call_tool(self, tool_name: str, payload: dict):
        # Build the core execution
        async def final_execution(name, args, context):
            tool = self.tools.get(name)
            if not tool:
                raise Exception(f"Tool '{name}' not found")
            return await tool(args)

        # Apply middlewares in reverse order (onion architecture)
        current_executor = final_execution
        for mw in reversed(self.middlewares):
            def make_executor(middleware, next_call):
                async def wrapped_executor(name, args, context):
                    return await middleware.on_call_tool(name, args, context, next_call)
                return wrapped_executor
            current_executor = make_executor(mw, current_executor)

        # Trigger the pipeline
        return await current_executor(tool_name, payload, context={})

async def mock_crm_tool(args: dict):
    """
    Target Tool with Intentional Schema Drift.
    It expects 'total_cents', but old agents still send 'amount_usd'.
    """
    if 'total_cents' not in args:
        raise ValueError(
            "Validation Error: 400 Bad Request - Missing required field 'total_cents'. "
            "'amount_usd' is deprecated."
        )
    return {"status": "success", "recorded_cents": args['total_cents']}
