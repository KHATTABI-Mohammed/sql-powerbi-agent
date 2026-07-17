# Table: order_items

Lignes de détail d'une commande (une ligne = un produit commandé dans une commande).

| Colonne       | Type    | Description                                    |
|---------------|---------|--------------------------------------------------|
| order_item_id | INTEGER | Identifiant unique de la ligne (clé primaire)    |
| order_id      | INTEGER | Référence vers `orders.order_id`                 |
| product_id    | INTEGER | Référence vers `products.product_id`             |
| quantity      | INTEGER | Quantité commandée                               |
| unit_price    | REAL    | Prix unitaire au moment de la commande (euros)   |

Relations:
- `order_items.order_id` -> `orders.order_id`
- `order_items.product_id` -> `products.product_id`

Le chiffre d'affaires d'une ligne se calcule par `quantity * unit_price`.
