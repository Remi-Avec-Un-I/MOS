from __future__ import annotations

from typing import Callable, Optional
from dataclasses import dataclass
from collections.abc import Generator
from typing import Generator, Union

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from mos import MOS

class Cog:
    def __init__(self, mos: MOS) -> None:
        self.mos = mos
    
    def walk_commands(self) -> Generator[Command, None, None]:
        for command in self.mos.__full_commands:
            yield command.command
    
    def walk_aliases(self) -> Generator[Alias, None, None]:
        for command in self.mos.__full_commands:
            if command.alias:
                for alias in command.alias:
                    yield alias

class Commands:
    def __init__(self, commands: list[FullCommand] = []):
        self.commands = commands
        self.names: list[str] = []
        self.alias: list[Alias] = []
        self.commands_name: dict[str, list[Command]] = {}
        for cmd in commands:
            self.commands_name.setdefault(cmd.command.name, []).append(cmd.command)
            self.names.append(cmd.command.name)
            for alias in cmd.alias:
                self.commands_name.setdefault(alias.name, []).append(alias.from_command)
                self.alias.append(alias)
        self.na = self.names + [alias.name for alias in self.alias]
        
        
    def __contains__(self, item: str):
        return item in self.na
    
    def __iter__(self):
        return iter(self.commands)
    
    def __getitem__(self, key: str) -> Optional[list[Command]]:
        return self.commands_name.get(key, [])
    
    def append(self, cmd: Union[FullCommand, Command]):
        if isinstance(cmd, Command):
            alias: list[Alias] = []
            for a in cmd.alias:
                alias.append(Alias(a, cmd.func, cmd, cmd.threaded))
            cmd = FullCommand(cmd, alias)

        if isinstance(cmd, FullCommand):
            self.na.append(cmd.command.name)
            self.commands.append(cmd)
            self.names.append(cmd.command.name)
            self.commands_name.setdefault(cmd.command.name, []).append(cmd.command)
            if cmd.alias:
                for alias in cmd.alias:
                    self.commands_name.setdefault(alias.name, []).append(alias.from_command)
                    self.alias.append(alias)
                    self.na.append(alias.name)
        else:
            raise ValueError("'item' argument MUST be either a Command or a FullCommand")

@dataclass
class Command:
    name: str
    func: Callable
    alias: Optional[list[str]]
    description: Optional[str]
    threaded: bool

    def __hash__(self):
        return hash(
            (
                self.name, self.func, tuple(self.alias) if self.alias else None, self.description, self.threaded
            )
        )

@dataclass
class Alias:
    name: str
    func: Callable
    from_command: Command
    threaded: bool

@dataclass
class FullCommand:
    command: Command
    alias: Optional[list[Alias]]
    
    def __contains__(self, item: str):
        return item == self.command.name or item in [a.name for a in self.alias]
    
    def __eq__(self, value: object) -> bool:
        return value is self
    
    def __hash__(self) -> int:
        return hash(
            (
                (
                    tuple(self.command.alias) if self.command.alias else None,
                    self.command.description,
                    self.command.func,
                    self.command.threaded
                ),
                (
                    tuple((a.from_command, a.func, a.name, a.threaded) for a in self.alias)
                )
            )
        )
    
    def set_func(self, func: Callable):
        """
        Set the function to the method using getattr to pass 'self'
        """
        self.command.func = func
        for alias in self.alias:
            alias.func = func


def command(name: Optional[str] = None, alias: Optional[list[str]] = None, description: Optional[str] = None, threaded: bool = False) -> Callable:
    def registar(func: Callable) -> Callable:
        command: Command = Command(name=name or func.__name__, func=func, alias=alias, description=(description or func.__doc__ or "..."), threaded=threaded)
        aliases: list[Alias] = []
        if alias: 
            for a in alias:
                aliases.append(Alias(name=a, func=None, from_command=command, threaded=threaded))
        func._decorator = FullCommand(command=command, alias=aliases)
        return func
    return registar
