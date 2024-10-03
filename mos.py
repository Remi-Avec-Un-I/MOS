import _thread
import sys
import shlex
import importlib
import readline
from typing import Type
from importlib.util import resolve_name
from .commands import FullCommand, Command, Commands

class MOS:
    def __init__(
        self, 
        prompt: str = ">>> ", 
        check_duplicates: bool = True,
        keyboard_interrupt: bool = True
    ):
        """
        prompt: what's show before you enter a command
        check_duplicates: warns you if you have a command load multiples times
        keyboard_interrupt: if ctrl+c close the app or not
        """
        self.prompt = prompt
        self.check_duplicates = check_duplicates
        
        self.commands = Commands()
        self.__extensions: list[str] = []
        
        readline.set_completer(self.completer)
        readline.parse_and_bind("tab: complete")
        readline.parse_and_bind('"\\C-p": previous-history')
        readline.parse_and_bind('"\\C-n": next-history')
        readline.parse_and_bind('"\\C-r": reverse-search-history')
        readline.parse_and_bind('"\\C-d": delete-char')
        readline.parse_and_bind('"\\C-a": beginning-of-line')
        readline.parse_and_bind('"\\C-e": end-of-line')
        readline.parse_and_bind('"\\C-k": kill-line')
        readline.parse_and_bind('"\\C-y": yank')
        readline.parse_and_bind('"\\C-l": clear-screen')
        
        
        self.setup_hook()
        if self.check_duplicates:
            self.__check_duplicates()
        if keyboard_interrupt:
            try:
                self.__run()
            except KeyboardInterrupt:
                exit(0)
        else:
            self.__run()

    def completer(self, text, state):
        commands = self.commands.na
        
        options = [cmd for cmd in commands if cmd.startswith(text)]
        if state < len(options):
            return options[state]
        else:
            return None

    def setup_hook(self) -> None:
        pass

    def __check_duplicates(self) -> None:
        duplicates = []
        
        # Check for duplicates in action
        seen_actions = set()
        for command in self.commands:
            if command in seen_actions:
                duplicates.append(command)
            else:
                seen_actions.add(command)

        for action in duplicates:
            print(f"WARNING: Duplicate action {action}")

    def add_cog(self, cog: Type):
        methods = [getattr(cog, func) for func in dir(cog) if callable(getattr(cog, func))]
        if not any("_decorator" in dir(attr) for attr in methods if callable(attr)):
            print("No commands found in cog", cog)
            return
        
        for attr in methods:
            if not "_decorator" in dir(attr):
                continue
            
            command: FullCommand = attr._decorator
            command.set_func(getattr(cog, command.command.func.__name__))
            self.commands.append(command)

    def add_file(self, name: str):
        if name in self.__extensions:
            raise ValueError("Extension already loaded")
        
        self.__extensions.append(name)
        name = resolve_name(name, package=None)
        try:
            lib = importlib.import_module(name)
        except ImportError as e:
            raise ValueError(f"File not found: {name}\n{str(e)}")
        
        sys.modules[name] = lib
        try:
            setup = getattr(lib, "setup")
        except AttributeError:
            del sys.modules[name]
            raise ValueError(f"No setup function for extension named : {name}")

        try:
            setup(self)
        except Exception as e:
            del sys.modules[name]
            raise e

    def __run(self):
        while True:
            instruction = input(self.prompt)
            cmd = shlex.split(instruction)
            if not cmd:
                continue
            args = cmd[1:]
            cmd = cmd[0]
            if cmd in self.commands:
                cog: Command
                for cog in self.commands[cmd]:
                    if cog.threaded:
                        _thread.start_new_thread(cog.func, args)
                    else:
                        cog.func(*args)