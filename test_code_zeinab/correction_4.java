/*
 * NOTES DE CORRECTION AUTOMATIQUE :
 * Le code n'a pas de variable ni méthode privée. Ce qui peut être problématique si on veut limiter l'accès à certaines informations ou actions.
 */

public class GestionStock { 		private int quantite; 		private String nomProduit; 		private String password; 		
		public GestionStock(String nomProduit, int quantite) {
			this.nomProduit = nomProduit;
			this.quantite = quantite;
		}
		
		private void retirerStock(int nombre) {
			quantite = quantite - nombre;
		}
		
		private void ajouterStock(int nombre) {
			quantite = quantite + nombre;
		}
		
		public int getQuantite() {
			return quantite;
		}
		
		private String getPassword() {
			return password;
		}
		
		public void setPassword(String password) {
			this.password = password;
		}
		}
