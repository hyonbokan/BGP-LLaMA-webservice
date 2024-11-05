import ast
import logging

logger = logging.getLogger(__name__)

class StreamToQueue:
    """
    A file-like object that redirects writes to a queue.
    """
    def __init__(self, q):
        self.queue = q

    def write(self, msg):
        if msg.strip():  # Avoid sending empty messages
            self.queue.put(msg)

    def flush(self):
        pass  # No action needed for flush


class VariableVisitor(ast.NodeVisitor):
    def __init__(self):
        self.defined_vars = set()
        self.used_vars = set()
        self.imported_modules = set()
        self.imported_names = set()

    def visit_FunctionDef(self, node):
        self.defined_vars.add(node.name)
        self.generic_visit(node)

    def visit_For(self, node):
        if isinstance(node.target, ast.Name):
            self.defined_vars.add(node.target.id)
        self.generic_visit(node)

    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Store):
            self.defined_vars.add(node.id)
        elif isinstance(node.ctx, ast.Load):
            self.used_vars.add(node.id)
        self.generic_visit(node)

    def visit_Import(self, node):
        for alias in node.names:
            self.imported_modules.add(alias.name)
            if alias.asname:
                self.imported_names.add(alias.asname)
            else:
                self.imported_names.add(alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        module = node.module
        if module:
            self.imported_modules.add(module)
            for alias in node.names:
                self.imported_names.add(alias.asname if alias.asname else alias.name)
        self.generic_visit(node)

def is_code_safe(code, safe_globals_keys):
    try:
        tree = ast.parse(code, mode='exec')
    except SyntaxError as e:
        logger.error(f"Syntax error during code parsing: {e}")
        return False

    # Define a list of allowed AST nodes, including ast.Global
    allowed_nodes = (
        ast.Module,
        ast.FunctionDef,
        ast.Call,
        ast.Name,
        ast.Load,
        ast.Store,
        ast.Import,
        ast.ImportFrom,
        ast.Assign,
        ast.For,
        ast.If,
        ast.Expr,
        ast.BinOp,
        ast.UnaryOp,
        ast.Compare,
        ast.BoolOp,
        ast.List,
        ast.Dict,
        ast.Tuple,
        ast.Return,
        ast.arguments,
        ast.arg,
        ast.Str,
        ast.Constant,  # For Python 3.8+
        ast.Attribute,
        ast.Subscript,
        ast.Index,
        ast.Slice,
        ast.ExtSlice,
        ast.alias,     # Allow alias nodes in import statements
        ast.Global,    # Allow 'global' statements
    )

    # Traverse the AST and ensure all nodes are allowed
    for node in ast.walk(tree):
        if not isinstance(node, allowed_nodes):
            logger.warning(f"Disallowed AST node detected: {node.__class__.__name__}")
            return False

        # Optionally, restrict certain function calls
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                if node.func.id in ['exec', 'eval', 'open', 'importlib']:
                    logger.warning(f"Disallowed function call detected: {node.func.id}")
                    return False
            elif isinstance(node.func, ast.Attribute):
                if node.func.attr in ['system', 'popen']:
                    logger.warning(f"Disallowed attribute function call detected: {node.func.attr}")
                    return False

    # Variable tracking
    visitor = VariableVisitor()
    visitor.visit(tree)

    # Combine imported names and built-ins
    allowed_vars = visitor.imported_names.union(safe_globals_keys).union(dir(__builtins__))

    # Check for undefined variables
    undefined_vars = visitor.used_vars - visitor.defined_vars - allowed_vars

    if undefined_vars:
        logger.warning(f"Undefined variables detected: {undefined_vars}")
        return False

    return True