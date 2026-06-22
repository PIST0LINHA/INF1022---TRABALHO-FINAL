"""
ast_nodes.py
============
Nós da AST (Abstract Syntax Tree) para a linguagem ObsAct.

Cada classe representa um nó da árvore sintática.
O método codegen() de cada nó gera o código Python correspondente,
recebendo o nível de indentação atual.

Hierarquia:
    Program
    ├── Device (com ou sem sensor)
    └── Cmd (um por linha de comando)
        ├── Attrib       — set x = VAR / set x = act_execute
        ├── IfCmd        — se OBS entao CMDS [senao CMDS]
        ├── WhileCmd     — enquanto OBS entao CMDS
        └── ActStmt      — ligar / desligar / verificar / alerta / broadcast
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional

INDENT = "    "  # 4 espaços por nível


# ─────────────────────────────────────────────────────────────────
# CLASSES BASE
# ─────────────────────────────────────────────────────────────────


class Node:
    """Classe base de todos os nós da AST."""

    def codegen(self, level: int = 0) -> str:
        raise NotImplementedError(
            f"codegen() não implementado em {type(self).__name__}"
        )

    def _indent(self, level: int) -> str:
        return INDENT * level


# ─────────────────────────────────────────────────────────────────
# PROGRAM
# ─────────────────────────────────────────────────────────────────


@dataclass
class Program(Node):
    """
    Raiz da AST.
    Contém a lista de declarações de dispositivos e a lista de comandos.
    """

    devices: list[Device]
    cmds: list[Node]

    def codegen(self, level: int = 0) -> str:
        lines = []

        # Preâmbulo: funções auxiliares exigidas pelo enunciado
        lines.append(PREAMBULO)

        # Inicialização dos sensores (gerada pelos Device nodes)
        sensor_inits = [d.codegen(level) for d in self.devices]
        sensor_inits = [s for s in sensor_inits if s]  # remove vazios
        if sensor_inits:
            lines.extend(sensor_inits)
            lines.append("")  # linha em branco separadora

        # Comandos principais
        for cmd in self.cmds:
            lines.append(cmd.codegen(level))

        return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────
# DEVICE
# ─────────────────────────────────────────────────────────────────


@dataclass
class Device(Node):
    """
    dispositivo : { namedevice }
    dispositivo : { namedevice, observation }

    Gera a inicialização do sensor com valor 0 (seção 1.4 do enunciado).
    """

    namedevice: str
    observation: Optional[str] = None  # None quando o device não tem sensor

    def codegen(self, level: int = 0) -> str:
        if self.observation:
            # Sensor declarado → inicializa com 0 por padrão
            return f"{self._indent(level)}{self.observation} = 0  # valor padrão"
        return ""  # dispositivo sem sensor não gera código de inicialização


# ─────────────────────────────────────────────────────────────────
# EXPRESSÕES (VAR e OBS)
# Não são nós completos — retornam strings prontas para emissão.
# ─────────────────────────────────────────────────────────────────


@dataclass
class VarExpr(Node):
    """
    VAR → num | bool | namedevice | VAR + VAR | VAR - VAR
    Sintetiza uma expressão Python como string.
    """

    value: str  # já vem como string do parser (ex: "40", "True", "potencia + 5")

    def codegen(self, level: int = 0) -> str:
        return self.value


@dataclass
class ObsExpr(Node):
    """
    OBS → observation oplogic VAR
        | OBS && OBS
        | OBS || OBS
    Sintetiza uma condição Python como string.
    """

    expr: str  # ex: "temperatura > 30", "(temperatura > 30) and (umidade < 80)"

    def codegen(self, level: int = 0) -> str:
        return self.expr


# ─────────────────────────────────────────────────────────────────
# ATTRIB
# ─────────────────────────────────────────────────────────────────


@dataclass
class Attrib(Node):
    """
    ATTRIB → set observation = VAR
           | set observation = ACT_EXECUTE
    """

    sensor: str  # nome do sensor/observation
    value: str  # expressão Python (VAR ou chamada de função)

    def codegen(self, level: int = 0) -> str:
        return f"{self._indent(level)}{self.sensor} = {self.value}"


# ─────────────────────────────────────────────────────────────────
# IF / IFELSE
# ─────────────────────────────────────────────────────────────────


@dataclass
class IfCmd(Node):
    """
    OBSACT → se OBS entao CMDS
           | se OBS entao CMDS senao CMDS
    """

    condition: str  # expressão Python da condição (ObsExpr.codegen())
    then_cmds: list[Node]  # comandos do bloco then
    else_cmds: list[Node] = field(default_factory=list)  # vazio se não houver senao

    def codegen(self, level: int = 0) -> str:
        lines = []

        # if
        lines.append(f"{self._indent(level)}if {self.condition}:")
        for cmd in self.then_cmds:
            lines.append(cmd.codegen(level + 1))

        # else (opcional)
        if self.else_cmds:
            lines.append(f"{self._indent(level)}else:")
            for cmd in self.else_cmds:
                lines.append(cmd.codegen(level + 1))

        return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────
# WHILE
# ─────────────────────────────────────────────────────────────────


@dataclass
class WhileCmd(Node):
    """
    LOOP → enquanto OBS entao CMDS
    """

    condition: str  # expressão Python da condição
    body_cmds: list[Node]

    def codegen(self, level: int = 0) -> str:
        lines = []
        lines.append(f"{self._indent(level)}while {self.condition}:")
        for cmd in self.body_cmds:
            lines.append(cmd.codegen(level + 1))
        return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────
# ACT — ações sobre dispositivos
# ─────────────────────────────────────────────────────────────────


@dataclass
class ActStmt(Node):
    """
    ACT_EXECUTE → ligar namedevice
                | desligar namedevice
                | verificar(namedevice)

    ACT_ALERT   → enviar alerta ("msg") namedevice
                | enviar alerta ("msg", observation) namedevice
                | enviar alerta ("msg") para todos: DEVLIST
    """

    call: str  # linha Python pronta, ex: "ligar('ventilador')"

    def codegen(self, level: int = 0) -> str:
        # Suporte a broadcast: call pode conter múltiplas linhas
        lines = self.call.strip().split("\n")
        return "\n".join(f"{self._indent(level)}{line}" for line in lines)


# ─────────────────────────────────────────────────────────────────
# PREÂMBULO PYTHON
# Funções auxiliares exigidas pelo enunciado (seção 1.3).
# ─────────────────────────────────────────────────────────────────

PREAMBULO = """\
# Gerado automaticamente pelo transpilador ObsAct -> Python
# ──────────────────────────────────────────────────────────

def ligar(namedevice):
    print(namedevice + " ligado!")
    return 1


def desligar(namedevice):
    print(namedevice + " desligado!")
    return 0


def verificar(namedevice):
    # Simulacao: retorna 1 (ligado). Adapte para hardware real.
    print(namedevice + " esta ligado.")
    return 1


def alerta(namedevice, msg, var=None):
    print(namedevice + " recebeu o alerta:")
    if var is not None:
        print(str(msg).strip('"') + " " + str(var))
    else:
        print(str(msg).strip('"'))


# ── Codigo transpilado ──────────────────────────────────────────
"""
