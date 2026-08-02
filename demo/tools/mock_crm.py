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
      
        async def final_execution(name, args, context):
            tool = self.tools.get(name)
            if not tool:
                raise Exception(f"Tool '{name}' not found")
            return await tool(args)

       
        current_executor = final_execution
        for mw in reversed(self.middlewares):
            def make_executor(middleware, next_call):
                async def wrapped_executor(name, args, context):
                    return await middleware.on_call_tool(name, args, context, next_call)
                return wrapped_executor
            current_executor = make_executor(mw, current_executor)

      
        return await current_executor(tool_name, payload, context={})

async def mock_crm_tool(args: dict):
    """
    Target Tool with Intentional Schema Drift and Outage Simulation.
    It expects 'total_cents', but old agents still send 'amount_usd'.
    """
    # Simulate a complete provider outage (500 Error)
    if args.get('total_cents') == 50000 or args.get('amount_usd') == 500:
        raise Exception("500 Internal Server Error: The legacy CRM provider is completely offline.")

    if 'total_cents' not in args:
        raise ValueError(
            "Validation Error: 400 Bad Request - Missing required field 'total_cents'. "
            "'amount_usd' is deprecated."
        )
    return {"status": "success", "recorded_cents": args['total_cents']}

async def mock_salesforce_tool(args: dict):
    """
    Competitor Backup Tool.
    Has a completely different schema: expects 'customer_id' (str) and 'revenue_usd' (float).
    """
    if 'customer_id' not in args or 'revenue_usd' not in args:
        raise ValueError("Salesforce Validation Error: Missing 'customer_id' or 'revenue_usd'")
    
    return {"status": "success", "vendor": "salesforce", "customer": args['customer_id'], "revenue": args['revenue_usd']}
