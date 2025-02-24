/** @odoo-module **/
import {WebsiteSale} from "@website_sale/js/website_sale";

WebsiteSale.include({
    events: Object.assign({}, WebsiteSale.prototype.events, {
        "change select[name='l10n_latam_identification_type_id']": "_onChangeIdentificationType",
    }),
    start: function () {
        this.elementCities = document.querySelector("select[name='city_id']");
        this.cityBlock = document.querySelector(".div_city");
        this.elementState = document.querySelector("select[name='state_id']");
        this.autoFormat = document.querySelector(".checkout_autoformat");
        this.elementCountry = document.querySelector("select[name='country_id']");
        $("select[name='l10n_co_edi_obligation_type_ids']").select2();
        this.obligationTypeBlock = document.querySelector(".div_obligation_types");
        this.fiscalRegimenBlock = document.querySelector(".div_fiscal_regimen");
        this.isColombianCompany = this.elementCountry?.dataset.company_country_code === 'CO';
        this.$("select[name='l10n_latam_identification_type_id']").change();
        return this._super.apply(this, arguments);
    },
    _onChangeIdentificationType: function(ev) {
        const selectedIdentificationType = ev.currentTarget.options[ev.currentTarget.selectedIndex].text

        if (selectedIdentificationType === "NIT") {
            this.obligationTypeBlock.classList.remove("d-none");
            this.fiscalRegimenBlock.classList.remove("d-none");
        } else {
            this.obligationTypeBlock.classList.add("d-none");
            this.fiscalRegimenBlock.classList.add("d-none");
        }
    },
    _onChangeState: function (ev) {
        return this._super.apply(this, arguments).then(() => {
            const selectedCountry = this.elementCountry.options[this.elementCountry.selectedIndex].getAttribute("code");
            if (this.isColombianCompany && selectedCountry === "CO") {
                if (! this.autoFormat.length) {
                    return undefined;
                }
                const rpcRoute = `/shop/l10n_co_state_infos/${this.elementState.value}`;
                return this.rpc(rpcRoute, {
                }).then((data) => {
                    if (data['cities']?.length) {
                        this.elementCities.innerHTML = "";
                        data['cities'].forEach((item) => {
                            const option = document.createElement("option");
                            option.textContent = item[1];
                            option.value = item[0];
                            option.setAttribute("data-code", item[2]);
                            this.elementCities.appendChild(option);
                        });
                        this.elementCities.parentElement.classList.remove("d-none");
                    } else {
                        this.elementCities.value = "";
                        this.elementCities.parentElement.classList.add("d-none");
                    }
                });
            }
        });
    },
    _onChangeCountry: function (ev) {
        return this._super.apply(this, arguments).then(() => {
            if (this.isColombianCompany) {
                const selectedCountry = ev.currentTarget.options[ev.currentTarget.selectedIndex].getAttribute("code");
                const cityInput = document.querySelector(".form-control[name='city']");
                if (selectedCountry === "CO") {
                    if (cityInput.value) {
                        cityInput.value = "";
                    }
                    this.cityBlock.classList.add("d-none");
                    return this._onChangeState();
                } else {
                    this.cityBlock.querySelector("input").value = "";
                    this.cityBlock.classList.remove("d-none");
                    this.elementCities.value = "";
                    this.elementCities.parentElement.classList.add("d-none");
                }
            }
        });
    },
});
