odoo.define('ebs_fusion_services.service_order_chart', function (require) {
'use strict';

    var core = require('web.core');
    var publicWidget = require('web.public.widget');
    var time = require('web.time');
    var portalComposer = require('portal.composer');
    var rpc = require('web.rpc');
    var qweb = core.qweb;
    var _t = core._t;

    publicWidget.registry.service_order_chart = publicWidget.Widget.extend({

        selector: '#service_order_chart',

        init: function(){
            this._super.apply(this, arguments);
        },

        start: function() {
            var service_order_ids = document.getElementById("service_order_ids").value;
            var so_ids = []
            if (service_order_ids) {
                so_ids = JSON.parse(service_order_ids)
            }
            rpc.query({
                model: "ebs.crm.service.process",
                method: "get_service_order_chart_data",
                args: [[]],
                kwargs: {
                    service_order_ids: so_ids,
                },
            }).then(function (result) {
            var service_order_data_ctx = document.getElementById("service_order_data_chart_canvas");
            var service_order_data_myChart = new Chart(service_order_data_ctx, {
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
                    }, {
                        label: result.label[3],
                        data: [result.data[3]],
                        backgroundColor: "rgba(75, 192, 192, 0.2)",
                        borderColor: "rgba(75, 192, 192, 1)",
                    }, {
                        label: result.label[4],
                        data: [result.data[4]],
                        backgroundColor: "rgba(153, 102, 255, 0.2)",
                        borderColor: "rgba(153, 102, 255, 1)",
                        }]
                    }
                });
            });
            var target_audience = document.getElementById("target_audience").value;
            var target_audience_ids = []
            if (target_audience) {
                target_audience_ids = JSON.parse(target_audience)
            }
            rpc.query({
                        model: "ebs.crm.service.process",
                        method: "get_service_order_chart_data_of_target_audience",
                        args: [[]],
                        kwargs: {
                            target_audience: target_audience_ids,
                        },
                    }).then(function (result) {
                        var ctx = document.getElementById("service_order_data_chart_canvas_of_target_audience");
                        var myChart = new Chart(ctx, {
                            type: 'bar',
                            data: {
                                labels: ["Target Audience"],
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
                                }, {
                                    label: result.label[3],
                                    data: [result.data[3]],
                                    backgroundColor: "rgba(75, 192, 192, 0.2)",
                                    borderColor: "rgba(75, 192, 192, 1)",
                                }]
                            },
                        });
                    })
            return this._super.apply(this, arguments);
        },
    });
});
