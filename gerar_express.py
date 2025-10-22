import os

# Estrutura de diretórios do projeto Express
estrutura = {
    "projeto_express": [
        "routes",
        "views",
        "public/css",
        "public/js",
        "scripts"
    ]
}

# Arquivos iniciais com conteúdo padrão (ou vazio)
arquivos = {
    "projeto_express/app.js": """\
import express from "express";
import dotenv from "dotenv";
import path from "path";
import { fileURLToPath } from "url";

dotenv.config();
const app = express();
const PORT = process.env.PORT || 3000;

// Configuração de caminhos
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Configuração do EJS e pasta pública
app.set("view engine", "ejs");
app.set("views", path.join(__dirname, "views"));
app.use(express.static(path.join(__dirname, "public")));
app.use(express.urlencoded({ extended: true }));

// Rotas
import indexRoutes from "./routes/index.js";
app.use("/", indexRoutes);

app.listen(PORT, () => {
  console.log(`Servidor rodando na porta ${PORT}`);
});
""",

    "projeto_express/routes/index.js": """\
import express from "express";
const router = express.Router();

router.get("/", (req, res) => {
  res.render("index", { title: "Página Inicial" });
});

export default router;
""",

    "projeto_express/views/index.ejs": """\
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title><%= title %></title>
    <link rel="stylesheet" href="/css/style.css">
</head>
<body>
    <h1><%= title %></h1>
    <p>Bem-vindo ao seu novo projeto Express.js!</p>
</body>
</html>
""",

    "projeto_express/public/css/style.css": """\
body {
    font-family: Arial, sans-serif;
    margin: 40px;
    background-color: #f8f9fa;
    color: #333;
}
h1 {
    color: #007bff;
}
""",

    "projeto_express/db.js": """\
import pkg from "pg";
import dotenv from "dotenv";
dotenv.config();

const { Pool } = pkg;

export const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: { rejectUnauthorized: false }
});
""",

    "projeto_express/.env": """\
DATABASE_URL=postgresql://usuario:senha@host:5432/postgres
PORT=3000
""",

    "projeto_express/package.json": """\
{
  "name": "projeto_express",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "start": "node app.js"
  },
  "dependencies": {
    "dotenv": "^16.0.0",
    "ejs": "^3.1.9",
    "express": "^4.19.0",
    "pg": "^8.11.1"
  }
}
"""
}

# Criação das pastas e arquivos
for pasta, subpastas in estrutura.items():
    for sub in subpastas:
        os.makedirs(os.path.join(pasta, sub), exist_ok=True)

for caminho, conteudo in arquivos.items():
    with open(caminho, "w", encoding="utf-8") as f:
        f.write(conteudo)

print("✅ Estrutura do projeto Express.js criada com sucesso!")
print("📂 Diretório: ./projeto_express")
