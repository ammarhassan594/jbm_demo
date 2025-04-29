odoo.define('ebs_fusion_theme.invoice_chart', function (require) {
'use strict';

    var core = require('web.core');
    var publicWidget = require('web.public.widget');
    var time = require('web.time');
    var portalComposer = require('portal.composer');
    var rpc = require('web.rpc');
    var qweb = core.qweb;
    var _t = core._t;

    publicWidget.registry.invoice_chart = publicWidget.Widget.extend({

        selector: '#invoice_chart',

        init: function(){
            this._super.apply(this, arguments);
        },

        start: function() {
            var invoice_ids = document.getElementById("invoice_ids").value;
            var inv_ids = []
            if (invoice_ids) {
                inv_ids = JSON.parse(invoice_ids)
            }
            rpc.query({
                        model: "account.move",
                        method: "get_invoice_chart_data",
                        args: [[]],
                        kwargs: {
                            invoice_ids: inv_ids,
                        },
                    }).then(function (result) {
                        var count_ctx = document.getElementById("invoice_data_chart_canvas");
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
            var invoice_amount_ids = document.getElementById("invoice_amount_ids").value;
            var inv_amount_ids = []
            if (invoice_amount_ids) {
                inv_amount_ids = JSON.parse(invoice_amount_ids)
            }
            rpc.query({
                        model: "account.move",
                        method: "get_invoice_chart_amount_data",
                        args: [[]],
                        kwargs: {
                            invoice_amount_ids: inv_amount_ids,
                        },
                    }).then(function (result) {
                        var amount_ctx = document.getElementById("invoice_amount_data_chart_canvas");
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
