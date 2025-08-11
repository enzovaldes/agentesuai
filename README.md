# Agentes UAI

pregunta1.py: Asistente general con Gemini (sin restricciones)
pregunta2.py: Asistente especializado solo en SBPay con OpenAI

1. Requisitos
	Python 3.10+
	Claves de API:

		OpenAI API key
		Tavily API key
		GCP API KEY

Instalar dependencias:

pip install langchain langchain-openai langgraph langchain-tavily python-dotenv

2. Configuración

Crea un archivo .env en la raíz del proyecto con:

	OPENAI_API_KEY=tu_clave_openai
	GOOGLE_API_KEY=tu_clave_gemini
	TAVILY_API_KEY=tu_clave_tavily

3. Ejecución

Para correr el agente:

	python3 pregunta1.py
	python3 pregunta2.py
