/** @odoo-module **/
import { _t } from "web.core";


const MANAGER_GROUP = 'printnode_base.printnode_security_group_manager';

// Messages that might be shown to the user dependening on the state of wkhtmltopdf
const WKHTMLTOPDF_LINK = '<br><br><a href="http://wkhtmltopdf.org/" target="_blank">wkhtmltopdf.org</a>';
const WKHTMLTOPDF_MESSAGES = {
  broken:
    _t(
      "Your installation of Wkhtmltopdf seems to be broken. The report will be shown " +
      "in html."
    ) + WKHTMLTOPDF_LINK,
  install:
    _t(
      "Unable to find Wkhtmltopdf on this system. The report will be shown in " + "html."
    ) + WKHTMLTOPDF_LINK,
  upgrade:
    _t(
      "You should upgrade your version of Wkhtmltopdf to at least 0.12.0 in order to " +
      "get a correct display of headers and footers as well as support for " +
      "table-breaking between pages."
    ) + WKHTMLTOPDF_LINK,
  workers: _t(
    "You need to start Odoo with at least two workers to print a pdf version of " +
    "the reports."
  ),
};

export {
  MANAGER_GROUP,
  WKHTMLTOPDF_MESSAGES,
}