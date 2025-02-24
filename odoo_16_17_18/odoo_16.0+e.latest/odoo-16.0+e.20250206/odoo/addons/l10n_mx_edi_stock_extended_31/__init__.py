from . import models


def _post_init_hook(cr, registry):
    cr.execute("""
        INSERT INTO l10n_mx_edi_customs_regime_stock_picking_rel (stock_picking_id, l10n_mx_edi_customs_regime_id)
             SELECT stock_picking.id,
                    l10n_mx_edi_customs_regime.id
               FROM stock_picking
               JOIN l10n_mx_edi_customs_regime
                 ON stock_picking.l10n_mx_edi_customs_regime_id = l10n_mx_edi_customs_regime.id
    """)
