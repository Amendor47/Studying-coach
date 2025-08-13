import spacy

nlp = spacy.load("fr_core_news_sm") # modèle français

def advanced_analyze(text):
    doc = nlp(text)
    themes = {}
    for sent in doc.sents:
        # Détecter concept clé, définition, exemple, relation
        keywords = [token.text for token in sent if token.is_alpha and not token.is_stop]
        theme = "Général"
        if keywords:
            theme = keywords[0] # exemple simple, à raffiner
        if theme not in themes:
            themes[theme] = []
        themes[theme].append({
            "front": sent.text[:200],
            "back": sent.text,
            "type": "QA"
        })
    return themes