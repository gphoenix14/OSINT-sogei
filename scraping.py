import os
import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from collections import Counter
import re

def load_config(file_path):
    """Carica il file di configurazione JSON."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def read_results(file_path):
    """Legge gli URL dal file results.txt."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip()]

def sanitize_folder_name(name):
    """Sanitizza il nome della cartella sostituendo caratteri illegali."""
    sanitized_name = "".join(c if c.isalnum() or c in (' ', '.', '_', '-') else '-' for c in name)
    return sanitized_name.strip('-')

def create_folder(folder_path):
    """Crea una cartella se non esiste."""
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

def extract_images(soup, base_url, images_directory):
    """Estrae e scarica le immagini dalla pagina."""
    image_tags = soup.find_all('img')
    if not os.path.exists(images_directory):
        os.makedirs(images_directory)
    for img_tag in image_tags:
        img_url = img_tag.get('src')
        if img_url:
            # Gestisce gli URL relativi
            img_url = requests.compat.urljoin(base_url, img_url)
            img_name = os.path.basename(urlparse(img_url).path)
            img_path = os.path.join(images_directory, img_name)
            try:
                img_response = requests.get(img_url, timeout=10)
                img_response.raise_for_status()
                with open(img_path, 'wb') as f:
                    f.write(img_response.content)
                print(f"Immagine scaricata: {img_url}")
            except Exception as e:
                print(f"Errore nel download dell'immagine {img_url}: {e}")

def extract_keywords(soup, keywords_file):
    """Estrae le parole chiave dalla pagina e le salva."""
    # Tenta di estrarre dai meta tag
    meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
    if meta_keywords and meta_keywords.get('content'):
        keywords = meta_keywords['content']
    else:
        # Metodo alternativo: estrai le parole più frequenti dal testo
        text = soup.get_text()
        words = [word.lower() for word in text.split() if word.isalpha()]
        word_counts = Counter(words)
        common_words = [word for word, count in word_counts.most_common(10)]
        keywords = ', '.join(common_words)
    # Salva le parole chiave nel file
    with open(keywords_file, 'w', encoding='utf-8') as f:
        f.write(keywords)
    print(f"Parole chiave estratte e salvate in {keywords_file}")

def extract_urls(soup, url_file):
    """Estrae tutti gli URL dalla pagina e li salva in un unico file."""
    urls = set()

    # Estrae gli URL dai tag 'a'
    for link in soup.find_all('a', href=True):
        href = link['href']
        # Gestisce gli URL relativi
        full_url = requests.compat.urljoin(soup.base_url, href)
        urls.add(full_url)

    # Estrae gli URL dal testo che iniziano con http o https
    text = soup.get_text()
    found_urls = re.findall(r'(https?://\S+)', text)
    urls.update(found_urls)

    # Salva tutti gli URL in un unico file
    with open(url_file, 'w', encoding='utf-8') as f:
        for extracted_url in urls:
            f.write(f"{extracted_url}\n")
    print(f"URL estratti e salvati in {url_file}")

def main():
    # Carica la configurazione
    config = load_config('config.json')
    parameters = config.get('scraping', {}).get('parameters', {})
    images_subdir = config.get('scraping', {}).get('images_directory', 'images')
    keywords_filename = config.get('scraping', {}).get('keywords_file', 'keywords.txt')
    url_filename = config.get('scraping', {}).get('url_file', 'url.txt')
    data_directory = config.get('scraping', {}).get('data_directory', 'data')

    # Assicura che la directory dei dati esista
    create_folder(data_directory)
    
    # Legge gli URL
    urls = read_results('results.txt')
    
    for url in urls:
        print(f"Processando l'URL: {url}")
        # Analizza l'URL per ottenere dominio e percorso
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        path = parsed_url.path
        # Crea il nome della cartella
        folder_name = sanitize_folder_name(domain + path.replace('/', '-'))
        site_folder_path = os.path.join(data_directory, folder_name)
        create_folder(site_folder_path)
        
        # Inizializza l'oggetto BeautifulSoup
        if any(parameters.get(param, False) for param in ['images', 'keywords', 'url']):
            try:
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                page_content = response.content
                soup = BeautifulSoup(page_content, 'html.parser')
                soup.base_url = url  # Imposta l'URL base per gestire gli URL relativi
            except Exception as e:
                print(f"Errore nell'accesso a {url}: {e}")
                continue  # Salta all'URL successivo se si verifica un errore
        
        # Estrae le immagini
        if parameters.get('images', False):
            images_directory = os.path.join(site_folder_path, images_subdir)
            extract_images(soup, url, images_directory)
        
        # Estrae le parole chiave
        if parameters.get('keywords', False):
            keywords_file = os.path.join(site_folder_path, keywords_filename)
            extract_keywords(soup, keywords_file)
        
        # Estrae e salva gli URL
        if parameters.get('url', False):
            url_file = os.path.join(site_folder_path, url_filename)
            extract_urls(soup, url_file)

if __name__ == "__main__":
    main()
