from mcp.server.fastmcp import FastMCP

mcp = FastMCP("mon_premier_serveur")

@mcp.tool()
def additionner(a: int, b: int) -> int:
    """Additionne deux nombres et retourne le resultat"""
    return a + b

@mcp.tool()
def analyser_code(code: str) -> dict:
    """Analyse un extrait de code Java et retourne des statistiques basiques"""
    nb_lignes = len(code.splitlines())
    nb_methodes = code.count("public ") + code.count("private ") + code.count("protected ")
    contient_try_catch = "try" in code and "catch" in code
    
    return {
        "nombre_de_lignes": nb_lignes,
        "nombre_approximatif_de_methodes": nb_methodes,
        "gestion_erreur_presente": contient_try_catch
    }


if __name__ == "__main__":
    mcp.run()