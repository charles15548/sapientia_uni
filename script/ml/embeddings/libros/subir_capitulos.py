from script.ml.gpt.prompt import PROMPT_CAPITULOS
from script.ml.variables_globales import MIN_TEXTO_POR_PAGINA,MODELO_CAPITULO
from script.service.libroCapitulosService import limpiar_titulo
import json
import os
import openai 
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI()

def detectar_capitulos(paginas):
    if not paginas:
        return []
    
    # Leer solo las primeras paginas para no sobre cargar el 
    # Modelo GPT, de esta forma extrae en menos tiempo y más barato
    paginas_recortadas = paginas[:15]

    prompt = PROMPT_CAPITULOS


    response = client.chat.completions.create(
        model=MODELO_CAPITULO, 
        messages=[
            {"role": "system", "content": prompt},
            {
                "role": "user",
                "content": json.dumps({"paginas": paginas_recortadas}, ensure_ascii=False)
            }
        ]
    )

    contenido = response.choices[0].message.content

    try:
        data = json.loads(contenido)
        capitulos = data.get("capitulos",[])

        # Limpiar numeración de todos los caps y sub caps
        for cap in capitulos:
            cap['titulo'] = limpiar_titulo(cap["titulo"])
            for sub in cap.get("subcapitulos",[]):
                sub["titulo"] = limpiar_titulo(sub["titulo"])

        print(f"📚 Capítulos detectados:\n==========\n{capitulos}\n==========")
        return capitulos
    except json.JSONDecodeError:
        print("❌ Error parseando JSON de capítulos")
        return []