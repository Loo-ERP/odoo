odoo.define('website_sale_delivery.checkout', function (require) {
    'use strict';
    
    var sAnimations = require('website.content.snippets.animation');
    var ajax = require('web.ajax');
    var core = require('web.core');
    var _t = core._t;
    
    sAnimations.registry.websiteSaleDelivery = sAnimations.Class.extend({
        selector: '.oe_website_sale',
        read_events: {
            'change .oe_website_sale select[name="shipping_id"]': '_onSetAddress',
            'click #delivery_carrier input[name="delivery_type"]': '_onCarrierClick'
        },
    
        /**
         * @override
         * @param {Object} parent
         */
        start: function (parent) {
            var $carriers = $("#delivery_carrier input[name='delivery_type']");
            // Workaround to:
            // - update the amount/error on the label at first rendering
            // - prevent clicking on 'Pay Now' if the shipper rating fails
            if ($carriers.length > 0) {
                $carriers.filter(':checked').click();
            }
        },
    
        //--------------------------------------------------------------------------
        // Private
        //--------------------------------------------------------------------------
    
        /**
         * @private
         * @param {Object} ev
         */
        _onCarrierClick: function (ev) {
            var $pay_button = $('#o_payment_form_pay');
            $pay_button.prop('disabled', true);
            var carrier_id = $(ev.currentTarget).val();
            var values = {'carrier_id': carrier_id};
            ajax.jsonRpc('/shop/update_carrier', 'call', values)
              .then(this._onCarrierUpdateAnswer);
        },
        /**
         * @private
         * @param {Object} result
         */
        _onCarrierUpdateAnswer: function (result) {
            var $pay_button = $('#o_payment_form_pay');
            var $amount_delivery = $('#order_delivery span.oe_currency_value');
            var $amount_untaxed = $('#order_total_untaxed span.oe_currency_value');
            var $amount_tax = $('#order_total_taxes span.oe_currency_value');
            var $amount_total = $('#order_total span.oe_currency_value');
            var $carrier_badge = $('#delivery_carrier input[name="delivery_type"][value=' + result.carrier_id + '] ~ .badge.d-none');
            var $compute_badge = $('#delivery_carrier input[name="delivery_type"][value=' + result.carrier_id + '] ~ .o_delivery_compute');
            var $discount = $('#order_discounted');
    
            if ($discount && result.new_amount_order_discounted) {
                // Cross module without bridge
                // Update discount of the order
                $discount.find('.oe_currency_value').text(result.new_amount_order_discounted);
    
                // We are in freeshipping, so every carrier is Free
                $('#delivery_carrier .badge').text(_t('Free'));
            }
    
            if (result.status === true) {
                $amount_delivery.text(result.new_amount_delivery);
                $amount_untaxed.text(result.new_amount_untaxed);
                $amount_tax.text(result.new_amount_tax);
                $amount_total.text(result.new_amount_total);
                $carrier_badge.children('span').text(result.new_amount_delivery);
                $carrier_badge.removeClass('d-none');
                $compute_badge.addClass('d-none');
                $pay_button.prop('disabled', false);
            }
            else {
                console.error(result.error_message);
                $compute_badge.text(result.error_message);
                $amount_delivery.text(result.new_amount_delivery);
                $amount_untaxed.text(result.new_amount_untaxed);
                $amount_tax.text(result.new_amount_tax);
                $amount_total.text(result.new_amount_total);
            }
        },
    
        //--------------------------------------------------------------------------
        // Handlers
        //--------------------------------------------------------------------------
    
        /**
         * @private
         * @param {Object} ev
         */
        _onSetAddress: function (ev) {
            var value = $(ev.currentTarget).val();
            var $provider_free = $("select[name='country_id']:not(.o_provider_restricted), select[name='state_id']:not(.o_provider_restricted)");
            var $provider_restricted = $("select[name='country_id'].o_provider_restricted, select[name='state_id'].o_provider_restricted");
            if (value === 0) {
                // Ship to the same address : only show shipping countries available for billing
                $provider_free.hide().attr('disabled', true);
                $provider_restricted.show().attr('disabled', false).change();
            } else {
                // Create a new address : show all countries available for billing
                $provider_free.show().attr('disabled', false).change();
                $provider_restricted.hide().attr('disabled', true);
            }
        },
    
    });
    
});