import json
import requests

def load_config(file_path):
    """Carica il file di configurazione JSON."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def build_query(illegal_words, common_words, legal_words):
    """Costruisce la query di ricerca combinando le parole."""
    # Combina le parole illegali e comuni con operatori AND
    base_query = ' AND '.join(f'"{word}"' for word in illegal_words + common_words)
    # Esclude le parole legali usando l'operatore NOT (-)
    if legal_words:
        exclude_query = ' '.join(f'-"{word}"' for word in legal_words)
        query = f'{base_query} {exclude_query}'
    else:
        query = base_query
    return query

def filter_urls(urls, good_websites, bad_websites):
    """Filtra gli URL eliminando quelli presenti nelle liste di siti da ignorare."""
    filtered_urls = []
    for url in urls:
        if not any(site in url for site in good_websites + bad_websites):
            filtered_urls.append(url)
    return filtered_urls

def save_results(file_path, urls):
    """Salva gli URL risultati in un file di testo."""
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(f"{url}\n" for url in urls)

def bing_web_search(config_path, output_file, subscription_key):
    """Esegue una ricerca utilizzando l'API di Ricerca Web di Bing."""
    config = load_config(config_path)
    
    # Estrai le liste dal file di configurazione
    illegal_words = config.get('dorking', {}).get('illegal_words', [])
    legal_words = config.get('dorking', {}).get('legal_words', [])
    common_words = config.get('dorking', {}).get('common_words', [])
    good_websites = config.get('dorking', {}).get('good_websites', [])
    bad_websites = config.get('dorking', {}).get('bad_websites', [])
    
    if not illegal_words or not common_words:
        print("Le liste 'illegal_words' e 'common_words' devono essere riempite.")
        return

    # Costruisci la query di ricerca
    query = build_query(illegal_words, common_words, legal_words)
    print(f"Eseguo la ricerca con la query: {query}")

    # Imposta la richiesta utilizzando le tue chiavi e l'endpoint
    endpoint = 'https://api.bing.microsoft.com/v7.0/search'

    headers = {"Ocp-Apim-Subscription-Key": subscription_key}
    params = {
        "q": query,
        "textDecorations": True,
        "textFormat": "HTML",
        "count": 50,  # Numero di risultati per pagina (massimo 50)
        # Aggiungi altri parametri se necessario, consultando la documentazione
    }

    # Esegui la ricerca
    try:
        response = requests.get(endpoint, headers=headers, params=params)
        response.raise_for_status()
        search_results = response.json()
        items = search_results.get('webPages', {}).get('value', [])
        results = [item.get('url') for item in items]
    except Exception as e:
        print(f"Si è verificato un errore: {e}")
        return

    # Filtra gli URL
    filtered_results = filter_urls(results, good_websites, bad_websites)

    # Salva i risultati nel file di output
    save_results(output_file, filtered_results)
    print(f"Risultati salvati in: {output_file}")

# Specifica il percorso del file di configurazione e del file di output
config_path = 'config.json'
output_file = 'results.txt'
subscription_key = '1550055c1c98450a96bff18e5aceb499'  # Sostituisci con la tua Key

# Esegui lo script
bing_web_search(config_path, output_file, subscription_key)
