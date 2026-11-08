# MiniCLsp

This lsp uses your Typing and Interpretor to work.
Your root folder name should be MiniC, contains MiniC.g4, and folder "TypingAndInterpret".
The "TypingAndInterpret" folder should contains "MiniCInterpretVisitor.py"  "MiniCTypingVisitor.py"	files.


## Install MyantlrLsp
In the folder you want to install the LSP (ex: ~/Documents/Lsp/MiniCLsp/)
```
git clone https://github.com/VociNur/MiniAntlr4Lsp.git
make install
```
Then add this lsp to your IDE by using the command ```minic-lsp``` in any terminal.

### Add lsp to Helix IDE.
Edit your ~/.config/helix/languages.toml in adding (this code also add the grammar of c for coloration)

```
[language-server.minic-lsp]
command = "minic-lsp"
          
[[language]]
name = "minic"
scope = "source.minic"
file-types = [{ glob = "**/MiniC/**/*.c" }]
language-servers = ["minic-lsp"]
grammar = "c"
comment-token = "//"
block-comment-tokens = { start = "/*", end ="*/"}
```

