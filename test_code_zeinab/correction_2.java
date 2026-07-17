/*
 * NOTES DE CORRECTION AUTOMATIQUE :
 * Ce code Java permet de gérer les opérations sur une compte en banque, telle que le dépôt et le retrait d'argent. L'objet Contient un double pour le solde du compte et une chaîne pour le nom du titulaire.
 */

public class GestionCompte {
    private double solde;
    private String titulaire;

    public GestionCompte(String titulaire) {
        this.titulaire = titulaire;
        this.solde = 0;
    }

    public void deposer(double montant) {
        if (montant > 0) {
            solde += montant;
        } else {
            throw new IllegalArgumentException("Montant doit être positif.");
        }
    }

    public void retirer(double montant) {
        if (montant <= solde) {
            solde -= montant;
        } else {
            throw new IllegalArgumentException("Montant supérieur au solde du compte.");
        }
    }

    public double getSolde() {
        return solde;
    }
}
