# 🚀 Criando Sua Primeira Landing Page com Flask e Tailwind CSS

Bem-vindo! Este é um guia passo a passo, estilo aula, para você criar sua primeira aplicação web full-stack. Vamos construir uma **Landing Page de Captura de Leads** moderna, responsiva e funcional.

## 📚 O Que Você Vai Aprender

Neste projeto, você aprenderá:
- ✅ Como configurar um ambiente Python isolado
- ✅ Como criar um servidor web com **Flask** (backend)
- ✅ Como estruturar pastas de forma profissional
- ✅ Como criar interfaces modernas com **Tailwind CSS** (frontend)
- ✅ Como processar dados de formulários
- ✅ Boas práticas de desenvolvimento web

---

## 🛠️ Pré-requisitos

Antes de começar, certifique-se de ter instalado:
- **Python 3.8 ou superior** ([Baixe aqui](https://www.python.org/downloads/))
- Um editor de código (recomendamos o [VS Code](https://code.visualstudio.com/))
- Noções básicas de terminal/command line

---

## 📁 Estrutura do Projeto

Nosso projeto terá a seguinte organização:

```
meu-projeto/
├── app.py              # Cérebro da aplicação (Backend Python)
├── templates/
│   └── index.html      # Cara da aplicação (Frontend HTML)
├── static/             # Pasta para arquivos estáticos (CSS, JS, imagens)
├── venv/               # Ambiente virtual (criado automaticamente)
└── README.md           # Este arquivo
```

---

## 👣 Passo a Passo

### Passo 1: Preparando o Ambiente

Primeiro, vamos criar um "quarto isolado" para nosso projeto, chamado **ambiente virtual**. Isso evita que as bibliotecas que instalarmos interfiram em outros projetos Python.

Abra seu terminal na pasta onde quer criar o projeto e execute:

#### 1.1 Criar o ambiente virtual
```bash
python -m venv venv
```

#### 1.2 Ativar o ambiente virtual

**No Windows:**
```bash
venv\Scripts\activate
```

**No Linux/Mac:**
```bash
source venv/bin/activate
```

✅ **Dica:** Quando o ambiente estiver ativo, você verá `(venv)` no início da linha do comando.

#### 1.3 Instalar o Flask
Com o ambiente ativado, instale o Flask (nosso framework web):

```bash
pip install flask
```

---

### Passo 2: Criando a Estrutura de Pastas

Crie as seguintes pastas e arquivos vazios:

```bash
mkdir templates
mkdir static
```

Ou crie manualmente pelo seu editor de código. Os arquivos `app.py` e `templates/index.html` já devem existir neste repositório.

---

### Passo 3: Construindo o Backend (app.py)

O **Flask** é um micro-framework Python que nos permite criar servidores web de forma simples. Ele vai:
1. Escutar requisições do navegador
2. Entregar nossa página HTML
3. Processar os dados do formulário

O arquivo `app.py` já está criado com o seguinte código:

```python
from flask import Flask, render_template, request, redirect, url_for

# Cria a aplicação Flask
# __name__ ajuda o Flask a localizar arquivos relativos
app = Flask(__name__)

# Rota 1: Página Inicial (GET)
# Quando alguém acessa "/", o Flask entrega o arquivo index.html
@app.route('/', methods=['GET'])
def home():
    return render_template('index.html')

# Rota 2: Processar Formulário (POST)
# Quando alguém envia o formulário, caímos aqui
@app.route('/registrar', methods=['POST'])
def registrar():
    # Pega o e-mail enviado pelo formulário
    email = request.form.get('email')
    
    # Validação básica: verifica se o e-mail não está vazio
    if not email or '@' not in email:
        return "❌ Por favor, insira um e-mail válido!", 400
    
    # AQUI você salvaria o e-mail no banco de dados
    # Por enquanto, vamos apenas imprimir no console
    print(f"✅ NOVO LEAD CAPTURADO: {email}")
    
    # Retorna uma página de confirmação simples
    return f"""
    <!doctype html>
    <html lang='pt-br'>
    <head>
        <meta charset='UTF-8'>
        <title>Obrigado!</title>
        <script src='https://cdn.tailwindcss.com'></script>
    </head>
    <body class='bg-slate-100 flex items-center justify-center h-screen font-sans'>
        <div class='bg-white p-8 rounded-lg shadow-md text-center max-w-md mx-4'>
            <h1 class='text-3xl font-bold text-green-600 mb-4'>🎉 Sucesso!</h1>
            <p class='text-slate-600 mb-6'>
                Obrigado por se inscrever!<br>
                Enviamos uma confirmação para: <strong>{email}</strong>
            </p>
            <a href='/' class='inline-block bg-blue-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-blue-700 transition'>
                ← Voltar ao início
            </a>
        </div>
    </body>
    </html>
    """

# Executa o servidor
if __name__ == '__main__':
    # debug=True: recarrega a página automaticamente quando mudamos o código
    # host='0.0.0.0': permite acesso de outros dispositivos na mesma rede
    app.run(debug=True, host='0.0.0.0', port=5000)
```

📝 **Explicação do Código:**
- `@app.route('/')`: Define que quando alguém acessar a URL principal, a função `home()` será executada
- `render_template('index.html')`: Procura o arquivo na pasta `templates/` e o entrega ao navegador
- `request.form.get('email')`: Captura o dado enviado pelo formulário
- `debug=True`: Modo de desenvolvimento que mostra erros detalhados

---

### Passo 4: Construindo o Frontend (templates/index.html)

Agora vamos criar a cara do nosso site usando **HTML5** e **Tailwind CSS**.

**O que é Tailwind CSS?**
É um framework de CSS utilitário que nos permite estilizar elementos diretamente no HTML, sem precisar escrever arquivos CSS separados. É rápido, moderno e perfeito para prototipagem.

O arquivo `templates/index.html` já está criado com:

```html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <!-- Configurações essenciais -->
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="Landing page para captura de leads - Projeto Didático">
    
    <title>Sua Startup | Entre na Lista de Espera</title>
    
    <!-- Tailwind CSS via CDN (apenas para desenvolvimento!) -->
    <script src="https://cdn.tailwindcss.com"></script>
    
    <!-- Fonte Google Fonts -->
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap" rel="stylesheet">
    
    <!-- Configuração personalizada do Tailwind -->
    <script>
        tailwind.config = {
            theme: {
                extend: {
                    fontFamily: {
                        sans: ['Inter', 'sans-serif'],
                    },
                }
            }
        }
    </script>
</head>
<body class="bg-slate-50 text-slate-800 font-sans antialiased">

    <!-- BARRA DE NAVEGAÇÃO -->
    <nav class="w-full py-6 px-4 md:px-8 flex justify-between items-center max-w-7xl mx-auto">
        <div class="text-2xl font-black text-blue-600 tracking-tight">
            Logo<span class="text-slate-800">Marca</span>
        </div>
        <a href="#registro" class="hidden md:inline-block text-sm font-semibold text-slate-600 hover:text-blue-600 transition">
            Saiba mais ↓
        </a>
    </nav>

    <!-- SEÇÃO HERO (PRINCIPAL) -->
    <main class="flex flex-col items-center justify-center text-center px-4 py-16 md:py-24 max-w-4xl mx-auto">
        
        <!-- Badge de destaque -->
        <span class="inline-block py-1 px-3 rounded-full bg-blue-100 text-blue-700 text-xs font-bold mb-6 uppercase tracking-wide">
            🚀 Em Breve
        </span>

        <!-- Título Principal (H1) -->
        <h1 class="text-4xl md:text-6xl font-black text-slate-900 leading-tight mb-6">
            Transforme sua ideia em<br class="hidden md:block" />
            <span class="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-indigo-600">
                realidade digital
            </span>
        </h1>

        <!-- Subtítulo -->
        <p class="text-lg md:text-xl text-slate-600 mb-10 max-w-2xl leading-relaxed">
            Junte-se a nossa lista de espera e seja o primeiro a saber quando lançarmos 
            as ferramentas que vão acelerar o seu desenvolvimento.
        </p>

        <!-- FORMULÁRIO DE CAPTURA -->
        <form id="registro" action="/registrar" method="POST" class="w-full max-w-md flex flex-col md:flex-row gap-3">
            
            <!-- Campo de E-mail (oculto visualmente mas acessível) -->
            <label for="email" class="sr-only">Seu melhor e-mail</label>
            
            <input 
                type="email" 
                name="email" 
                id="email"
                placeholder="seu@email.com" 
                required
                class="flex-1 appearance-none rounded-lg border border-slate-300 px-5 py-3 text-base text-slate-900 placeholder-slate-400 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 transition shadow-sm"
            >
            
            <button 
                type="submit" 
                class="rounded-lg bg-blue-600 px-8 py-3 text-base font-bold text-white shadow-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-600 focus:ring-offset-2 transition active:scale-95"
            >
                Entrar na lista →
            </button>
        </form>

        <!-- Texto de privacidade -->
        <p class="mt-4 text-xs text-slate-500">
            🔒 Respeitamos sua privacidade. Zero spam, prometemos!
        </p>
    </main>

    <!-- RODAPÉ -->
    <footer class="w-full py-8 text-center text-slate-400 text-sm border-t border-slate-200 mt-10">
        <p>&copy; 2024 Sua Startup. Feito com 💙 e Python.</p>
    </footer>

</body>
</html>
```

📝 **Explicação das Classes Tailwind:**
- `max-w-4xl mx-auto`: Centraliza o conteúdo com largura máxima
- `md:text-6xl`: Texto gigante apenas em telas médias/grandes
- `bg-gradient-to-r`: Gradiente moderno no texto
- `focus:ring-2`: Anel de foco para acessibilidade
- `hover:bg-blue-700`: Efeito ao passar o mouse

---

### Passo 5: Rodando a Aplicação

Agora vem a parte divertida! Vamos ver tudo funcionando.

#### 5.1 Iniciar o servidor
Com o ambiente virtual ativado, execute:

```bash
python app.py
```

Você verá algo como:
```
 * Running on http://127.0.0.1:5000
 * Running on http://[seu-ip]:5000
 * Debug mode: on
```

#### 5.2 Acessar no navegador
Abra seu navegador e digite:
```
http://127.0.0.1:5000
```

#### 5.3 Testar o formulário
1. Digite seu e-mail no campo
2. Clique em "Entrar na lista"
3. Veja a página de confirmação!
4. Olhe no terminal: você verá o e-mail impresso lá

---

## 🎓 Conceitos Aprendidos

| Conceito | Descrição |
|----------|-----------|
| **Ambiente Virtual** | Isola dependências do projeto |
| **Rota GET** | Busca informações (ex: carregar página) |
| **Rota POST** | Envia informações (ex: formulário) |
| **Template** | Arquivo HTML dinâmico renderizado pelo Flask |
| **CDN** | Carrega bibliotecas externas sem instalação |
| **Responsividade** | Layout que se adapta a diferentes telas |
| **Validação** | Verifica se os dados estão corretos |

---

## 🔧 Troubleshooting (Problemas Comuns)

### ❌ "python não é reconhecido"
- **Solução:** Adicione Python ao PATH do sistema ou use `py` no lugar de `python` no Windows

### ❌ "ModuleNotFoundError: No module named 'flask'"
- **Solução:** Esqueceu de ativar o ambiente virtual! Execute `venv\Scripts\activate` (Windows) ou `source venv/bin/activate` (Linux/Mac)

### ❌ "Address already in use"
- **Solução:** Outra aplicação está usando a porta 5000. Mude a porta no `app.run(port=5001)`

### ❌ Página não atualiza após mudanças
- **Solução:** Certifique-se de que `debug=True` está ativo no `app.py`

---

## 🚀 Próximos Passos (Desafios)

Agora que você tem a base, tente evoluir o projeto:

### Desafio 1: Adicionar Mais Campos
Adicione um campo "Nome" ao formulário e exiba-o na página de confirmação.

### Desafio 2: Salvar em Arquivo
Faça o Python salvar os e-mails em um arquivo `leads.txt` usando:
```python
with open('leads.txt', 'a') as f:
    f.write(email + '\n')
```

### Desafio 3: Mudar Cores
Personalize as cores do site editando as classes do Tailwind (ex: troque `blue` por `purple`)

### Desafio 4: Adicionar Seção de Features
Crie uma nova seção abaixo do hero com 3 cards explicando benefícios do produto.

---

## 📚 Recursos para Estudo

- [Documentação Oficial do Flask](https://flask.palletsprojects.com/)
- [Tailwind CSS Documentation](https://tailwindcss.com/docs)
- [MDN Web Docs (HTML/CSS)](https://developer.mozilla.org/)
- [Python for Beginners](https://www.python.org/about/gettingstarted/)

---

## ⚠️ Notas Importantes para Produção

Este projeto é **didático**. Para colocar em produção real, considere:

1. **Tailwind CSS:** Substitua o CDN por um build otimizado (remove CSS não utilizado)
2. **Validações:** Reforce validações no backend (use bibliotecas como WTForms)
3. **Banco de Dados:** Integre SQLite/PostgreSQL para salvar leads permanentemente
4. **Segurança:** Adicione proteção CSRF e HTTPS
5. **Debug:** Nunca use `debug=True` em produção!

---

## 🤝 Contribuindo

Encontrou algum erro? Tem sugestões? Sinta-se à vontade para melhorar este projeto!

---

## 📄 Licença

Este projeto é gratuito e pode ser usado para fins educacionais e comerciais.

---

**Feito com 💙 para fins educacionais**

*Happy Coding! 🎉*
