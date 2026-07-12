
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    server_params = StdioServerParameters(
        command="python",
        args=["mcp-test.py"]
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            result = await session.call_tool("additionner", {"a": 3, "b": 5})
            print("Resultat additionner:", result)

            result2 = await session.call_tool("analyser_code", {"code": """
public void deposit(double amount) throws InsufficientAmountException {
    try {
        if (amount <= 0) throw new InsufficientAmountException();
        balance += amount;
    } catch (Exception e) {
        System.out.println(e.getMessage());
    }
}
"""})
            print("Resultat analyser_code:", result2)
    
    


asyncio.run(main())