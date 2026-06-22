import ply.lex as lex

reserved = {
    "dispositivo": "DISPOSITIVO",
    "set": "SET",
    "se": "SE",
    "entao": "ENTAO",
    "senao": "SENAO",
    "enquanto": "ENQUANTO",
    "ligar": "LIGAR",
    "desligar": "DESLIGAR",
    "verificar": "VERIFICAR",
    "enviar": "ENVIAR",
    "alerta": "ALERTA",
    "para": "PARA",
    "todos": "TODOS",
    "TRUE": "TRUE",
    "FALSE": "FALSE",
}

tokens = list(reserved.values()) + [
    "NAMEDEVICE",
    "NUM",
    "STRING",
    "OPLOGIC",
    "AND",
    "OU",
    "MAIS",
    "MENOS",
    "IGUAL",
    "DOIS_PONTOS",
    "PONTO",
    "VIRGULA",
    "PAREN_ESQ",
    "PAREN_DIR",
    "CHAVE_ESQ",
    "CHAVE_DIR",
]

t_IGUAL = r"="
t_DOIS_PONTOS = r":"
t_PONTO = r"\."
t_VIRGULA = r","
t_PAREN_ESQ = r"\("
t_PAREN_DIR = r"\)"
t_CHAVE_ESQ = r"\{"
t_CHAVE_DIR = r"\}"
t_MAIS = r"\+"
t_MENOS = r"\-"
t_AND = r"&&"
t_OU = r"\|\|"


def t_NUM(t):
    r"\d+"
    t.value = int(t.value)
    return t


def t_OPLOGIC(t):
    r">=|<=|==|!=|>|<"
    return t


def t_STRING(t):
    r'"[^"]+"'
    return t


def t_COMMENT(t):
    r"//[^\n]*"
    pass


def t_NAMEDEVICE(t):
    r"[a-zA-Z_][a-zA-Z0-9_]*"
    t.type = reserved.get(t.value, "NAMEDEVICE")
    return t


t_ignore = " \t"


def t_newline(t):
    r"\n+"
    t.lexer.lineno += len(t.value)


def t_error(t):
    print(f"[ERRO]: Caractere invalido '{t.value[0]}' na linha {t.lexer.lineno}")
    t.lexer.skip(1)


lexer = lex.lex()

# teste que fiz baseado nos exemplos do pdf do trabalho

if __name__ == "__main__":
    teste = """
    // comentario ignorado
    dispositivo: {Termometro, temperatura}
    dispositivo: {ventilador, potencia}
    set temperatura = 40.
    set potencia = 30.
    se temperatura >= 20 entao
        set estado_ventilador = verificar(ventilador)
        se estado_ventilador == 0 entao ligar ventilador
        set potencia = 50
    
    se temperatura <= 25 entao
        set estado_ventilador = 0
    """

    lexer.input(teste)
    print(f"{'TOKEN':<15} {'TIPO':<15} {'LINHA'}")
    print("-" * 40)
    for tok in lexer:
        print(f"{str(tok.value):<15} {tok.type:<15} {tok.lineno}")
