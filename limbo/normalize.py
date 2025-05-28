import unicodedata
import re

def normalize_string(text):
    """Normaliza uma string: substitui acentos por caracteres base (preservando maiúsculas/minúsculas)
       e substitui espaços/não alfanuméricos por underscore."""
    
    if not text:
        return text
    try:
        text_str = str(text)
        # Transliterar acentos para caracteres base (e.g., á -> a, Ç -> C)
        # NFKD decompõe caracteres como 'ç' em 'c' e um acento combinatório.
        nfkd_form = unicodedata.normalize('NFKD', text_str)
        # Remove os acentos combinatórios, preservando a letra base e sua caixa.
        sem_acentos = "".join([c for c in nfkd_form if not unicodedata.combining(c)])
        # Substituir espaços e outros caracteres não alfanuméricos (exceto underscore) por underscore
        # O padrão \W corresponde a qualquer caractere que não seja letra, número ou underscore.
        # Aplicamos isso na string já sem acentos, mas com a caixa original preservada.
        normalized = re.sub(r'\W+', '_', sem_acentos)
        # Remover underscores múltiplos que podem ter sido criados
        normalized = re.sub(r'_+', '_', normalized)
        # Remover underscores no início ou fim, se houver
        normalized = normalized.strip('_')
        # Caso a string fique vazia (ex: só tinha caracteres não alfanuméricos), retorna um fallback.
        # Este fallback ainda usa lower() por simplicidade, mas a lógica principal preserva a caixa.
        if not normalized:
             normalized = re.sub(r'\s+', '_', text_str.lower()).strip('_') # Fallback simples
             if not normalized:
                 # Se ainda vazio, retorna um valor genérico para evitar string vazia
                 return "string_normalizada_fallback"
        return normalized
    except Exception as e:
        print(f"Erro ao normalizar string '{text}': {e}")
        # Em caso de erro inesperado, retorna uma versão simplificada (minúscula, espaços por _)
        return re.sub(r'\s+', '_', str(text).lower()).strip('_')
