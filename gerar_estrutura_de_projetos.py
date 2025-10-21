# import os


# # Caminho raiz do seu projeto
# raiz = "."  # "." significa a pasta atual

# # Extensões que queremos mostrar
# extensoes_permitidas = [".py", ".html"]

# # Pastas que queremos ignorar
# pastas_ignorar = {"__pycache__", "venv", "node_modules", ".git"}

# def mostrar_estrutura(raiz, prefix=""):
#     for item in sorted(os.listdir(raiz)):
#         caminho_completo = os.path.join(raiz, item)

#         if os.path.isdir(caminho_completo):
#             if item in pastas_ignorar:
#                 continue
#             print(f"{prefix}{item}/")
#             mostrar_estrutura(caminho_completo, prefix + "    ")
#         elif os.path.isfile(caminho_completo):
#             if any(item.endswith(ext) for ext in extensoes_permitidas):
#                 print(f"{prefix}{item}")

# # Executa
# print("Estrutura do projeto:")
# mostrar_estrutura(raiz)


import os

# Caminho raiz do seu projeto
raiz = "."  # "." significa a pasta atual

# Extensões que queremos mostrar
extensoes_permitidas = [".py", ".html"]

# Pastas que queremos ignorar
pastas_ignorar = {"__pycache__", "venv", "node_modules", ".git", ".venv"} # <--- Adicionado .venv

def mostrar_estrutura(raiz, prefix=""):
    for item in sorted(os.listdir(raiz)):
        caminho_completo = os.path.join(raiz, item)

        if os.path.isdir(caminho_completo):
            if item in pastas_ignorar:
                continue
            print(f"{prefix}{item}/")
            mostrar_estrutura(caminho_completo, prefix + "    ")
        elif os.path.isfile(caminho_completo):
            if any(item.endswith(ext) for ext in extensoes_permitidas):
                print(f"{prefix}{item}")

# Executa
print("Estrutura do projeto:")
mostrar_estrutura(raiz)