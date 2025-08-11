from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain.chat_models import init_chat_model
from langchain_tavily import TavilySearch
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.messages import SystemMessage
from langgraph.checkpoint.memory import MemorySaver  # Me permite guardar el estado del grafo
from dotenv import load_dotenv
load_dotenv()


llm = init_chat_model("google_genai:gemini-2.0-flash")


class State(TypedDict):
    messages: Annotated[list, add_messages]

memory = MemorySaver()

graph_builder = StateGraph(State)
tool = TavilySearch(max_results=10)
tools = [tool]
llm_with_tools = llm.bind_tools(tools)


def chatbot(state: State):
    mensajes = [SystemMessage(
        content="Responde siempre en español.")] + state["messages"]
    return {"messages": [llm_with_tools.invoke(mensajes)]}


graph_builder.add_node("chatbot", chatbot)
tool_node = ToolNode(tools=[tool])
graph_builder.add_node("tools", tool_node)
graph_builder.add_conditional_edges("chatbot", tools_condition)
graph_builder.add_edge("tools", "chatbot")
graph_builder.add_edge(START, "chatbot")

graph = graph_builder.compile(checkpointer=memory)

session_id= "conversacion_usuario_1"

def stream_graph_updates(user_input: str):
    # Usar config con thread_id para mantener memoria
    config = {"configurable": {"thread_id": session_id}}  # NUEVO
    
    for event in graph.stream(
        {"messages": [{"role": "user", "content": user_input}]}, 
        config=config  # AGREGADO
    ):
        for value in event.values():
            for message in value["messages"]:
                if message.type == "ai":
                    print("Asistente:", message.content)

while True:
    user_input = input("User: ")
    if user_input.lower() in ["quit", "exit", "q", "chao", "adios", "chabela"]:
        print("Adios!")
        break
    stream_graph_updates(user_input)