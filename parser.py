"""
parser.py
=========
Parser ObsAct que constrói a AST e a converte para Python.

Fluxo:
    .obsact -> lexer -> tokens -> parser (p_* retornam nós AST)
            -> Program (raiz) -> Program.codegen() -> .py

Uso:
    python parser.py programa.obsact
    python parser.py programa.obsact -o saida.py
"""

import sys
import os
import ply.yacc as yacc
from lexer import tokens, lexer
from ast_nodes import (
    Program,
    Device,
    Attrib,
    IfCmd,
    WhileCmd,
    ActStmt,
)

# ─────────────────────────────────────────────────────────────────
# PRECEDÊNCIA
# ─────────────────────────────────────────────────────────────────

precedence = (
    ("left", "OU"),
    ("left", "AND"),
    ("left", "MAIS", "MENOS"),
)

# ─────────────────────────────────────────────────────────────────
# PROGRAM — raiz da AST
# ─────────────────────────────────────────────────────────────────


def p_program(p):
    """program : devices cmds"""
    p[0] = Program(devices=p[1], cmds=p[2])


# ─────────────────────────────────────────────────────────────────
# DEVICES  →  list[Device]
# ─────────────────────────────────────────────────────────────────


def p_devices_multi(p):
    """devices : devices device"""
    p[0] = p[1] + [p[2]]


def p_devices_single(p):
    """devices : device"""
    p[0] = [p[1]]


def p_device_sensor(p):
    """device : DISPOSITIVO DOIS_PONTOS CHAVE_ESQ NAMEDEVICE VIRGULA NAMEDEVICE CHAVE_DIR"""
    # p[4] = namedevice  |  p[6] = observation
    p[0] = Device(namedevice=p[4], observation=p[6])


def p_device_only(p):
    """device : DISPOSITIVO DOIS_PONTOS CHAVE_ESQ NAMEDEVICE CHAVE_DIR"""
    p[0] = Device(namedevice=p[4], observation=None)


# ─────────────────────────────────────────────────────────────────
# CMDS  →  list[Node]   (recursão à esquerda)
# ─────────────────────────────────────────────────────────────────


def p_cmds_multi_simple(p):
    """cmds : cmds simple_cmd PONTO"""
    p[0] = p[1] + [p[2]]


def p_cmds_multi_block(p):
    """cmds : cmds block_cmd"""
    p[0] = p[1] + [p[2]]


def p_cmds_single_simple(p):
    """cmds : simple_cmd PONTO"""
    p[0] = [p[1]]


def p_cmds_single_block(p):
    """cmds : block_cmd"""
    p[0] = [p[1]]


def p_simple_cmd(p):
    """simple_cmd : attrib
    | act_stmt"""
    p[0] = p[1]


def p_block_cmd(p):
    """block_cmd : obsact
    | loop"""
    p[0] = p[1]


# ─────────────────────────────────────────────────────────────────
# ATTRIB  →  Attrib
# ─────────────────────────────────────────────────────────────────


def p_attrib_var(p):
    """attrib : SET NAMEDEVICE IGUAL var"""
    p[0] = Attrib(sensor=p[2], value=p[4])


def p_attrib_act(p):
    """attrib : SET NAMEDEVICE IGUAL act_execute"""
    p[0] = Attrib(sensor=p[2], value=p[4])


# ─────────────────────────────────────────────────────────────────
# VAR  →  str  (expressão Python pronta)
# ─────────────────────────────────────────────────────────────────


def p_var_num(p):
    """var : NUM"""
    p[0] = str(p[1])


def p_var_true(p):
    """var : TRUE"""
    p[0] = "True"


def p_var_false(p):
    """var : FALSE"""
    p[0] = "False"


def p_var_namedevice(p):
    """var : NAMEDEVICE"""
    p[0] = p[1]


def p_var_soma(p):
    """var : var MAIS var"""
    p[0] = f"{p[1]} + {p[3]}"


def p_var_sub(p):
    """var : var MENOS var"""
    p[0] = f"{p[1]} - {p[3]}"


# ─────────────────────────────────────────────────────────────────
# OBS  →  str  (condição Python pronta)
# ─────────────────────────────────────────────────────────────────


def p_obs_simples(p):
    """obs : NAMEDEVICE OPLOGIC var"""
    p[0] = f"{p[1]} {p[2]} {p[3]}"


def p_obs_and(p):
    """obs : obs AND obs"""
    p[0] = f"({p[1]}) and ({p[3]})"


def p_obs_or(p):
    """obs : obs OU obs"""
    p[0] = f"({p[1]}) or ({p[3]})"


# ─────────────────────────────────────────────────────────────────
# OBSACT  →  IfCmd
#
# if_header carrega a condição como p[0] para o IfCmd pai.
# Estrutura de PONTO:
#   bloco:  if_header cmds [else_header cmds] PONTO
#   inline: if_header act_stmt PONTO
# ─────────────────────────────────────────────────────────────────


def p_if_header(p):
    """if_header : SE obs ENTAO"""
    p[0] = p[2]  # condição Python


def p_else_header(p):
    """else_header : SENAO"""
    pass


def p_obsact_if_bloco(p):
    """obsact : if_header cmds PONTO"""
    p[0] = IfCmd(condition=p[1], then_cmds=p[2])


def p_obsact_ifelse_bloco(p):
    """obsact : if_header cmds else_header cmds PONTO"""
    # Sem PONTO antes do else_header — o PONTO final fecha o bloco inteiro
    p[0] = IfCmd(condition=p[1], then_cmds=p[2], else_cmds=p[4])


def p_obsact_if_inline(p):
    """obsact : if_header act_stmt PONTO"""
    p[0] = IfCmd(condition=p[1], then_cmds=[p[2]])


def p_obsact_ifelse_inline(p):
    """obsact : if_header act_stmt PONTO else_header act_stmt PONTO"""
    p[0] = IfCmd(condition=p[1], then_cmds=[p[2]], else_cmds=[p[5]])


# ─────────────────────────────────────────────────────────────────
# LOOP  →  WhileCmd
# ─────────────────────────────────────────────────────────────────


def p_while_header(p):
    """while_header : ENQUANTO obs ENTAO"""
    p[0] = p[2]


def p_loop_bloco(p):
    """loop : while_header cmds PONTO"""
    p[0] = WhileCmd(condition=p[1], body_cmds=p[2])


def p_loop_inline(p):
    """loop : while_header act_stmt PONTO"""
    p[0] = WhileCmd(condition=p[1], body_cmds=[p[2]])


# ─────────────────────────────────────────────────────────────────
# ACT  →  ActStmt (empacota uma string Python pronta)
# ─────────────────────────────────────────────────────────────────


def p_act_stmt(p):
    """act_stmt : act_execute
    | act_alert"""
    p[0] = ActStmt(call=p[1])


def p_act_ligar(p):
    """act_execute : LIGAR NAMEDEVICE"""
    p[0] = f"ligar('{p[2]}')"


def p_act_desligar(p):
    """act_execute : DESLIGAR NAMEDEVICE"""
    p[0] = f"desligar('{p[2]}')"


def p_act_verificar(p):
    """act_execute : VERIFICAR PAREN_ESQ NAMEDEVICE PAREN_DIR"""
    p[0] = f"verificar('{p[3]}')"


def p_alert_simples(p):
    """act_alert : ENVIAR ALERTA PAREN_ESQ STRING PAREN_DIR NAMEDEVICE"""
    p[0] = f"alerta('{p[6]}', {p[4]})"


def p_alert_simples_sem_paren(p):
    """act_alert : ENVIAR ALERTA STRING NAMEDEVICE"""
    p[0] = f"alerta('{p[4]}', {p[3]})"


def p_alert_com_sensor(p):
    """act_alert : ENVIAR ALERTA PAREN_ESQ STRING VIRGULA NAMEDEVICE PAREN_DIR NAMEDEVICE"""
    p[0] = f"alerta('{p[8]}', {p[4]}, {p[6]})"


def p_alert_com_sensor_sem_paren(p):
    """act_alert : ENVIAR ALERTA STRING VIRGULA NAMEDEVICE NAMEDEVICE"""
    p[0] = f"alerta('{p[6]}', {p[3]}, {p[5]})"


def p_alert_broadcast(p):
    """act_alert : ENVIAR ALERTA PAREN_ESQ STRING PAREN_DIR PARA TODOS DOIS_PONTOS devlist"""
    chamadas = [f"alerta('{d}', {p[4]})" for d in p[9]]
    p[0] = "\n".join(chamadas)


def p_alert_broadcast_sem_paren(p):
    """act_alert : ENVIAR ALERTA STRING PARA TODOS DOIS_PONTOS devlist"""
    chamadas = [f"alerta('{d}', {p[3]})" for d in p[7]]
    p[0] = "\n".join(chamadas)


# ─────────────────────────────────────────────────────────────────
# DEVLIST  →  list[str]
# ─────────────────────────────────────────────────────────────────


def p_devlist_multi(p):
    """devlist : devlist VIRGULA NAMEDEVICE"""
    p[0] = p[1] + [p[3]]


def p_devlist_single(p):
    """devlist : NAMEDEVICE"""
    p[0] = [p[1]]


# ─────────────────────────────────────────────────────────────────
# ERRO
# ─────────────────────────────────────────────────────────────────


def p_error(p):
    if p:
        print(
            f"[ERRO SINTÁTICO] Token inesperado '{p.value}' ({p.type}) na linha {p.lineno}"
        )
    else:
        print("[ERRO SINTÁTICO] Fim de arquivo inesperado")
        print("  Dica: verifique se todos os blocos estão fechados com '.'")


# ─────────────────────────────────────────────────────────────────
# INSTÂNCIA
# ─────────────────────────────────────────────────────────────────

parser = yacc.yacc()

# ─────────────────────────────────────────────────────────────────
# PONTO DE ENTRADA
# ─────────────────────────────────────────────────────────────────


def transpilar(source: str, output_path: str) -> None:
    lexer.lineno = 1
    ast = parser.parse(source, lexer=lexer)

    if ast is None:
        print("[ERRO] Parse falhou — arquivo de saída não gerado.")
        return

    codigo = ast.codegen()

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(codigo)
        f.write("\n")

    print(f"[OK] Gerado: {output_path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python parser.py <arquivo.obsact> [-o saida.py]")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = (
        sys.argv[sys.argv.index("-o") + 1]
        if "-o" in sys.argv
        else os.path.splitext(input_path)[0] + ".py"
    )

    with open(input_path, encoding="utf-8") as f:
        source = f.read()

    transpilar(source, output_path)
