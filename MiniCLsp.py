#pyright: basic
import importlib
import logging
import re
import sys  # noqa: F401
import traceback
from pathlib import Path
from urllib.parse import unquote, urlparse

import antlr4
from antlr4.error.ErrorListener import (
    ErrorListener,
)
from lsprotocol import types as lsp
from pygls.lsp.server import LanguageServer
from rapidfuzz import process

logging.basicConfig(
    filename="/tmp/minic_lsp.log",
    filemode="w",  # Écrase le fichier à chaque relance du serveur
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

log = logging.getLogger("minic-lsp")
server = LanguageServer("mini-lsp", "0.1")

# search for MiniC.g4
# output: folder path qui contient MiniC.g4
def find_root(uri: str) -> Path | None:
    p = Path(unquote(urlparse(uri).path)).resolve()
    for d in [p.parent, *p.parents]:
        if (d / "MiniC.g4").exists():
            return d
    return None

# entrée: folder path qui contient MiniC.g4
# sortie
def load_project(root: Path):  
    """(Re)charge parser, lexer, visiteur depuis le projet du TP."""
    # by default
    for r in (root, root / "TypingAndInterpret"):
        if str(r) not in sys.path:
            sys.path.insert(0, str(r))

    names = ["MiniCLexer", "MiniCParser", "MiniCVisitor",
             "Lib.Errors", "TypingAndInterpret.MiniCTypingVisitor"]
    mods = {}
    for n in names:
        # reload: tes modifications du visiteur sont prises en compte
        # sans relancer le serveur
        mods[n] = importlib.reload(sys.modules[n]) if n in sys.modules \
            else importlib.import_module(n)
    return mods

def stem_from_uri(uri: str) -> str:
    return Path(unquote(urlparse(uri).path)).stem

def make_diag(line: int, col: int, len: int, msg: str):

    line = max(line - 1, 0)   # ANTLR : ligne depuis 1, LSP : depuis 0

    #j’arrive pas a réglre ce end position donc par défaut col + 1
    return lsp.Diagnostic(
        range=lsp.Range(lsp.Position(line, col), lsp.Position(line, col + len)),
        message=msg,
        severity=lsp.DiagnosticSeverity.Error,
        source="my-antlr4-lsp")

def make_safe_diag(line: int, col: int, len: int, msg: str):

    line = max(line - 1, 0)   # ANTLR : ligne depuis 1, LSP : depuis 0

    #j’arrive pas a réglre ce end position donc par défaut col + 1
    return lsp.Diagnostic(
        range=lsp.Range(lsp.Position(line, col), lsp.Position(line, col + len)),
        message=msg,
        severity=lsp.DiagnosticSeverity.Warning,
        source="my-antlr4-lsp")
    #j’aurais pu le rennomer
    # 
class MyErrorListener(ErrorListener):

    def __init__(self):
        super().__init__()
        self.diags: list[lsp.Diagnostic] = []

    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):   
        # self.count += 1
        self.diags.append(make_diag(line, column, len(offendingSymbol.text), msg))


class Analyzer:

    def analyze(self, uri: str, text: str) -> list[lsp.Diagnostic]:
        root = find_root(uri)
        if root is None:
            return [make_diag(1, 0, 0, "No root found")]

        try:
            m = load_project(root)
        except Exception as e:   
            log.exception("chargement du projet")
            return [make_diag(1, 0, 0, f"minic-lsp: {e!r}")]

        collector = MyErrorListener()
        lexer = m["MiniCLexer"].MiniCLexer(antlr4.InputStream(text))
        lexer.removeErrorListeners()
        lexer.addErrorListener(collector)

        parser = m["MiniCParser"].MiniCParser(antlr4.CommonTokenStream(lexer))
        parser.removeErrorListeners()
        parser.addErrorListener(collector)

        tree = parser.prog() 

        if collector.diags:
            return collector.diags

        errors = m["Lib.Errors"]
        try:
            m["TypingAndInterpret.MiniCTypingVisitor"].MiniCTypingVisitor().visit(tree)
        except errors.MiniCTypeError as e:
            msg = str(e)
            mt = re.search(r"Line (\d+) col (\d+)", msg)
            line, col = (int(mt[1]), int(mt[2])) if mt else (1, 0)
            collector.diags.append(make_diag(line, col, 1, msg))
        except Exception as e:   # NotImplementedError, MiniCInternalError, assert...
            log.exception("typage")
            collector.diags.append(make_diag(1, 0, 0, f"internal: {e!r}"))
        return collector.diags

analyzer = Analyzer()

def publish(ls: LanguageServer, uri: str):
    doc = ls.workspace.get_text_document(uri)
    diags = analyzer.analyze(doc.uri, doc.source)
    ls.text_document_publish_diagnostics(
        lsp.PublishDiagnosticsParams(uri=doc.uri, diagnostics=diags)
    )

@server.feature(lsp.TEXT_DOCUMENT_DID_OPEN)
def did_open(ls, params: lsp.DidOpenTextDocumentParams):
    publish(ls, params.text_document.uri)


@server.feature(lsp.TEXT_DOCUMENT_DID_CHANGE)
def did_change(ls, params: lsp.DidChangeTextDocumentParams):
    publish(ls, params.text_document.uri)


@server.feature(lsp.TEXT_DOCUMENT_DID_SAVE)
def did_save(ls, params: lsp.DidSaveTextDocumentParams):
    publish(ls, params.text_document.uri)


if __name__ == "__main__":
    server.start_io()


