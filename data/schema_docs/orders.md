# Table: orders

Commandes passées par les clients. Une commande contient une ou plusieurs lignes,
stockées dans la table `order_items`.

| Colonne     | Type    | Description                                          |
|-------------|---------|--------------------------------------------------------|
| order_id    | INTEGER | Identifiant unique de la commande (clé primaire)       |
| customer_id | INTEGER | Référence vers `customers.customer_id`                 |
| order_date  | TEXT    | Date de la commande (format YYYY-MM-DD)                |
| status      | TEXT    | Statut: "Livrée", "En cours", "Annulée"                |

Relation: `orders.customer_id` -> `customers.customer_id`
