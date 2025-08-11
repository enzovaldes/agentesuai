import os
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START
from langgraph.graph.message import add_messages
from langchain_openai import ChatOpenAI
from langchain_tavily import TavilySearch  # CORRECCIÓN AQUÍ
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.tools import tool
from langgraph.checkpoint.memory import MemorySaver
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Inicializar el modelo OpenAI GPT
llm = ChatOpenAI(
    model="gpt-4o-mini",  # o "gpt-4" si tienes acceso
    temperature=0.1,
    openai_api_key=os.getenv("OPENAI_API_KEY") # type: ignore
)

# Inicializar TavilySearch
tavily_search = TavilySearch(max_results=5)

# Herramienta personalizada para SBPay
@tool
def search_sbpay_info(query: str) -> str:
    """
    Busca información específica sobre SBPay.cl en la web.
    Útil para obtener información actualizada sobre la empresa chilena SBPay.
    Args:
        query: La consulta específica sobre SBPay que se quiere buscar
    Returns:
        str: Información encontrada sobre SBPay desde fuentes web
    """
    try:
        # Crear consulta específica para SBPay
        search_query = f"sbpay Chile {query}"
        
        # Buscar usando TavilySearch
        results = tavily_search.run(search_query)
        
        # Formatear resultados
        if results:
            return f"🔍 Información sobre SBPay encontrada:\n\n{results}"
        else:
            return "No se encontró información específica sobre SBPay para esta consulta."
            
    except Exception as e:
        return f"Error al buscar información sobre SBPay: {str(e)}"

@tool  
def search_sbpay_website(query: str) -> str:
    """
    Busca información específicamente en el sitio web oficial de SBPay (sbpay.cl).
    Útil para obtener información oficial y actualizada directamente desde su página web.
    Args:
        query: La consulta específica que se quiere buscar en sbpay.cl
    Returns:
        str: Información encontrada en el sitio oficial de SBPay
    """
    try:
        # Búsqueda específica en el sitio sbpay.cl
        search_query = f"site:sbpay.cl {query}"
        
        # Buscar usando TavilySearch
        results = tavily_search.run(search_query)
        
        # Formatear resultados
        if results:
            return f"Información oficial de sbpay.cl:\n\n{results}"
        else:
            return "No se encontró información específica en el sitio oficial sbpay.cl para esta consulta."
            
    except Exception as e:
        return f"Error al buscar en sbpay.cl: {str(e)}"

# Definir el estado del grafo
class State(TypedDict):
    messages: Annotated[list, add_messages]

# Crear el grafo
graph_builder = StateGraph(State)
memory = MemorySaver()

# Herramientas disponibles
tools = [search_sbpay_info, search_sbpay_website]
llm_with_tools = llm.bind_tools(tools)

def chatbot(state: State):
    """Función principal del chatbot que maneja las respuestas"""
    system_message = SystemMessage(content="""
    Eres un asistente EXCLUSIVAMENTE especializado en SBPay, la empresa chilena de tecnología financiera.

    RESTRICCIONES IMPORTANTES:
    - SOLO puedes responder preguntas relacionadas con SBPay
    - NO respondas preguntas sobre otras empresas, temas generales, o cualquier cosa que no sea SBPay
    - Si te preguntan sobre algo que NO es SBPay, responde amablemente que solo puedes ayudar con información sobre SBPay
    - Rechaza consultas sobre: otras fintech, bancos, tecnología general, noticias generales, etc.

    HERRAMIENTAS DISPONIBLES (solo para SBPay):
    1. search_sbpay_info: Para buscar información general sobre SBPay en toda la web
    2. search_sbpay_website: Para buscar información específicamente en sbpay.cl

    INSTRUCCIONES PARA CONSULTAS SOBRE SBPAY:
    1. Primero, verifica que la pregunta sea específicamente sobre SBPay
    2. Si es sobre SBPay, intenta responder con tu conocimiento previo
    3. Si necesitas más información sobre SBPay, usa las herramientas:
       - Para información oficial: usa search_sbpay_website
       - Para información general sobre SBPay: usa search_sbpay_info
    4. Combina tu conocimiento con la información encontrada
    5. Responde siempre en español

    RESPUESTAS PARA CONSULTAS NO RELACIONADAS CON SBPAY:
    "Lo siento, soy un asistente especializado únicamente en información sobre SBPay, la empresa chilena de fintech. Solo puedo ayudarte con consultas relacionadas con SBPay, sus servicios, historia, equipo, productos, etc. ¿Hay algo específico sobre SBPay que te gustaría saber?"

    Sobre SBPay:
    - Es una empresa chilena de tecnología financiera (fintech)
    - Se enfoca en soluciones de pago digital
    - Para información específica, usa las herramientas de búsqueda
    """)
    
    messages = [system_message] + state["messages"]
    return {"messages": [llm_with_tools.invoke(messages)]}

# Configurar el grafo
graph_builder.add_node("chatbot", chatbot)
tool_node = ToolNode(tools=tools)
graph_builder.add_node("tools", tool_node)

graph_builder.add_conditional_edges("chatbot", tools_condition)
graph_builder.add_edge("tools", "chatbot")
graph_builder.add_edge(START, "chatbot")

# Compilar con memoria
graph = graph_builder.compile(checkpointer=memory)

def ask_about_sbpay(question: str):
    """Función para hacer preguntas sobre SBPay"""
    config = {"configurable": {"thread_id": "sbpay_session"}}
    
    print(f"\n🔍 Pregunta: {question}")
    print("=" * 50)
    
    for event in graph.stream(
        {"messages": [HumanMessage(content=question)]}, 
        config=config # type: ignore
    ):
        for value in event.values():
            for message in value.get("messages", []):
                if hasattr(message, 'content') and message.content:
                    if hasattr(message, 'type') and message.type == "ai":
                        print(f"🤖 Respuesta: {message.content}")
                    elif hasattr(message, 'name') and message.name == "search_sbpay_info":
                        print(f"🔎 Buscando información...")
# Función principal para interactuar con el sistema
def main():
    print("🚀 Sistema de Información SBPay - Powered by OpenAI + Tavily")
    print("Escribe 'salir' para terminar\n")
    
    # Preguntas de ejemplo
    ejemplos = [
        "¿Qué es SBPay?",
        "¿Cuáles son los servicios de SBPay?",
        "¿Quiénes son los fundadores de SBPay?",
        "¿En qué año se fundó SBPay?",
        "¿Cuál es el modelo de negocio de SBPay?"
    ]
    
    print("💡 Ejemplos de preguntas que puedes hacer:")
    for i, ejemplo in enumerate(ejemplos, 1):
        print(f"   {i}. {ejemplo}")
    print()
    
    while True:
        try:
            pregunta = input("❓ Tu pregunta sobre SBPay: ").strip()
            
            if pregunta.lower() in ['salir', 'exit', 'quit', 'bye']:
                print("👋 ¡Hasta luego!")
                break
                
            if not pregunta:
                print("⚠️  Por favor, escribe una pregunta válida sobre sbpaye.")
                continue
                
            ask_about_sbpay(pregunta)
            print("\n" + "-" * 80 + "\n")
            
        except KeyboardInterrupt:
            print("\n👋 ¡Hasta luego!")
            break
        except Exception as e:
            print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    # Verificar que las API keys estén configuradas
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: Configura OPENAI_API_KEY en tu archivo .env")
        exit(1)
        
    if not os.getenv("TAVILY_API_KEY"):
        print("❌ Error: Configura TAVILY_API_KEY en tu archivo .env")
        print("💡 Obtén tu API key gratis en: https://tavily.com")
        exit(1)
    
    print("✅ APIs configuradas correctamente")
    main()