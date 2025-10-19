# POS Deposit Auto Lines (Odoo 18)

Auto-fügt im **POS** eine **Pfand-Position** hinzu, sobald ein Produkt mit Pfand verknüpft wird.
Dieses Modul ist speziell für **Odoo 18** umgesetzt und nutzt die offiziellen Loader‑Hooks und POS‑Patches.

## Verwendete Felder (wie von dir genannt)
- `x_deposit_product_1` → M2O auf **product.product** (Pfandprodukt)
- `x_quantity_by_deposit_product` → Anzahl/Faktor (z. B. 20 für einen Kasten)
- `x_unit_sale_product` → M2O auf **product.product** (Einzel‑/Einheiten‑Produkt). Wenn beim Hauptprodukt kein Pfand verknüpft ist, wird das Pfand vom **Einheiten‑Produkt** geerbt.

> Falls deine Felder anders heißen, einfach in `models/pos_session.py` und `static/src/pos_deposit.js` austauschen.

## Funktionsweise
- Beim Hinzufügen eines Produkts ins POS wird automatisch ein **zweites** POS‑Orderline mit dem Pfandprodukt erstellt.
- Die Menge ist **(Menge der Hauptzeile × `x_quantity_by_deposit_product`)**.
- Mengen bleiben **synchron**; Löschen der Hauptzeile löscht die Pfandzeile.

## Voraussetzungen
- Pfandprodukte sind **im POS verfügbar** (Häkchen „Im Kassensystem“).
- Pfandprodukte haben **0 % USt** (TSE‑freundlich, wenn DE).

## Installation
1. Ordner `pos_deposit_auto_v18` in deinen Addons‑Pfad / Repo „Zusatzmodule“ kopieren.
2. **Apps → Apps‑Liste aktualisieren** → Modul **POS Deposit Auto Lines (v18)** installieren.
3. POS‑Sitzung **schließen & neu öffnen**.

## Technisches
- Lädt Felder via `pos.session._loader_params_product_product`.
- Frontend‑Patch: `Order.add_product`, `Orderline.set_quantity`, `Order.removeOrderline`.
- Assets‑Bundle: `point_of_sale._assets_pos` (Odoo 18).
- Lizenz: LGPL‑3