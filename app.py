from flask import Flask, render_template, request, redirect, url_for

# Inicializa a aplicação Flask
# __name__ ajuda o Flask a encontrar recursos relativos a este arquivo
app = Flask(__name__)

@app.route('/', methods=['GET'])
def home():
    """
    Rota principal que renderiza a landing page.
    Apenas serve o HTML inicial.
    """
    return render_template('index.html')

@app.route('/registrar', methods=['POST'])
def registrar():
    """
    Processa o envio do formulário de captura de lead.
    """
    # Captura o email enviado pelo formulário
    email = request.form.get('email')

    # Validação simples no backend (segurança básica)
    if not email or '@' not in email:
        # Em um cenário real, você poderia retornar um erro com flash messages
        return "Por favor, insira um e-mail válido.", 400

    # AQUI: É onde você salvaria o e-mail no banco de dados ou API de marketing
    print(f"Lead capturado com sucesso: {email}")

    # Retorna uma página simples de confirmação
    # Usamos um string formatada para simplicidade, mas poderia ser outro template
    return f"""
    <!doctype html>
    <html lang='pt-br'>
    <head>
        <meta charset='UTF-8'>
        <title>Obrigado!</title>
        <script src='https://cdn.tailwindcss.com'></script>
    </head>
    <body class='bg-slate-100 flex items-center justify-center h-screen font-sans'>
        <div class='bg-white p-8 rounded-lg shadow-md text-center max-w-md'>
            <h1 class='text-3xl font-bold text-green-600 mb-4'>Inscrição Realizada!</h1>
            <p class='text-slate-600 mb-6'>Obrigado por fornecer seu e-mail: <strong>{email}</strong>.</p>
            <a href='/' class='inline-block bg-blue-600 text-white px-6 py-2 rounded hover:bg-blue-700 transition'>
                Voltar ao início
            </a>
        </div>
    </body>
    </html>
    """

if __name__ == '__main__':
    # Executa o servidor de desenvolvimento
    # host='0.0.0.0' torna acessível na rede local (útil para testes em mobile)
    app.run(debug=True, host='0.0.0.0', port=5000)
