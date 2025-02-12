import asyncio
import autogen
from typing import Dict, Any

class AgentChatManager:
    def __init__(self, llm_config=None):
        if llm_config is None:
            llm_config = {"model": "gpt-3.5-turbo", "temperature": 0}
            
        # Basic assistant for simple queries
        self.assistant = autogen.AssistantAgent(
            name="assistant",
            llm_config=llm_config,
            system_message="You are a helpful assistant."
        )
        
        # Code assistant for programming tasks
        self.code_assistant = autogen.AssistantAgent(
            name="code_assistant",
            llm_config=llm_config,
            system_message="You are a programming expert. Provide code solutions and explanations."
        )
        
        # Math assistant for calculations
        self.math_assistant = autogen.AssistantAgent(
            name="math_assistant",
            llm_config=llm_config,
            system_message="You are a mathematics expert. Help solve math problems step by step."
        )
        
        # User proxy for all assistants
        self.user_proxy = autogen.UserProxyAgent(
            name="user_proxy",
            human_input_mode="NEVER",
            max_consecutive_auto_reply=10,
            code_execution_config=False,
        )
        
        self.outgoing_queue = asyncio.Queue()
        self.incoming_queue = asyncio.Queue()
        self.user_proxy.set_queues(self.incoming_queue, self.outgoing_queue)

    async def initiate_basic_chat(self, message: str):
        try:
            await self.user_proxy.a_initiate_chat(
                self.assistant,
                clear_history=True,
                message=message
            )
            final_response = await self.outgoing_queue.get()
            return {"type": "basic", "response": final_response}
        except Exception as e:
            print(f"Error in basic chat: {str(e)}")
            return {"type": "error", "message": str(e)}

    async def initiate_code_chat(self, message: str):
        try:
            await self.user_proxy.a_initiate_chat(
                self.code_assistant,
                clear_history=True,
                message=f"Please help with this programming task: {message}"
            )
            final_response = await self.outgoing_queue.get()
            return {"type": "code", "response": final_response}
        except Exception as e:
            print(f"Error in code chat: {str(e)}")
            return {"type": "error", "message": str(e)}

    async def initiate_math_chat(self, message: str):
        try:
            await self.user_proxy.a_initiate_chat(
                self.math_assistant,
                clear_history=True,
                message=f"Please solve this math problem: {message}"
            )
            final_response = await self.outgoing_queue.get()
            return {"type": "math", "response": final_response}
        except Exception as e:
            print(f"Error in math chat: {str(e)}")
            return {"type": "error", "message": str(e)}
