# Table: customers

Contient les clients de l'entreprise.

| Colonne      | Type    | Description                                  |
|--------------|---------|-----------------------------------------------|
| customer_id  | INTEGER | Identifiant unique du client (clé primaire)   |
| name         | TEXT    | Nom complet du client                         |
| country      | TEXT    | Pays du client (ex: "France", "Maroc")        |
| segment      | TEXT    | Segment: "Particulier", "PME", "Grand Compte" |
| signup_date  | TEXT    | Date d'inscription (format YYYY-MM-DD)        |
