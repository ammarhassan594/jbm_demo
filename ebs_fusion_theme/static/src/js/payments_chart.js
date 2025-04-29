odoo.define('ebs_fusion_theme.payments_chart', function (require) {
'use strict';

    var core = require('web.core');
    var publicWidget = require('web.public.widget');
    var time = require('web.time');
    var portalComposer = require('portal.composer');
    var rpc = require('web.rpc');
    var qweb = core.qweb;
    var _t = core._t;

    publicWidget.registry.payments_chart = publicWidget.Widget.extend({

        selector: '#proforma_invoice_chart',

        init: function(){
            this._super.apply(this, arguments);
        },

        start: function() {
            var payments_ids = document.getElementById("payments_ids").value;
            var pay_ids = []
            if (payments_ids) {
                pay_ids = JSON.parse(payments_ids)
            }
            rpc.query({
                        model: "account.payment",
                        method: "get_account_payment_chart_data",
                        args: [[]],
                        kwargs: {
                            payments_ids: pay_ids,
                        },
                    }).then(function (result) {
                        var count_ctx = document.getElementById("payments_data_chart_canvas");
                        var myChart = new Chart(count_ctx, {
                            type: 'bar',
                            data: {
                                labels: ["Status"],
                                datasets: [{
                                    label: result.label[0],
                                    data: [result.data[0]],
                                    backgroundColor: "rgba(255, 99, 132, 0.2)",
                                    borderColor: "rgba(255,99,132,1)",
                                }, {
                                    label: result.label[1],
                                    data: [result.data[1]],
                                    backgroundColor: "rgba(54, 162, 235, 0.2)",
                                    borderColor: "rgba(54, 162, 235, 1)",
                                }, {
                                    label: result.label[2],
                                    data: [result.data[2]],
                                    backgroundColor: "rgba(255, 206, 86, 0.2)",
                                    borderColor: "rgba(255, 206, 86, 1)",
                                }]
                            },
                        });
                    })
            var payments_amount_ids = document.getElementById("payments_amount_ids").value;
            var pay_amount_ids = []
            if (payments_amount_ids) {
                pay_amount_ids = JSON.parse(payments_amount_ids)
            }
            rpc.query({
                        model: "account.payment",
                        method: "get_account_payment_amount_chart_data",
                        args: [[]],
                        kwargs: {
                            payments_amount_ids: pay_amount_ids,
                        },
                    }).then(function (result) {
                        var amount_ctx = document.getElementById("payments_amount_data_chart_canvas");
                        var myChart = new Chart(amount_ctx, {
                            type: 'bar',
                            data: {
                                labels: ["Total Amount"],
                                datasets: [{
                                    label: result.label[0],
                                    data: [result.data[0]],
                                    backgroundColor: "rgba(255, 99, 132, 0.2)",
                                    borderColor: "rgba(255,99,132,1)",
                                }, {
                                    label: result.label[1],
                                    data: [result.data[1]],
                                    backgroundColor: "rgba(54, 162, 235, 0.2)",
                                    borderColor: "rgba(54, 162, 235, 1)",
                                }, {
                                    label: result.label[2],
                                    data: [result.data[2]],
                                    backgroundColor: "rgba(255, 206, 86, 0.2)",
                                    borderColor: "rgba(255, 206, 86, 1)",
                                }]
                            },
                        });
                    })
            return this._super.apply(this, arguments);
        },
    });
});
