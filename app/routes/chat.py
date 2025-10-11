import base64
import json
from app.schemas.chat import Chat
from app.services.identify_image import identify_image
from app.services.llm import gpt
from app.services.categories import categories
import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1.base_query import FieldFilter
from rapidfuzz import fuzz



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
                "- Responda sempre de forma amigável e clara"
                "- detecte o idioma da pessoa, e reponda o mesmo que o dela"
                "- Não use quebras de linha (sem \\n). "
                "- Nunca recomende ou cite concorrentes ou outros sites. "
                "- Se o usuário fugir do contexto de produtos, desconverse e traga-o de volta ao assunto. "
                "- Se houver imagem, ela estará indicada no final do prompt. "
                "- Se a imagem for 'usuario não mandou', ignore-a."
                "- Recomendações de imagem para anúncios: produto centralizado, formato 1:1 (quadrado), fundo limpo/cor sólida, ambiente bem iluminado. "
                "- O modelo de detecção de imagens é simples: apenas identifica o item presente, sem características adicionais. "
                "- Atualize SEMPRE o histórico de conversa recebido: pegue o histórico anterior, acrescente a nova pergunta do usuário e sua nova resposta. "
                "- O histórico deve ser um resumo curto, objetivo e claro, sem opiniões ou frases desnecessárias. "
                "- SEMPRE mantenha no histórico um campo de **características do produto** com as chaves: categoria, subcategoria, preço e produto. "
                "- A categoria e a subcategoria devem ser atribuídas AUTOMATICAMENTE com base no produto que o usuário mencionar. "
                "- Exemplo: se o usuário falar 'cabo tipo C', então: {\"categoria\": \"Acessórios\", \"subcategoria\": \"Cabos USB\", \"preço\": \"20 reais\", \"produto\": \"Cabo tipo C\"}. "
                "- Se não houver categoria ou subcategoria óbvias, escolha a mais adequada de forma genérica. "
                f"- Suas categorias disponíveis são: {categories} "
                "- Se faltar preço, pergunte de forma natural (ex: 'Qual faixa de preço você procura?'). "
                "- Nunca deixe categoria, subcategoria, preço ou produto vazios: se não souber, preencha com valores genéricos (ex: categoria='Acessórios', subcategoria='Diversos', preço='não informado'). "
                "- O valor de 'rag' deve ser 'y' sempre que houver produto, preço, categoria e subcategoria (mesmo preenchidos de forma genérica). "
                "- Use 'rag': 'n' somente se realmente faltar alguma dessas quatro informações e não houver como inferir. "
                "- Sua resposta deve ser **exclusivamente** um JSON válido neste formato: "
                "{\"output\": \"texto da resposta\", \"history\": \"resumo atualizado da conversa\", \"rag\": \"y ou n\"} "
                f"Histórico atual: {payload.history}"
            ),
        },
        {
            "role": "user",
            "content": f"{payload.prompt}\n\nimagem: {product}",
        },
    ]



    menssageSourceProduct = [
        {
            "role": "system",
            "content": (
                "Você recebe um histórico de conversa de um chatbot de vendas"
                " Sua função é criar um json de informações com o histórico"
                " Tente criar elas com suas infromações, independente do jeito que elas vieram, se REALMENTE não der retorne em moreInfo oque precisa ter a mais, caso n precise retorne so n"
                f"categorias presentes que podem ser usadas: {categories}"
                "Formato obrigatório: {\"moreInfo\": \"informacoes extras\" ou \"n\", \"products\": [{\"category\": \"categoria\", \"name\": \"nome do produto\", \"subCategory\": \"subcategoria\", \"price\": \"preco\"}]}"
                "⚠️ Responda apenas com um JSON válido, sem texto adicional, sem explicações e sem comentários."
            ),
        },
        {
            "role": "user",
            "content": f"Histórico: {payload.history}",
        },
    ]


    resposta = gpt(messageChat, 0.7)
    resposta = json.loads(resposta)

    print("RESPOSTA DO CHATBOT:", resposta)

    if resposta.get("rag") == "n":
        return {
            "output": resposta.get("output"),
            "history": resposta.get("history"),
        }

    productInfo = gpt(menssageSourceProduct, 0)
    product_json = json.loads(productInfo)

    if product_json.get("moreInfo") != "n":
        missing = product_json.get("moreInfo")
        print(f"⚠️ Faltam informações: {missing}")
        return {
            "output": f"Entendi! Só preciso que você me diga o(a) {missing} para continuar a busca.",
            "history": payload.history + f" Solicitei ao usuário o(a) {missing} pois estava faltando.",
        }

    if not firebase_admin._apps:
        cred = credentials.Certificate("app/firebase/market-partners-firebase-adminsdk-fbsvc-387eb0523e.json")
        firebase_admin.initialize_app(cred)

    db = firestore.client()

    try:
        produtos = product_json.get("products")
        resultados = []

        for prod in produtos:
            nome_produto = prod.get("name", "").lower().strip()
            encontrados = []

            todos = db.collection("products").limit(100).stream()
            lista_produtos = [{"id": doc.id, **doc.to_dict()} for doc in todos]

            parecidos = sorted(
                lista_produtos,
                key=lambda x: fuzz.partial_ratio(nome_produto, x.get("name", "").lower()),
                reverse=True,
            )

            encontrados = [
                p for p in parecidos if fuzz.partial_ratio(nome_produto, p.get("name", "").lower()) > 60
            ][:5]

            if not encontrados:
                query = (
                    db.collection("products")
                    .where(filter=FieldFilter("category", "==", prod["category"]))
                    .where(filter=FieldFilter("subCategory", "==", prod["subCategory"]))
                    .limit(3)
                    .stream()
                )
                encontrados = [{"id": doc.id, **doc.to_dict()} for doc in query]

            if not encontrados:
                query_sub = (
                    db.collection("products")
                    .where(filter=FieldFilter("subCategory", "==", prod["subCategory"]))
                    .limit(3)
                    .stream()
                )
                encontrados = [{"id": doc.id, **doc.to_dict()} for doc in query_sub]


            if not encontrados:
                query_recent = (
                    db.collection("products")
                    .order_by("createdAt", direction=firestore.Query.DESCENDING)
                    .limit(3)
                    .stream()
                )
                encontrados = [{"id": doc.id, **doc.to_dict()} for doc in query_recent]

            resultados.extend(encontrados)

        if not resultados:
            print("Nenhum produto encontrado nas tentativas.")
            resultados = []

    except Exception as e:
        print("Erro ao buscar produtos:", e)
        return {
            "output": "Tivemos um problema ao buscar os produtos, pode tentar novamente?",
            "history": payload.history,
        }

    return {
        "output": resposta.get("output"),
        "history": payload.history,
        "products": resultados,
    }