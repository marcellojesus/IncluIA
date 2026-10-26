"""Comandos de operação do acesso à Gestão Ativa (a partir de backend/, com o .venv ativo).

    python -m app.features.acesso.cli criar-admin --nome "Nome" --email admin@exemplo.gov.br
    python -m app.features.acesso.cli demo       # só com AMBIENTE=dev
    python -m app.features.acesso.cli limpar     # retenção: códigos antigos e pedidos não confirmados

`criar-admin` é o único jeito de criar administrador (não há rota para isso). `demo` prepara o
ambiente local: um administrador, uma secretária de Niterói/RJ já ativa e um pedido pendente de
diretor numa escola municipal de Niterói — só para desenvolvimento.
"""

import argparse

from dotenv import load_dotenv

from app.features.acesso import servico
from app.features.acesso.modelos import Conta
from app.features.declaracao.conversa import limpar_conversas_paradas
from app.shared import banco_gestao
from app.shared.ambiente import em_desenvolvimento

NITEROI = 3303302
ESCOLA_DEMO = 33055238  # UMEI Hermogenes Reis, rede municipal de Niterói


def _sessao():
    banco_gestao.migrar()
    return next(banco_gestao.obter_sessao())


def criar_admin(nome: str, email: str) -> None:
    sessao = _sessao()
    conta = servico.criar_admin(sessao, nome=nome, email=email)
    print(f"Administrador criado: {conta.email}. Entre na Gestão Ativa com o código enviado a este e-mail.")


def demo() -> None:
    # Contas de demonstração com códigos no console só existem em desenvolvimento (revisão do AgLGPD, B1).
    if not em_desenvolvimento():
        raise SystemExit("O comando demo só roda com AMBIENTE=dev.")
    sessao = _sessao()
    if sessao.query(Conta).count():
        print("O banco local já tem contas; nada foi criado.")
        return
    admin = servico.criar_admin(sessao, nome="Administração Escola Sem Barreiras", email="admin@demo.local")
    secretaria = servico.provisionar_secretario(
        sessao, admin=admin, nome="Secretária Demonstração", email="secretaria@demo.local", co_municipio=NITEROI,
        categoria="outro", metodo="Ambiente de demonstração local",
    )
    servico.solicitar_acesso_diretor(sessao, nome="Diretora Demonstração", email="diretora@demo.local", co_entidade=ESCOLA_DEMO)
    print("Ambiente de demonstração criado:")
    print(f"  administrador: {admin.email}")
    print(f"  secretária de Niterói/RJ: {secretaria.email}")
    print("  diretora com pedido pendente: diretora@demo.local (UMEI Hermogenes Reis)")
    print("Os códigos aparecem neste console; peça outro pela tela de entrada.")


def limpar() -> None:
    removidos = servico.limpar(_sessao())
    removidos["conversas_paradas"] = limpar_conversas_paradas(_sessao())
    print("Retenção aplicada: " + ", ".join(f"{quantidade} {tipo.replace('_', ' ')}" for tipo, quantidade in removidos.items()))


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(description="Operação do acesso à Gestão Ativa")
    sub = parser.add_subparsers(dest="comando", required=True)
    admin = sub.add_parser("criar-admin")
    admin.add_argument("--nome", required=True)
    admin.add_argument("--email", required=True)
    sub.add_parser("demo")
    sub.add_parser("limpar", help="apaga códigos antigos e pedidos nunca confirmados")
    args = parser.parse_args()
    try:
        if args.comando == "criar-admin":
            criar_admin(args.nome, args.email)
        elif args.comando == "demo":
            demo()
        else:
            limpar()
    except servico.ErroAcesso as erro:
        raise SystemExit(erro.mensagem) from None


if __name__ == "__main__":
    main()
