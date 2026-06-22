"""
parser.py
=========
Esqueleto do parser ObsAct → Python usando PLY.

Importa o lexer já pronto (lexer.py).
Todas as regras da gramática estão aqui com comentários explicando
onde você deve adicionar a geração de código (marcado com TODO).

ESTRUTURA DE BLOCOS:
    Comandos simples terminam com '.':
        set x = 10.
        ligar ventilador.

    Blocos se/enquanto com múltiplos cmds:
        se cond entao
            cmd1.
            cmd2.
        senao           ← sem PONTO antes do senao
            cmd3.
        .               ← PONTO final fecha o bloco inteiro

    se inline (linha única):
        se cond entao ligar ventilador.
"""

import ply.yacc as yacc
from lexer import tokens, lexer  # importa do seu lexer.py

# ─────────────────────────────────────────────────────────────────
# PRECEDÊNCIA
# Resolve shift/reduce de OBS (&&, ||) e VAR (+, -)
# Menor prioridade primeiro, maior prioridade por último.
# ─────────────────────────────────────────────────────────────────

precedence = (
    ("left", "OU"),
    ("left", "AND"),
    ("left", "MAIS", "MENOS"),
)


def p_program(p):
    """program : devices cmds"""
    # TODO: ponto de entrada — aqui você pode emitir o preâmbulo
    #       (funções ligar/desligar/verificar/alerta) antes dos cmds
    pass


def p_devices_multi(p):
    """devices : devices device"""
    pass


def p_devices_single(p):
    """devices : device"""
    pass


def p_device_sensor(p):
    """device : DISPOSITIVO DOIS_PONTOS CHAVE_ESQ NAMEDEVICE VIRGULA NAMEDEVICE CHAVE_DIR"""
    # dispositivo : { namedevice, observation }
    namedevice = p[4]  # ex: "Termometro"
    observation = p[6]  # ex: "temperatura"  ← mesmo token NAMEDEVICE, posição diferente
    # TODO: emitir inicialização do sensor com valor padrão 0
    #   ex: codegen.emit(f"{observation} = 0")
    pass


def p_device_only(p):
    """device : DISPOSITIVO DOIS_PONTOS CHAVE_ESQ NAMEDEVICE CHAVE_DIR"""
    # dispositivo : { namedevice }  — sem sensor
    namedevice = p[4]
    # TODO: registrar dispositivo sem sensor (se necessário)
    pass


def p_cmds_multi_simple(p):
    """cmds : cmds simple_cmd PONTO"""
    pass


def p_cmds_multi_block(p):
    """cmds : cmds block_cmd"""
    # block_cmd já consumiu seu próprio PONTO de fechamento
    pass


def p_cmds_single_simple(p):
    """cmds : simple_cmd PONTO"""
    pass


def p_cmds_single_block(p):
    """cmds : block_cmd"""
    pass


def p_simple_cmd(p):
    """simple_cmd : attrib
    | act_stmt"""
    pass


def p_block_cmd(p):
    """block_cmd : obsact
    | loop"""
    pass


def p_attrib_var(p):
    """attrib : SET NAMEDEVICE IGUAL var"""
    # set observation = VAR
    sensor = p[2]  # nome do sensor/observation
    valor = p[4]  # string sintetizada pelas regras de VAR
    # TODO: codegen.emit(f"{sensor} = {valor}")
    pass


def p_attrib_act(p):
    """attrib : SET NAMEDEVICE IGUAL act_execute"""
    # set observation = ACT_EXECUTE
    # ex: set estado = verificar(ventilador)
    sensor = p[2]
    chamada = p[4]  # string retornada por p_act_execute_*
    # TODO: codegen.emit(f"{sensor} = {chamada}")
    pass


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
    # permite usar o valor de um sensor como VAR
    p[0] = p[1]


def p_var_soma(p):
    """var : var MAIS var"""
    p[0] = f"{p[1]} + {p[3]}"


def p_var_sub(p):
    """var : var MENOS var"""
    p[0] = f"{p[1]} - {p[3]}"


def p_obs_simples(p):
    """obs : NAMEDEVICE OPLOGIC var"""
    p[0] = f"{p[1]} {p[2]} {p[3]}"


def p_obs_and(p):
    """obs : obs AND obs"""
    p[0] = f"({p[1]}) and ({p[3]})"


def p_obs_or(p):
    """obs : obs OU obs"""
    p[0] = f"({p[1]}) or ({p[3]})"


def p_if_header(p):
    """if_header : SE obs ENTAO"""
    # TODO: codegen.emit(f"if {p[2]}:")
    # TODO: codegen.indent()
    pass


def p_else_header(p):
    """else_header : SENAO"""
    # TODO: codegen.dedent()
    # TODO: codegen.emit("else:")
    # TODO: codegen.indent()
    pass


def p_end_block(p):
    """end_block :"""
    # Regra vazia executada ao fechar qualquer bloco.
    # TODO: codegen.dedent()
    pass


# Bloco multi-linha
def p_obsact_if_bloco(p):
    """obsact : if_header cmds PONTO end_block"""
    pass


def p_obsact_ifelse_bloco(p):
    """obsact : if_header cmds else_header cmds PONTO end_block"""
    # Sem PONTO entre cmds e else_header — o PONTO do último cmd
    # interno já foi consumido por cmds. O PONTO final fecha o else.
    pass


# Linha única (act_stmt apenas — attrib inline geraria ambiguidade)
def p_obsact_if_inline(p):
    """obsact : if_header act_stmt PONTO end_block"""
    pass


def p_obsact_ifelse_inline(p):
    """obsact : if_header act_stmt PONTO else_header act_stmt PONTO end_block"""
    pass


def p_while_header(p):
    """while_header : ENQUANTO obs ENTAO"""
    # TODO: codegen.emit(f"while {p[2]}:")
    # TODO: codegen.indent()
    pass


def p_loop_bloco(p):
    """loop : while_header cmds PONTO end_block"""
    pass


def p_loop_inline(p):
    """loop : while_header act_stmt PONTO end_block"""
    pass


def p_act_stmt(p):
    """act_stmt : act_execute
    | act_alert"""
    # act_execute e act_alert sintetizam strings com o código Python
    # TODO: emitir p[1]  ex: codegen.emit(p[1])
    pass


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
    # enviar alerta ("msg") namedevice
    p[0] = f"alerta('{p[6]}', {p[4]})"


def p_alert_com_sensor(p):
    """act_alert : ENVIAR ALERTA PAREN_ESQ STRING VIRGULA NAMEDEVICE PAREN_DIR NAMEDEVICE"""
    # enviar alerta ("msg", observation) namedevice
    # p[6] = observation (sensor cujo valor é concatenado à msg)
    # p[8] = namedevice  (destinatário)
    p[0] = f"alerta('{p[8]}', {p[4]}, {p[6]})"


def p_alert_broadcast(p):
    """act_alert : ENVIAR ALERTA PAREN_ESQ STRING PAREN_DIR PARA TODOS DOIS_PONTOS devlist"""
    # enviar alerta ("msg") para todos: dev1, dev2
    # p[9] = lista Python de nomes de dispositivos
    chamadas = [f"alerta('{d}', {p[4]})" for d in p[9]]
    p[0] = "\n".join(chamadas)


def p_devlist_multi(p):
    """devlist : devlist VIRGULA NAMEDEVICE"""
    p[0] = p[1] + [p[3]]


def p_devlist_single(p):
    """devlist : NAMEDEVICE"""
    p[0] = [p[1]]


def p_error(p):
    if p:
        print(
            f"[ERRO SINTÁTICO] Token inesperado '{p.value}' ({p.type}) na linha {p.lineno}"
        )
    else:
        print("[ERRO SINTÁTICO] Fim de arquivo inesperado")
        print("  Dica: verifique se todos os blocos estão fechados com '.'")


parser = yacc.yacc()

if __name__ == "__main__":
    casos = [
        (
            "simples",
            "dispositivo : { Termometro, temperatura }\n"
            "set temperatura = 40.\n"
            "se temperatura > 30 entao ligar ventilador.\n",
        ),
        (
            "bloco if/else",
            "dispositivo : { Termometro, temperatura }\n"
            "set temperatura = 40.\n"
            "se temperatura > 30 entao\n"
            "    set temperatura = 0.\n"
            "senao\n"
            "    set temperatura = 10.\n"
            ".\n",
        ),
        (
            "broadcast",
            "dispositivo : { monitor }\n"
            "dispositivo : { celular }\n"
            'enviar alerta ("Alerta!") para todos: monitor, celular.\n',
        ),
        (
            "enquanto",
            "dispositivo : { Termometro, temperatura }\n"
            "set temperatura = 5.\n"
            "enquanto temperatura > 0 entao\n"
            "    set temperatura = temperatura - 1.\n"
            ".\n",
        ),
        (
            "aritmetica",
            "dispositivo : { lampada, potencia }\n"
            "set potencia = 10.\n"
            "set potencia = potencia + 5.\n",
        ),
        (
            "and/or",
            "dispositivo : { Termometro, temperatura }\n"
            "dispositivo : { higrometro, umidade }\n"
            "set temperatura = 35.\n"
            "set umidade = 60.\n"
            "se temperatura > 30 && umidade < 80 entao ligar Termometro.\n",
        ),
    ]

    print("Testando casos da gramática ObsAct:")
    print("=" * 40)
    ok = 0
    for nome, src in casos:
        lexer.lineno = 1
        result = parser.parse(src, lexer=lexer)
        status = "✓OK" if result is not None else "FALHOU"
        if result is not None:
            ok += 1
        print(f"  {status}  {nome}")

    print(f"\n{ok}/{len(casos)} casos passando")
