from odoo import api, fields, models

class PosConfig(models.Model):
    _inherit = "pos.config"

    closure_target_cash = fields.Monetary(
        string="Ziel-Barbestand (Kassenschluss)",
        help=(
            "Ziel-Barbestand, auf den der Kassierer die Kasse am Ende zurückführen soll.\n"
            "Dieser Betrag erscheint auf dem Abschlussbon."
        ),
        currency_field="currency_id",
        default=250.0,
    )

    print_closure_auto = fields.Boolean(
        string="Abschlussbon automatisch drucken",
        help="Wenn aktiv, wird beim Kassenschluss automatisch der Abschlussbon gedruckt.",
        default=True,
    )

    @api.model
    def get_pos_ui_settings(self, config_id):
        """Werte fürs Frontend."""
        config = self.browse(config_id)
        return {
            "closure_target_cash": config.closure_target_cash,
            "print_closure_auto": config.print_closure_auto,
            "currency_symbol": config.currency_id and config.currency_id.symbol or "€",
        }
