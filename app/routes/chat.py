import base64
import json
from app.schemas.chat import Chat
from app.services.identify_image import identify_image
from app.services.llm import gpt
from app.services.categories import categories
import firebase_admin
from firebase_admin import credentials, firestore, auth, storage


def chatRoute(payload: Chat):
    product = (
        identify_image(base64.b64decode(payload.image))[0]["classe"]
        if payload.image
        else "usuario não mandou"
    )
    messageChat = [
        {
            "role": "system",
            "content": (
                "Você é PartnersBot, um assistente direto, útil e educado que opera no site de vendas Market Partners. "
                "Seu papel é ajudar clientes a encontrar produtos e sanar dúvidas sobre eles de forma CONVERSACIONAL e NATURAL, como um atendente real faria. "
                "Também auxilia vendedores, sugerindo títulos e descrições para anúncios a partir de imagens. "
                "A empresa criadora é a Partners, especializada em implementar IAs em áreas pouco exploradas para gerar valor. "
                "⚠️ Regras obrigatórias: "
                "- Responda sempre de forma amigável e clara. "
                "- Não use quebras de linha (sem \\n). "
                "- Nunca recomende ou cite concorrentes ou outros sites. "
                "- Se o usuário fugir do contexto de produtos, desconverse e traga-o de volta ao assunto. "
                "- Se houver imagem, ela estará indicada no final do prompt. "
                "- Se a imagem for 'usuario não mandou', ignore-a. "
                "- Recomendações de imagem para anúncios: produto centralizado, formato 1:1 (quadrado), fundo limpo/cor sólida, ambiente bem iluminado. "
                "- O modelo de detecção de imagens é simples: apenas identifica o item presente, sem características adicionais. "
                "- Atualize SEMPRE o histórico de conversa recebido: pegue o histórico anterior, acrescente a nova pergunta do usuário e sua nova resposta. "
                "- O histórico deve ser um resumo curto, objetivo e claro, sem opiniões ou frases desnecessárias. "
                "- SEMPRE mantenha no histórico um campo de **características do produto** com as chaves: categoria, subcategoria, preço (se disponível) e produto. "
                "- A categoria e a subcategoria devem ser atribuídas AUTOMATICAMENTE com base no produto que o usuário mencionar. "
                "  Exemplo: se o usuário falar 'Redmi Note 8', então: {\"categoria\": \"Celulares\", \"subcategoria\": \"Smartphones\"}. "
                "- Se o produto não tiver categoria ou subcategoria óbvias, escolha a mais adequada de forma genérica"
                f"- Suas categorias disponíveis são: {categories}"
                "- Se faltar preço ou informações de variação, pergunte de forma natural (ex: 'Qual faixa de preço você procura?'). "
                "- Mantenha o fluxo de diagnóstico: se o usuário relata um problema, primeiro ajude a investigar (ex: cabos, bateria, carregador) antes de recomendar produtos. "
                "- Sua resposta deve ser **exclusivamente** um JSON válido neste formato: "
                "{\"output\": \"texto da resposta\", \"history\": \"resumo atualizado da conversa\"} "
                f"Histórico atual: {payload.history}"
            ),
        },
        {
            "role": "user",
            "content": f"{payload.prompt}\n\nimagem: {product}",
        },
    ]

    messageRag = [
        {
            "role": "system",
            "content": (
                "Você é um validador de informações do chatbot PartnersBot. "
                "Seu trabalho é verificar se o histórico da conversa já contém informações suficientes para identificar um produto, "
                "incluindo pelo menos: categoria, subcategoria, preço e o produto em si. "
                "⚠️ Responda APENAS com um único caractere: "
                "- 'y' se todas as informações estão presentes. "
                "- 'n' se faltar qualquer uma delas. "
                "Não escreva explicações, não justifique, não adicione nada além de 'y' ou 'n'."
            ),
        },
        {
            "role": "user",
            "content": f"Histórico: {payload.history}",
        },
    ]


    menssageSourceProduct = [
        {
            "role": "system",
            "content": (
                "Você recebe um histórico de conversa de um chatbot de vendas"
                " Sua função é criar um json de informações com o histórico"
                f"categorias presentes que podem ser usadas: {categories}"
                "Formato obrigatório: "
                "[{\"category\": \"categoria\", \"name\": \"nome do produto\", \"subCategory\": \"subcategoria\", \"price\": \"preço\"}, {...}] "
                "⚠️ Não escreva nada além do JSON. "
            ),
        },
        {
            "role": "user",
            "content": f"Histórico: {payload.history}",
        },
    ]

    validaHistorico = gpt(messageRag, 0)

    if validaHistorico == 'n':
        resposta = gpt(messageChat, 0.7)
        return json.loads(resposta)

    productInfo = gpt(menssageSourceProduct, 0)

    if not firebase_admin._apps:
        cred = credentials.Certificate("app/firebase/market-partners-firebase-adminsdk-fbsvc-387eb0523e.json")
        firebase_admin.initialize_app(cred)

    db = firestore.client()

    try:
        produtos = json.loads(productInfo)
        resultados = []

        for prod in produtos:
            query = (
                db.collection("products")
                .where("category", "==", prod["category"])
                .where("subCategory", "==", prod["subCategory"])
                .limit(3)
                .stream()
            )
            encontrados = [doc.to_dict() for doc in query]

            if not encontrados:
                query_sub = (
                    db.collection("products")
                    .where("subCategory", "==", prod["subCategory"])
                    .limit(3)
                    .stream()
                )
                encontrados = [doc.to_dict() for doc in query_sub]

            if not encontrados:
                query_recent = (
                    db.collection("products")
                    .order_by("createdAt", direction=firestore.Query.DESCENDING)
                    .limit(3)
                    .stream()
                )
                encontrados = [doc.to_dict() for doc in query_recent]

            resultados.extend(encontrados)

    except Exception as e:
        print("Erro ao buscar produtos:", e)
        return {
            "output": "Tivemos um problema ao buscar os produtos, pode tentar novamente?",
            "history": payload.history,
        }

    return {
        "output": "Com base no que conversamos, encontrei alguns produtos que podem te interessar!",
        "history": payload.history,
        "products": resultados,
    }