# Taskr - A CLI Wrapper for TaskWarrior

Objective:
Provide an enhanced UX for TaskWarrior by integrating questionary and typer for interactive task management & rich for aesthetic outputs

project structure:
```txt
src
└── taskr
    ├── __init__.py
    ├── cli
    │   └── commands # typer cli with questionary
    ├── config # yaml based config
    └── interface # taskwarrior shell commands interface

6 directories, 1 file
```

**Naming Conventions & Underscore Usage Guide:**

`_varorfunc` -- acceptable
`__varorfunc` -- acceptable
`__varorfunc__` -- acceptable
`VarOrFunc` -- acceptable
`varorfunc` -- golden standard

`_var_or_func` -- unacceptable
`__var_or_func` -- unacceptable
`__var_or_func__` -- unacceptable
`var_or_func`  -- disgusting
`Var_Or_Func` -- i will murder you
