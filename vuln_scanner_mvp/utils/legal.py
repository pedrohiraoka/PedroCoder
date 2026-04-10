"""
Módulo de avisos legais e termos de uso.
Essencial para garantir que o usuário compreenda as responsabilidades.
"""

LEGAL_WARNING = """
⚠️ **AVISO LEGAL IMPORTANTE** ⚠️

Esta ferramenta foi desenvolvida exclusivamente para fins **EDUCACIONAIS** e de **TESTES AUTORIZADOS**.

Ao utilizar este scanner de vulnerabilidades, você declara que:

1. ✅ Possui **autorização explícita** do proprietário do sistema/alvo para realizar testes de segurança.
2. ✅ Compreende que o uso não autorizado desta ferramenta pode configurar **crime cibernético** conforme a legislação aplicável (ex: Lei 12.737/2012 - Lei Carolina Dieckmann no Brasil).
3. ✅ Assume total **responsabilidade** pelas ações realizadas com esta ferramenta.
4. ✅ Não utilizará esta ferramenta para atividades maliciosas ou ilegais.

**Os desenvolvedores NÃO se responsabilizam** por quaisquer danos, perdas ou consequências legais decorrentes do uso indevido desta ferramenta.

---

### 📜 Termos de Uso

- Esta ferramenta realiza apenas verificações **PASSIVAS** e **SIMULAÇÕES**.
- Nenhum exploit ativo é executado.
- O scanning de portas e serviços pode gerar logs nos sistemas alvo.
- Use apenas em ambientes de teste controlados ou com autorização documentada.

---

**Deseja prosseguir? Marque a caixa abaixo para confirmar que leu e concorda com os termos.**
"""

ETHICAL_GUIDELINES = """
### 🛡️ Diretrizes Éticas para Pentest

1. **Autorização**: Sempre obtenha autorização por escrito antes de testar qualquer sistema.
2. **Escopo**: Defina claramente o escopo do teste (quais sistemas, quais técnicas).
3. **Confidencialidade**: Mantenha em sigilo todas as descobertas.
4. **Não Maleficência**: Não cause danos aos sistemas testados.
5. **Documentação**: Registre todas as ações e descobertas detalhadamente.
6. **Reporte Responsável**: Comunique vulnerabilidades de forma responsável ao proprietário.
"""

RESPONSIBLE_DISCLOSURE = """
### 📧 Divulgação Responsável de Vulnerabilidades

Caso encontre vulnerabilidades em sistemas de terceiros:

1. **Contate o proprietário** de forma privada e segura.
2. **Forneça detalhes** suficientes para reproduzir o problema.
3. **Aguarde um prazo razoável** (geralmente 90 dias) antes de divulgar publicamente.
4. **Não explore** a vulnerabilidade além do necessário para demonstração.
5. **Ofereça recomendações** de correção quando possível.
"""


def get_legal_warning() -> str:
    """Retorna o texto completo do aviso legal."""
    return LEGAL_WARNING


def get_ethical_guidelines() -> str:
    """Retorna as diretrizes éticas."""
    return ETHICAL_GUIDELINES


def get_responsible_disclosure() -> str:
    """Retorna informações sobre divulgação responsável."""
    return RESPONSIBLE_DISCLOSURE
