from mcp.server.fastmcp import FastMCP
import javalang

mcp = FastMCP("mon_premier_serveur")

@mcp.tool()
def analyser_code(code: str) -> dict:
    """Analyse un extrait de code Java et retourne des informations structurees et fiables"""
    try:
        tree = javalang.parse.parse(code)
    except javalang.parser.JavaSyntaxError as e:
        return {
            "erreur_syntaxe": True,
            "type_erreur": "syntaxe_invalide",
            "message": f"Erreur de syntaxe Java detectee : {str(e)}",
            "conseil": "Le code contient une ou plusieurs erreurs de syntaxe qui empechent une analyse complete. Il faut d'abord corriger la syntaxe (accolades, points-virgules, declarations) avant de pouvoir analyser la logique du code."
        }
    except Exception as e:
        return {
            "erreur_syntaxe": True,
            "type_erreur": "erreur_inconnue",
            "message": f"Erreur lors de l'analyse : {str(e)}",
            "conseil": "Impossible d'analyser ce code automatiquement."
        }
    
    methodes_info = []
    for path, node in tree.filter(javalang.tree.MethodDeclaration):
        methodes_info.append({
            "nom": node.name,
            "modificateurs": list(node.modifiers),
            "parametres": [(p.type.name, p.name) for p in node.parameters],
            "exceptions_declarees": node.throws if node.throws else []
        })
    
    return {
        "nombre_de_methodes": len(methodes_info),
        "methodes": methodes_info
    }

@mcp.tool()
def additionner(a: int, b: int) -> int:
    """Additionne deux nombres et retourne le resultat"""
    return a + b


if __name__ == "__main__":
    mcp.run()