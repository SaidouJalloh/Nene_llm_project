import anthropic
import json
import gradio as gr
import re
import os
import time
from dotenv import load_dotenv

# Charger les variables d'environnement du fichier .env
load_dotenv()

# Récupérer la clé API
api_key = os.getenv("ANTHROPIC_API_KEY")
if not api_key:
    raise ValueError("La clé API ANTHROPIC_API_KEY n'est pas définie dans le fichier .env")

# Initialiser le client Claude
client = anthropic.Anthropic(api_key=api_key)

# Charger le dataset soussou-français
try:
    with open('clean_big_data_soussou_francais.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    soussou_to_french = {item["soussou"]: item["francais"] for item in data}
    french_to_soussou = {item["francais"]: item["soussou"] for item in data}
    print(f"Dataset chargé avec succès: {len(data)} entrées")
except Exception as e:
    print(f"Erreur lors du chargement du dataset: {e}")
    # Dataset minimal pour démonstration si le chargement échoue
    soussou_to_french = {
        "Tana": "Bonjour",
        "I mɛri?": "Comment vas-tu?",
        "Minden?": "Où?",
        "Munfera?": "Pourquoi?",
    }
    french_to_soussou = {v: k for k, v in soussou_to_french.items()}

# Enrichir le dictionnaire avec des mots supplémentaires
additional_words = {
    "Merci": "Tantina",
    "Au revoir": "I tanga",
    "Oui": "Iyo",
    "Non": "Ade",
    "Bien": "Fan",
    "Pays": "Bɔxi",
    "Ville": "Taa belebele",
    "Capital": "Xunyi",
    "Président": "Mangɛ",
    "Peuple": "Mixie",
    "Langue": "Xui",
    "Culture": "Namunɛ",
    "Tradition": "Namu ki",
    "Travail": "Wali",
    "École": "Xaranyi",
    "Étudiant": "Xarande",
    "Professeur": "Xaranma",
    "Livre": "Buki",
    "Eau": "Ye",
    "Nourriture": "Donse",
    "Maison": "Banxi",
}

# Mettre à jour les dictionnaires
french_to_soussou.update(additional_words)
soussou_to_french.update({v: k for k, v in additional_words.items()})

# Dictionnaire multilingue pour les questions-réponses prédéfinies
qa_pairs = {
    # Questions sur la Guinée en soussou
    "Guinée mangɛ nde ra?": {
        "french": "Le président actuel de la Guinée est le Général Mamadi Doumbouya, qui dirige le pays depuis le coup d'État de septembre 2021 en tant que président de la transition.",
        "english": "The current president of Guinea is General Mamadi Doumbouya, who has been leading the country since the coup d'état in September 2021 as the transitional president.",
        "soussou": "Guinée mangɛ na yi sàre findexi Général Mamadi Doumbouya nan na, naxan na yamare ti kabi septembre kike 2021 ɲɛ, a findexi mangɛya masarafe nan na."
    },
    "Guinée xunyi minden na?": {
        "french": "La capitale de la Guinée est Conakry, située sur la côte atlantique du pays.",
        "english": "The capital of Guinea is Conakry, located on the Atlantic coast of the country.",
        "soussou": "Guinée xunyi findexi Conakry nan na, naxan na baa dɛ ra bɔxi sɛnbɛ ma."
    },
    "Guinée xaranyi xungbe minden na?": {
        "french": "La plus grande université de Guinée est l'Université Gamal Abdel Nasser de Conakry (UGANC), fondée en 1962.",
        "english": "The largest university in Guinea is the Gamal Abdel Nasser University of Conakry (UGANC), founded in 1962.",
        "soussou": "Guinée xaranyi xungbe findexi Gamal Abdel Nasser Conakry (UGANC) nan na, naxan ti ɲɛ 1962 kui."
    },
    "Guinée xulun yeri na?": {
        "french": "La monnaie de la Guinée est le Franc Guinéen (GNF).",
        "english": "The currency of Guinea is the Guinean Franc (GNF).",
        "soussou": "Guinée xulun findexi Franc Guinéen (GNF) nan na."
    },
    "Munse Guinée rasabatixi?": {
        "french": "La Guinée a obtenu son indépendance de la France le 2 octobre 1958, sous la direction de Sékou Touré.",
        "english": "Guinea gained independence from France on October 2, 1958, under the leadership of Sékou Touré.",
        "soussou": "Guinée a xa yɛtɛ sɔtɔ Faransi bɛlɛxɛ 2 octobre 1958, Sékou Touré xa mangɛya bun ma."
    },
    "Guinée xa bɔxi xungbo di?": {
        "french": "La superficie de la Guinée est de 245 857 km².",
        "english": "The area of Guinea is 245,857 square kilometers.",
        "soussou": "Guinée xa bɔxi xungbo findexi kilomɛtiri wuli kɛmɛ firin tongo naani nun suuli kɛmɛ solomasaxan tongo suuli nun solofere (245 857 km²) nan na."
    },
    "Mixie yeri na Guinée kui?": {
        "french": "La population de la Guinée est d'environ 13,5 millions d'habitants selon les dernières estimations.",
        "english": "The population of Guinea is approximately 13.5 million according to the latest estimates.",
        "soussou": "Mixie naxan na Guinée kui findexi mixi wulu miliyɔn fu nun saxan nun a tagi (13,5 millions) nan na, xasabi dɔnxɛ ra."
    },
    "Xui mundun falama Guinée kui?": {
        "french": "La langue officielle de la Guinée est le français, mais plusieurs langues nationales sont parlées comme le soussou, le peul, le malinké, le kissi, le toma et le guerzé.",
        "english": "The official language of Guinea is French, but several national languages are spoken such as Susu, Fula, Malinke, Kissi, Toma, and Guerzé.",
        "soussou": "Guinée kui, xui xungbe findexi faransɛ nan na, kɔnɔ bɔxi xui wuyaxi fan falama alɔ soso, fula, malinke, kissi, toma, nun gerzé."
    },
    "Xure xungbe mundun kelima Guinée?": {
        "french": "Le fleuve Niger, l'un des plus importants d'Afrique, prend sa source dans les montagnes du Fouta-Djallon en Guinée.",
        "english": "The Niger River, one of Africa's most important rivers, has its source in the Fouta Djallon mountains in Guinea.",
        "soussou": "Joliba (Xure Niger), naxan findexi Afrika xure xungbe nde ra, a kelima Futa-Jallon geyae nan kui Guinée bɔxi ma."
    },
    "Manse Guinée xa kurunba kilɔn keren sɔtɔ mu?": {
        "french": "Les principales ressources naturelles de la Guinée sont la bauxite (parmi les plus grandes réserves mondiales), le fer, l'or, le diamant et d'autres minerais précieux.",
        "english": "Guinea's main natural resources are bauxite (among the world's largest reserves), iron, gold, diamonds, and other precious minerals.",
        "soussou": "Guinée xa kurunba xungbe findexi bɔxita (bauxite) nan na (naxan findexi dunia bɔxita ragata xungbe nde ra), wure, xɛma, diyaman, nun gɛmɛ tofanyi gbɛtɛe."
    },
    "Guinée dɔxɔ sɛgɛ yeri na?": {
        "french": "La Guinée est divisée en quatre régions naturelles: la Basse-Guinée (ou Guinée Maritime), la Moyenne-Guinée (Fouta-Djallon), la Haute-Guinée et la Guinée Forestière.",
        "english": "Guinea is divided into four natural regions: Lower Guinea (or Maritime Guinea), Middle Guinea (Fouta Djallon), Upper Guinea, and Forest Guinea.",
        "soussou": "Guinée bɔxi yitaxunxi dɔxɔ sɛgɛ naani nan na: Baa Guinée (xa ma Guinée Maritime), Tagi Guinée (Futa-Jallon), Kore Guinée, nun Fɔrɛti Guinée."
    },
    "Boxi mundun na Guinée rabilinma?": {
        "french": "La Guinée est entourée par six pays: la Guinée-Bissau, le Sénégal, le Mali, la Côte d'Ivoire, le Liberia et la Sierra Leone.",
        "english": "Guinea is surrounded by six countries: Guinea-Bissau, Senegal, Mali, Ivory Coast, Liberia, and Sierra Leone.",
        "soussou": "Bɔxi senni nan Guinée rabilinma: Guinée-Bissau, Senegal, Mali, Côte d'Ivoire, Liberia, nun Sierra Leone."
    },
    "Donkin yire fanyi na Guinée?": {
        "french": "Parmi les sites touristiques remarquables de Guinée, on trouve les chutes de Kinkon, le Mont Nimba (site du patrimoine mondial de l'UNESCO), les îles de Loos, le Voile de la Mariée à Kindia, et le Fouta-Djallon avec ses paysages montagneux spectaculaires.",
        "english": "Among Guinea's remarkable tourist sites are the Kinkon Falls, Mount Nimba (UNESCO World Heritage Site), the Loos Islands, the Bride's Veil in Kindia, and the Fouta Djallon with its spectacular mountainous landscapes.",
        "soussou": "Donkin yire fanyi naxee na Guinée kui: Kinkon ye birama, Nimba geya (naxan findexi UNESCO dunia kɛ barama yire nde ra), Loos surie, Ginɛ dugi dukubi Kindia, nun Futa-Jallon xa geya tofanyi."
    },
    "Guinée donma munse ma dunia kui?": {
        "french": "La Guinée est connue internationalement pour ses immenses ressources minières, particulièrement la bauxite (environ un tiers des réserves mondiales), mais aussi pour sa riche culture musicale avec des artistes comme Mory Kanté et son instrument traditionnel, la kora.",
        "english": "Guinea is internationally known for its vast mineral resources, particularly bauxite (about one-third of the world's reserves), but also for its rich musical culture with artists like Mory Kanté and the traditional kora instrument.",
        "soussou": "Guinée kolonxi dunia kui a xa bɔxi bun naafuli xungbe nan ma, gbengbenyi bɔxita (bauxite) naxan yataxi dunia bɔxita birin saxande ra, a man kolonxi a xa fare namunɛ fan ma nun a xa fare mixie alɔ Mory Kanté nun a xa kora maxase."
    },
    "Gninima mundun na Guinée xa xui xungbe ra?": {
        "french": "Les plus grands groupes ethniques de Guinée sont les Peuls (40%), les Malinkés (30%), les Soussous (20%), ainsi que plusieurs autres groupes minoritaires comme les Kissis, les Tomas et les Guerzés.",
        "english": "The largest ethnic groups in Guinea are the Fula (40%), the Malinke (30%), the Susu (20%), as well as several other minority groups such as the Kissi, Toma, and Guerzé.",
        "soussou": "Gninima xungbe naxee na Guinée xa xui ra e findexi Fulae (40%), Malinkee (30%), Sosoe (20%), nun gninima doonie gbɛtɛe alɔ Kissie, Tomae, nun Gerzée."
    },
    "Nènè munki ra?": {
        "french": "Nènè est le premier LLM open source dédié aux langues locales guinéennes, développé par une équipe de jeunes ingénieurs guinéens passionnés et visionnaires. Ce projet révolutionnaire utilise l'intelligence artificielle pour préserver et valoriser notre patrimoine linguistique. Nènè permet aux Guinéens d'interagir avec la technologie moderne dans leurs langues maternelles, facilitant ainsi l'accès au savoir et aux services numériques pour tous.",
        "english": "Nènè project is the first open-source LLM dedicated to Guinean local languages, developed by a team of passionate and visionary young Guinean engineers. This revolutionary project uses artificial intelligence to preserve and enhance our linguistic heritage. Nènè allows Guineans to interact with modern technology in their native languages, facilitating access to knowledge and digital services for all.",
        "soussou": "Nènè findexi LLM singefe nan na naxan na open source ki ma, a rafalaxi Guinée xui xungbee bɛ, gineli fonike kɔnxɛfɔrie nan a rafalaxi, e xaxili tixi yare ma. Yi wali nɛɛnɛ xungbe fatanxi xaxilima suusa nan ma, alɔɔxi won ma xui kolonya ragata nun a xa tide ite fee ma. Nènè a niyaxi Guineekae nɔma fala tide fewalafe ra sɛnbɛma se nɛɛnɛe ra e gbe xui kui, na nan a niyama birin nɔma fe kolonyie nun kɔmpita walie masɔtɔ sɔɔnɛya ra."
    }
}

# Système de traduction avancé soussou-français
def translate_soussou_to_french(text):
    # Vérifier d'abord les phrases complètes
    if text in soussou_to_french:
        return soussou_to_french[text]
    
    # Traduction par segments
    segments = re.split(r'([.!?])', text)
    translated_segments = []
    
    for segment in segments:
        if segment in ['.', '!', '?']:
            translated_segments.append(segment)
            continue
            
        segment = segment.strip()
        if not segment:
            continue
            
        if segment in soussou_to_french:
            translated_segments.append(soussou_to_french[segment])
        else:
            # Traduction mot à mot pour les segments inconnus
            words = segment.split()
            translated_words = []
            
            for word in words:
                if word in soussou_to_french:
                    translated_words.append(soussou_to_french[word])
                else:
                    translated_words.append(word)
            
            translated_segments.append(" ".join(translated_words))
    
    return "".join(translated_segments)

# Système de traduction français-soussou
def translate_french_to_soussou(text):
    # Vérifier d'abord les phrases complètes
    if text in french_to_soussou:
        return french_to_soussou[text]
    
    # Traduction par segments
    segments = re.split(r'([.!?])', text)
    translated_segments = []
    
    for segment in segments:
        if segment in ['.', '!', '?']:
            translated_segments.append(segment)
            continue
            
        segment = segment.strip()
        if not segment:
            continue
            
        if segment in french_to_soussou:
            translated_segments.append(french_to_soussou[segment])
        else:
            # Traduction mot à mot pour les segments inconnus
            words = segment.split()
            translated_words = []
            
            for word in words:
                word_lower = word.lower()
                if word_lower in french_to_soussou:
                    translated_words.append(french_to_soussou[word_lower])
                else:
                    translated_words.append(word)
            
            translated_segments.append(" ".join(translated_words))
    
    return "".join(translated_segments)

# Traitement avec Claude (version corrigée)
def process_with_claude(text, language="french", system_prompt=None):
    try:
        # Vérifier que le texte n'est pas vide
        if not text or text.strip() == "":
            # Retourner un message par défaut si le texte est vide
            if language == "english":
                return "I need more information to help you. Could you please provide more details?"
            else:
                return "J'ai besoin de plus d'informations pour vous aider. Pourriez-vous fournir plus de détails?"
        
        # Configuration du message pour Claude
        if language == "english":
            # Pour avoir des réponses en anglais
            if system_prompt:
                system_prompt += " Please respond in English."
            else:
                system_prompt = "Please respond in English."
        
        # Configuration du message pour Claude
        messages = [{"role": "user", "content": text}]
        
        # Ajouter un system prompt si fourni
        if system_prompt:
            response = client.messages.create(
                model="claude-3-7-sonnet-20250219",
                max_tokens=1000,
                system=system_prompt,
                messages=messages
            )
        else:
            response = client.messages.create(
                model="claude-3-7-sonnet-20250219",
                max_tokens=1000,
                messages=messages
            )
        
        return response.content[0].text
    except Exception as e:
        if language == "english":
            return f"Error communicating with Claude: {str(e)}"
        else:
            return f"Erreur lors de la communication avec Claude: {str(e)}"

# Fonction principale pour les questions-réponses avec effet de chargement
def multilingual_chat_with_loading(question, history, output_language):
    if not question.strip():  # Ignorer les messages vides
        return history
    
    # Créer une nouvelle copie de l'historique pour éviter de modifier l'original
    new_history = history.copy() if history else []
    
    # Ajouter la question de l'utilisateur à l'historique
    new_history.append([question, "⏳ Traitement en cours..."])
    
    # Retourner immédiatement l'historique avec le message de chargement
    return new_history

# Fonction pour traiter la réponse réelle avec support multilingue
def process_response(question, history, output_language):
    if not history:
        return history
    
    # Détecter si la question est en soussou
    is_soussou = question in qa_pairs or any(word in soussou_to_french for word in question.split())
    
    # Préparer la réponse
    response = ""
    
    # Questions prédéfinies
    if question in qa_pairs:
        if output_language == "Français":
            response = qa_pairs[question]["french"]
        elif output_language == "English":
            response = qa_pairs[question]["english"]
        elif output_language == "Soussou":
            response = qa_pairs[question]["soussou"]
    
    # Traitement pour les questions en soussou
    elif is_soussou:
        # Traduire la question en français
        french_question = translate_soussou_to_french(question)
        
        # Obtenir la réponse dans la langue demandée
        if output_language == "Français":
            system_prompt = """Tu es un assistant spécialisé dans la culture, l'histoire et la géographie de la Guinée.
            Fournis des réponses précises, complètes et actualisées. Si tu ne connais pas la réponse exacte, indique-le clairement."""
            
            response = process_with_claude(french_question, "french", system_prompt)
        elif output_language == "English":
            system_prompt = """You are an assistant specialized in the culture, history, and geography of Guinea.
            Provide accurate, complete, and up-to-date answers. If you don't know the exact answer, clearly state it."""
            
            response = process_with_claude(french_question, "english", system_prompt)
        elif output_language == "Soussou":
            # Obtenir d'abord la réponse en français puis la traduire en soussou
            system_prompt = """Tu es un assistant spécialisé dans la culture, l'histoire et la géographie de la Guinée.
            Fournis des réponses précises, complètes et actualisées. Si tu ne connais pas la réponse exacte, indique-le clairement."""
            
            french_response = process_with_claude(french_question, "french", system_prompt)
            response = translate_french_to_soussou(french_response)
    
    # Pour les questions en français ou anglais (on les passe directement à Claude)
    else:
        if output_language == "Français":
            system_prompt = """Tu es un assistant spécialisé dans la culture, l'histoire et la géographie de la Guinée.
            Fournis des réponses précises, complètes et actualisées. Si tu ne connais pas la réponse exacte, indique-le clairement."""
            response = process_with_claude(question, "french", system_prompt)
        elif output_language == "English":
            system_prompt = """You are an assistant specialized in the culture, history, and geography of Guinea.
            Provide accurate, complete, and up-to-date answers. If you don't know the exact answer, clearly state it."""
            response = process_with_claude(question, "english", system_prompt)
        elif output_language == "Soussou":
            # Obtenir la réponse en français puis la traduire en soussou
            system_prompt = """Tu es un assistant spécialisé dans la culture, l'histoire et la géographie de la Guinée.
            Fournis des réponses précises, complètes et actualisées. Si tu ne connais pas la réponse exacte, indique-le clairement."""
            french_response = process_with_claude(question, "french", system_prompt)
            response = translate_french_to_soussou(french_response)
    
    # Mettre à jour le dernier message avec la réponse
    history[-1][1] = response
    
    # Simuler un petit délai pour montrer le traitement
    time.sleep(0.5)
    
    return history

# Fonction pour ajouter une nouvelle traduction au dictionnaire
def add_translation_pair(soussou_text, french_text):
    """Ajoute une nouvelle paire de traduction au dictionnaire"""
    
    if not soussou_text or not french_text:
        return "Les deux champs doivent être remplis"
    
    # Ajouter aux dictionnaires en mémoire
    soussou_to_french[soussou_text] = french_text
    french_to_soussou[french_text] = soussou_text
    
    # Enregistrer dans un fichier JSON
    try:
        # Charger le fichier existant s'il existe
        try:
            with open('clean_big_data_soussou_francais.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            data = []
        
        # Vérifier si cette paire existe déjà
        exists = False
        for item in data:
            if item.get("soussou") == soussou_text:
                item["francais"] = french_text
                exists = True
                break
        
        # Ajouter si n'existe pas
        if not exists:
            data.append({"soussou": soussou_text, "francais": french_text})
        
        # Enregistrer dans le fichier
        with open('clean_big_data_soussou_francais.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return "Traduction ajoutée avec succès !"
    except Exception as e:
        return f"Erreur lors de l'enregistrement : {str(e)}"

# Fonction pour ajouter un caractère au texte (pour le clavier soussou)
def add_char_to_text(char, current_text):
    # Si le texte est None, initialiser à une chaîne vide
    if current_text is None:
        current_text = ""
    return current_text + char

# NOUVEAU: Fonction pour créer un clavier soussou interactif
def create_soussou_keyboard(textbox_component):
    """
    Crée un clavier soussou interactif avec des boutons pour les caractères spéciaux
    """
    # Caractères spéciaux soussous organisés par catégories
    special_chars = {
        "voyelles": ["ɛ", "ɔ", "ǝ", "ẽ", "ã"],
        "consonnes": ["ɲ", "ŋ", "ɗ", "ƴ"],
        "tons": ["́", "̀", "̂", "̌", "̄"],
        "majuscules": ["Ɛ", "Ɔ", "Ǝ", "Ɲ", "Ŋ", "Ɗ", "Ƴ"]
    }
    
    with gr.Accordion("🔤 Clavier Soussou", open=True, elem_id="soussou-keyboard") as keyboard_container:
        # Organisation en onglets pour un clavier plus compact
        with gr.Tabs() as tabs:
            # Onglet voyelles
            with gr.TabItem("Voyelles") as vowels_tab:
                with gr.Row():
                    for char in special_chars["voyelles"]:
                        btn = gr.Button(char, elem_classes=["keyboard-key", "vowel"])
                        btn.click(
                            fn=add_char_to_text,
                            inputs=[gr.Textbox(value=char, visible=False), textbox_component],
                            outputs=textbox_component
                        )
            
            # Onglet consonnes
            with gr.TabItem("Consonnes") as consonants_tab:
                with gr.Row():
                    for char in special_chars["consonnes"]:
                        btn = gr.Button(char, elem_classes=["keyboard-key", "consonant"])
                        btn.click(
                            fn=add_char_to_text, 
                            inputs=[gr.Textbox(value=char, visible=False), textbox_component],
                            outputs=textbox_component
                        )
            
            # Onglet tons et accents
            with gr.TabItem("Tons") as tones_tab:
                with gr.Row():
                    for char in special_chars["tons"]:
                        btn = gr.Button(char, elem_classes=["keyboard-key", "tone"])
                        btn.click(
                            fn=add_char_to_text,
                            inputs=[gr.Textbox(value=char, visible=False), textbox_component],
                            outputs=textbox_component
                        )
                # Guide d'utilisation des tons
                gr.Markdown("""
                **Utilisation des tons:** Tapez d'abord la voyelle, puis cliquez sur le ton.
                Exemple: pour écrire "è", tapez "e" puis cliquez sur "`̀`"
                """)
            
            # Onglet majuscules
            with gr.TabItem("Majuscules") as caps_tab:
                with gr.Row():
                    for char in special_chars["majuscules"]:
                        btn = gr.Button(char, elem_classes=["keyboard-key", "capital"])
                        btn.click(
                            fn=add_char_to_text,
                            inputs=[gr.Textbox(value=char, visible=False), textbox_component],
                            outputs=textbox_component
                        )
    
    return keyboard_container

# Fonction pour CSS personnalisé amélioré avec support pour le clavier
def modern_css():
    return """
    /* Variables de couleurs */
    :root {
        --orange-primary: #E65100;
        --orange-secondary: #FF9800;
        --orange-light: #FFB74D;
        --orange-pale: #FFF8E1;
        --dark-text: #333333;
        --medium-text: #666666;
        --light-text: #999999;
        --container-shadow: 0 10px 25px rgba(0, 0, 0, 0.08);
        --button-shadow: 0 4px 12px rgba(230, 81, 0, 0.2);
        --hover-shadow: 0 6px 15px rgba(230, 81, 0, 0.3);
    }
    
    /* Styles globaux */
    .gradio-container {
        background: linear-gradient(135deg, var(--orange-pale), #FFF);
        font-family: 'Poppins', 'Inter', 'Segoe UI', system-ui, -apple-system, sans-serif;
        max-width: 1200px;
        margin: 0 auto;
        border-radius: 20px;
        overflow: hidden;
    }
    
 /* En-tête amélioré */
    .header-container {
        background: linear-gradient(90deg, var(--orange-primary), var(--orange-secondary));
        padding: 2.5rem 1.5rem;
        text-align: center;
        position: relative;
        overflow: hidden;
        border-radius: 0 0 20px 20px;
        box-shadow: var(--container-shadow);
    }
    
    /* Effet de motif d'arrière-plan pour l'en-tête */
    .header-container::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-image: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.1'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v-4h4v2h-4v4h-2v-4h-4v2h-4v-4h4v-2H36zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2v-4h4V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
        opacity: 0.1;
    }
    
    .header-logo {
        width: 80px;
        height: 80px;
        margin: 0 auto 15px;
        filter: drop-shadow(0 4px 8px rgba(0, 0, 0, 0.2));
    }
    
    .main-title {
        font-size: 3rem;
        font-weight: 800;
        color: white;
        margin: 0;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
    }
    
    .sub-title {
        font-size: 1.2rem;
        font-weight: 500;
        color: rgba(255, 255, 255, 0.9);
        margin-top: 10px;
        max-width: 700px;
        margin-left: auto;
        margin-right: auto;
    }
    
    /* Sélecteur de langue amélioré */
    .language-selector {
        background-color: white;
        border-radius: 15px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: var(--container-shadow);
        border-left: 4px solid var(--orange-primary);
    }
    
    .language-selector label {
        font-weight: 600;
        color: var(--dark-text);
        margin-bottom: 0.5rem;
    }
    
    /* Radio boutons améliorés */
    .language-selector [data-testid="radio"] {
        display: flex;
        gap: 10px;
        flex-wrap: wrap;
    }
    
    .language-selector [data-testid="radio"] label {
        margin: 0 !important;
        padding: 0 !important;
    }
    
    .language-selector [data-testid="radio"] input {
        display: none;
    }
    
    .language-selector [data-testid="radio"] span:not(.sr-only) {
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 600;
        border-radius: 50px;
        padding: 8px 16px;
        background: #f5f5f5;
        border: 2px solid #eee;
        cursor: pointer;
        transition: all 0.3s ease;
        font-size: 0.9rem;
    }
    
    .language-selector [data-testid="radio"] input:checked + span {
        background: var(--orange-primary);
        color: white;
        border-color: var(--orange-primary);
        box-shadow: var(--button-shadow);
    }
    
    .language-selector [data-testid="radio"] span:hover {
        border-color: var(--orange-secondary);
        transform: translateY(-2px);
    }
    
    /* Section à propos */
    .about-section {
        background-color: white;
        border-radius: 20px;
        padding: 1.5rem;
        margin-top: 2rem;
        box-shadow: var(--container-shadow);
        position: relative;
        overflow: hidden;
        border: 1px solid #f0f0f0;
    }
    
    .about-section::before {
        content: '';
        position: absolute;
        top: -30px;
        right: -30px;
        width: 100px;
        height: 100px;
        border-radius: 50%;
        background: var(--orange-pale);
        opacity: 0.6;
        z-index: 0;
    }
    
    .about-section h2 {
        color: var(--orange-primary);
        border-bottom: 2px solid var(--orange-light);
        padding-bottom: 10px;
        margin-bottom: 15px;
        position: relative;
        z-index: 1;
    }
    
    .about-section p, .about-section ul {
        position: relative;
        z-index: 1;
    }
    
    /* Chatbot amélioré */
    .chatbot {
        border-radius: 20px !important;
        overflow: hidden !important;
        box-shadow: var(--container-shadow) !important;
        border: none !important;
        background-color: white !important;
        height: 500px;
    }
    
    /* Messages de l'utilisateur */
    .chatbot .user {
        background: linear-gradient(135deg, var(--orange-primary), var(--orange-secondary)) !important;
        color: white !important;
        border-radius: 18px 18px 0 18px !important;
        padding: 12px 18px !important;
        margin: 8px 0 !important;
        box-shadow: 0 3px 10px rgba(230, 81, 0, 0.15) !important;
        position: relative !important;
        max-width: 85% !important;
        margin-left: auto !important;
    }
    
    .chatbot .user::after {
        content: '';
        position: absolute;
        bottom: 0;
        right: -10px;
        width: 20px;
        height: 20px;
        background: linear-gradient(135deg, var(--orange-primary), var(--orange-secondary)) !important;
        clip-path: polygon(0 100%, 100% 0, 100% 100%);
    }
    
    /* Messages du bot */
    .chatbot .bot {
        background-color: #F5F5F5 !important;
        color: var(--dark-text) !important;
        border-radius: 18px 18px 18px 0 !important;
        padding: 12px 18px !important;
        margin: 8px 0 !important;
        box-shadow: 0 3px 10px rgba(0, 0, 0, 0.05) !important;
        position: relative !important;
        max-width: 85% !important;
    }
    
    .chatbot .bot::after {
        content: '';
        position: absolute;
        bottom: 0;
        left: -10px;
        width: 20px;
        height: 20px;
        background-color: #F5F5F5 !important;
        clip-path: polygon(0 0, 100% 100%, 0 100%);
    }
    
    /* Pied de page */
    .footer {
        text-align: center;
        font-size: 0.9rem;
        margin-top: 2rem;
        padding: 1.5rem;
        border-top: 1px solid #FFCCBC;
        color: var(--medium-text);
    }
    
    /* Boutons améliorés */
    .primary-button {
        background: linear-gradient(135deg, var(--orange-primary), var(--orange-secondary)) !important;
        color: white !important;
        border-radius: 50px !important;
        padding: 10px 20px !important;
        font-weight: 600 !important;
        border: none !important;
        transition: all 0.3s ease !important;
        box-shadow: var(--button-shadow) !important;
    }
    
    .primary-button:hover {
        background: linear-gradient(135deg, var(--orange-secondary), var(--orange-primary)) !important;
        transform: translateY(-2px) !important;
        box-shadow: var(--hover-shadow) !important;
    }
    
    .primary-button:active {
        transform: translateY(0) !important;
    }
    
    .secondary-button {
        background-color: #F5F5F5 !important;
        color: var(--medium-text) !important;
        border-radius: 50px !important;
        padding: 10px 20px !important;
        font-weight: 600 !important;
        border: 1px solid #E0E0E0 !important;
        transition: all 0.3s ease !important;
    }
    
    .secondary-button:hover {
        background-color: white !important;
        color: var(--orange-primary) !important;
        border-color: var(--orange-light) !important;
        transform: translateY(-2px) !important;
    }
    
    /* Animations */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .fade-in {
        animation: fadeIn 0.5s ease-out forwards !important;
    }
    
    /* Zone de texte améliorée */
    .input-textbox {
        border-radius: 15px !important;
        border: 2px solid #EEEEEE !important;
        padding: 12px 18px !important;
        transition: all 0.3s ease !important;
        background-color: white !important;
        font-family: 'Poppins', 'Inter', 'Segoe UI', sans-serif !important;
        font-size: 0.95rem !important;
    }
    
    .input-textbox:focus {
        border-color: var(--orange-secondary) !important;
        box-shadow: 0 0 0 3px rgba(255, 152, 0, 0.2) !important;
    }
    
    /* Onglet Traduction */
    .translation-container {
        background-color: white;
        border-radius: 20px;
        padding: 1.5rem;
        box-shadow: var(--container-shadow);
        border: 1px solid #f0f0f0;
    }
    
    .translation-container h3 {
        color: var(--orange-primary);
        margin-bottom: 1.5rem;
        font-weight: 700;
        border-left: 4px solid var(--orange-secondary);
        padding-left: 10px;
    }
    
    .output-textbox {
        border-radius: 15px !important;
        border: 2px solid #E6E6E6 !important;
        background-color: #FAFAFA !important;
    }
    
    /* Styles pour le clavier soussou */
    #soussou-keyboard {
        margin-top: 10px;
        margin-bottom: 15px;
        border-radius: 15px;
        overflow: hidden;
        border: 1px solid #EEEEEE;
        background-color: white;
    }
    
    #soussou-keyboard .accordion-button {
        background-color: #FFF3E0 !important;
        font-weight: 600 !important;
        color: var(--orange-primary) !important;
        border-bottom: 1px solid #FFE0B2;
    }
    
    #soussou-keyboard .tab-nav {
        border-bottom: 1px solid #FFE0B2 !important;
        background-color: #FFFAF1 !important;
        padding: 5px 10px 0 !important;
    }
    
    #soussou-keyboard .tab-nav button {
        font-size: 0.8rem !important;
        padding: 5px 12px !important;
        border-radius: 5px 5px 0 0 !important;
        background-color: #FFF8E1 !important;
        border: 1px solid #FFE0B2 !important;
        border-bottom: none !important;
        margin-right: 3px !important;
        color: var(--medium-text) !important;
    }
    
    #soussou-keyboard .tab-nav button.selected {
        background-color: white !important;
        color: var(--orange-primary) !important;
        font-weight: 600 !important;
    }
    
    .keyboard-key {
        min-width: 40px !important;
        height: 40px !important;
        margin: 5px !important;
        background-color: white !important;
        border: 1px solid #EEEEEE !important;
        border-radius: 8px !important;
        font-size: 1.2rem !important;
        transition: all 0.2s ease-in-out !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05) !important;
    }
    
    .keyboard-key:hover {
        background-color: #FFF3E0 !important;
        border-color: var(--orange-light) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1) !important;
        color: var(--orange-primary) !important;
    }
    
    .keyboard-key.vowel {
        background-color: #FFF8E1 !important;
        border-color: #FFECB3 !important;
    }
    
    .keyboard-key.consonant {
        background-color: #FFF3E0 !important;
        border-color: #FFE0B2 !important;
    }
    
    .keyboard-key.tone {
        background-color: #FFFDE7 !important;
        border-color: #FFF9C4 !important;
        font-family: Arial, sans-serif !important;
    }
    
    .keyboard-key.capital {
        font-weight: bold !important;
        background-color: #E8F5E9 !important;
        border-color: #C8E6C9 !important;
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
        .main-title {
            font-size: 2.5rem;
        }
        
        .header-logo {
            width: 60px;
            height: 60px;
        }
        
        .chatbot {
            height: 400px;
        }
        
        .language-selector [data-testid="radio"] {
            justify-content: center;
        }
    }
    
    @media (max-width: 480px) {
        .main-title {
            font-size: 2rem;
        }
        
        .sub-title {
            font-size: 1rem;
        }
        
        .keyboard-key {
            min-width: 36px !important;
            height: 36px !important;
            font-size: 1rem !important;
            margin: 3px !important;
        }
    }
    """

# Obtenir le logo et l'en-tête HTML améliorés
def get_html_elements():
    # Logo SVG pour Nènè amélioré
    nene_logo = """
    <svg width="100" height="100" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
        <defs>
            <linearGradient id="orangeGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stop-color="#E65100" />
                <stop offset="100%" stop-color="#FF9800" />
            </linearGradient>
            <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
                <feGaussianBlur in="SourceAlpha" stdDeviation="3" />
                <feOffset dx="0" dy="2" result="offsetblur" />
                <feComponentTransfer>
                    <feFuncA type="linear" slope="0.5" />
                </feComponentTransfer>
                <feMerge>
                    <feMergeNode />
                    <feMergeNode in="SourceGraphic" />
                </feMerge>
            </filter>
        </defs>

        <!-- Cercle principal -->
        <circle cx="50" cy="50" r="45" fill="url(#orangeGradient)" filter="url(#shadow)" />

        <!-- Cercles concentriques décoratifs -->
        <circle cx="50" cy="50" r="35" fill="none" stroke="#FFF" stroke-width="2" stroke-opacity="0.5" />
        <circle cx="50" cy="50" r="25" fill="none" stroke="#FFF" stroke-width="1.5" stroke-opacity="0.3" />

        <!-- Motif africain stylisé -->
        <path d="M50,20 C65,20 75,35 75,50 C75,65 65,80 50,80 C35,80 25,65 25,50 C25,35 35,20 50,20 Z"
              fill="none" stroke="#FFFFFF" stroke-width="1.5" stroke-dasharray="3,2" stroke-opacity="0.6" />

        <!-- Élément linguistique (suggestion de dialogue) -->
        <path d="M65,40 A20,20 0 0,1 60,65 L60,70 L50,60 A20,20 0 1,1 65,40 Z"
              fill="#FFFFFF" fill-opacity="0.15" />

        <!-- Lettres stylisées -->
        <text x="50" y="54" font-family="Arial" font-size="16" font-weight="bold" fill="#FFFFFF"
              text-anchor="middle" filter="url(#shadow)">NÈNÈ</text>
    </svg>
    """

    # Header avec style moderne et amélioré
    header_html = f"""
    <div class="header-container">
        <div class="header-logo">
            {nene_logo}
        </div>
        <h1 class="main-title">Nènè</h1>
        <p class="sub-title">Premier modèle de langage dédié aux langues locales guinéennes</p>
        
        <!-- Badge flottant -->
        <div style="
            position: absolute;
            top: 15px;
            right: 15px;
            background-color: white;
            color: #E65100;
            font-size: 0.8rem;
            font-weight: 700;
            padding: 5px 12px;
            border-radius: 50px;
            box-shadow: 0 3px 10px rgba(0,0,0,0.1);
        ">
            Beta 1.0
        </div>
    </div>
    """

    # Footer avec infos et crédits amélioré
    footer_html = """
    <div class="footer">
        <div style="display: flex; justify-content: center; margin-bottom: 10px;">
            <div style="height: 3px; width: 60px; background: linear-gradient(90deg, #E65100, #FF9800);"></div>
        </div>
        <p>Développé avec <span style="color: #E65100;">❤️</span> en Guinée | Designed with ❤️ in Guinea • 2025</p>
        <p style="font-size: 0.9rem; font-weight: 600;">TechMinds Africa</p>
        <p style="font-size: 0.8rem; color: #999;">Préservation linguistique • Inclusion numérique • Innovation</p>
    </div>
    """

    return header_html, footer_html

# Interface Gradio améliorée avec onglets et clavier soussou intégré
with gr.Blocks(css=modern_css(), theme=gr.themes.Soft(primary_hue="orange"), title="Projet Nènè - Premier LLM pour les langues guinéennes") as demo:
    
    # En-tête avec style personnalisé amélioré
    header_html, footer_html = get_html_elements()
    gr.HTML(header_html)
    
    # Interface avec onglets
    with gr.Tabs():
        # Onglet Chat
        with gr.TabItem("💬 Chat"):
            # Sélecteur de langue de sortie
            with gr.Row(elem_classes=["language-selector"]):
                output_language = gr.Radio(
                    ["Français", "English", "Soussou"],
                    value="Français",
                    label="Langue de réponse / Answer language",
                    info="Sélectionnez la langue dans laquelle vous souhaitez recevoir les réponses / Select the language in which you want to receive answers"
                )
            
            # Interface de chat
            chatbot = gr.Chatbot(
                elem_classes=["chatbot"],
                show_label=False,
                height=500,
                show_copy_button=True,
                avatar_images=("https://i.ibb.co/wYYhh5M/user-icon.png", "https://i.ibb.co/vdKN1V3/nene-avatar.png"),
            )
            
            # Champ de texte et clavier soussou intégré
            msg = gr.Textbox(
                placeholder="Posez votre question en soussou, français ou anglais...",
                show_label=False,
                elem_classes=["input-textbox"],
                lines=2
            )
            
            # Création du clavier soussou intégré
            create_soussou_keyboard(msg)
            
            with gr.Row():
                submit_btn = gr.Button("Envoyer / Send", variant="primary", elem_classes=["primary-button"])
                clear_btn = gr.Button("Effacer / Clear", elem_classes=["secondary-button"])
            
            # Exemples de questions
            gr.Examples(
                examples=[
                    "Tana",
                    "I mɛri?",
                    "Guinée xunyi minden na?",
                    "Nènè munki ra?",
                    "Mixie yeri na Guinée kui?"
                ],
                inputs=msg,
                label="Exemples de questions en soussou"
            )
            
        # Onglet Traduction
        with gr.TabItem("🔄 Traduction"):
            with gr.Column(elem_classes=["translation-container"]):
                gr.Markdown("### Traduction Soussou-Français / Français-Soussou")
                
                with gr.Row():
                    source_lang = gr.Dropdown(
                        ["Soussou", "Français"],
                        value="Soussou",
                        label="Langue source"
                    )
                    target_lang = gr.Dropdown(
                        ["Français", "Soussou"],
                        value="Français",
                        label="Langue cible"
                    )
                
                # Entrée de texte à traduire avec clavier soussou
                source_text = gr.Textbox(
                    lines=5,
                    placeholder="Entrez le texte à traduire...",
                    label="Texte source",
                    elem_classes=["input-textbox"]
                )
                
                # Ajout du clavier soussou pour l'onglet traduction
                create_soussou_keyboard(source_text)
                
                # Boutons de traduction
                with gr.Row():
                    translate_btn = gr.Button("Traduire", variant="primary", elem_classes=["primary-button"])
                    swap_btn = gr.Button("🔄 Échanger les langues", elem_classes=["secondary-button"])
                
                # Résultat de la traduction
                translated_text = gr.Textbox(
                    lines=5,
                    label="Traduction",
                    elem_classes=["output-textbox"]
                )
                
                # Fonction de traduction pour l'interface
                def perform_translation(text, source, target):
                    if not text.strip():
                        return "Veuillez entrer un texte à traduire"
                    
                    if source == "Soussou" and target == "Français":
                        return translate_soussou_to_french(text)
                    elif source == "Français" and target == "Soussou":
                        return translate_french_to_soussou(text)
                    else:
                        return text  # Même langue, retourner le texte original
                
                # Fonction pour échanger les langues
                def swap_languages(src, tgt):
                    return tgt, src
                
                # Connexion des boutons
                translate_btn.click(
                    fn=perform_translation,
                    inputs=[source_text, source_lang, target_lang],
                    outputs=translated_text
                )
                
                swap_btn.click(
                    fn=swap_languages,
                    inputs=[source_lang, target_lang],
                    outputs=[source_lang, target_lang]
                )
                
                # Exemples de traduction
                gr.Examples(
                    examples=[
                        ["Tana", "Soussou", "Français"],
                        ["Bonjour", "Français", "Soussou"],
                        ["I mɛri?", "Soussou", "Français"],
                        ["Comment vas-tu?", "Français", "Soussou"]
                    ],
                    inputs=[source_text, source_lang, target_lang],
                    outputs=translated_text,
                    fn=perform_translation,
                    label="Exemples de traduction"
                )
        
        # Onglet Contribution
        with gr.TabItem("👥 Contribuer"):
            with gr.Column(elem_classes=["translation-container"]):
                gr.Markdown("### Enrichir le dictionnaire Soussou-Français")
                gr.Markdown("Aidez-nous à améliorer notre traducteur en ajoutant de nouveaux mots ou expressions")
                
                # Formulaire de contribution avec clavier soussou
                with gr.Row():
                    new_soussou = gr.Textbox(
                        placeholder="Mot ou phrase en soussou",
                        label="Soussou",
                        elem_classes=["input-textbox"]
                    )
                    new_french = gr.Textbox(
                        placeholder="Équivalent en français",
                        label="Français",
                        elem_classes=["input-textbox"]
                    )
                
                # Ajout du clavier soussou pour l'onglet contribution également
                create_soussou_keyboard(new_soussou)
                
                add_btn = gr.Button("Ajouter cette traduction", variant="primary", elem_classes=["primary-button"])
                result_msg = gr.Textbox(label="Résultat", interactive=False)
                
                # Connexion du bouton d'ajout
                add_btn.click(
                    fn=add_translation_pair,
                    inputs=[new_soussou, new_french],
                    outputs=result_msg
                )
                
                gr.Markdown("""
                #### Pourquoi contribuer?
                
                En enrichissant notre dictionnaire de traduction, vous aidez à:
                - **Préserver** le patrimoine linguistique guinéen
                - **Améliorer** la qualité des traductions automatiques
                - **Rendre** la technologie plus accessible dans les langues locales
                
                Merci pour votre contribution! 🙏
                """)
    
    # Section à propos améliorée
    with gr.Accordion("À propos du projet Nènè", open=False, elem_classes=["about-section"]):
        gr.Markdown("""
        ## Le projet Nènè
        
        Nènè est le **premier modèle de langage dédié aux langues locales guinéennes**, développé par une équipe de jeunes ingénieurs passionnés et visionnaires.
        
        Ce projet révolutionnaire utilise l'intelligence artificielle pour préserver et valoriser notre patrimoine linguistique. Nènè permet aux Guinéens d'interagir avec la technologie moderne dans leurs langues maternelles, facilitant ainsi l'accès au savoir et aux services numériques pour tous.
        
        ### Fonctionnalités
        
        - **Traduction** entre le soussou et le français
        - **Réponses à des questions** sur la Guinée, son histoire et sa culture
        - **Interface multilingue** avec support du soussou, du français et de l'anglais
        - **IA conversationnelle** adaptée aux contextes culturels guinéens
        
        ### Objectifs
        
        - Préserver et valoriser les langues locales guinéennes
        - Faciliter la communication et l'accès à l'information
        - Offrir des solutions adaptées aux entreprises et institutions locales
        - Réduire la fracture numérique et promouvoir l'inclusion
        
        ### Rejoignez-nous !
        
        Participez à cette aventure technologique et culturelle en nous contactant:
        mamadou-moussa.bangoura@techmindsafrica.net
        """)
    
    # Pied de page amélioré
    gr.HTML(footer_html)
    
    # Fonction en deux étapes pour montrer l'animation de chargement
    def submit_workflow(message, chat_history, language):
        if not message.strip():
            return chat_history, message
        
        # Étape 1: Ajouter le message à l'historique avec indication de chargement
        history = multilingual_chat_with_loading(message, chat_history, language)
        
        # Étape 2: Traiter la réponse réelle
        processed_history = process_response(message, history, language)
        
        return processed_history, ""
    
    # Connexion des boutons de chat
    submit_btn.click(
        fn=submit_workflow,
        inputs=[msg, chatbot, output_language],
        outputs=[chatbot, msg],
        api_name="submit"
    )
    
    msg.submit(
        fn=submit_workflow,
        inputs=[msg, chatbot, output_language],
        outputs=[chatbot, msg]
    )
    
    clear_btn.click(lambda: None, None, chatbot, queue=False)

# Lancer l'application
if __name__ == "__main__":
    demo.launch(share=True)