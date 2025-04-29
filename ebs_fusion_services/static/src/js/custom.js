odoo.define('ebs_fusion_services.portal_services', function (require) {
'use strict';
    var core = require('web.core');
    var ajax = require('web.ajax');
    var _t = core._t;
    var rpc = require('web.rpc')

    jQuery( document ).ready(function() {
        $('#model_btn').hide();
        $(".new_row").css("display","block !important");
        var selectContacts = $("select[name='contacts']");
        var selectCompany = $("select[name='company']");
        var selectEmployee = $("select[name='employee']");
        var selectDependant = $("select[name='dependant']");
        $(".contact_input").parent('div').hide();
        $("select[name='service_option']").parent('div').hide();
        $("#option_label").hide();
        $(".company_input").parent('div').hide();
//        selectClients.parent('div').hide();
        $(".employee_input").parent('div').hide();
        $(".dependant_input").parent('div').hide();
//        $(".contacts_row").hide();
        $(".fees").hide();
        $(".comments").hide();
//        $(".alert").hide();
        $(".readonly-input").attr('readonly',1);
        selectContacts.attr('required',false);
        selectCompany.attr('required',false);
        selectEmployee.attr('required',false);
        selectDependant.attr('required',false);
        $("#document_modal").modal('hide');
//        ajax.jsonRpc("/get/client",'call',{}).then(function (data) {
//            if(data){
//                selectClients.html('');
//                var opt = $('<option>').text(data['client'][0][1])
//                            .attr('value', data['client'][0][0]);
//                console.log(opt,"PPP");
//                selectClients.append(opt);
//                selectClients.selectpicker("refresh");
//            }
//        });

         $('*[data-href]').on('click', function() {
            window.location = $(this).data("href");
        });

        $('.upload_doc_button').on('click', function(ev) {
            var selectTypes = $("select[name='doc_type']");
            var document_type_id = $(this).siblings($('.doc_id')).val();
            if(document_type_id){
                ajax.jsonRpc("/search/document_type",'call',{'doc_type_id':document_type_id}).then(function (data) {
                    console.log(data,"##");
                    selectTypes.html('');
                    var opt = $('<option>').text('Select...')
                                .attr('value', '');
                    selectTypes.append(opt);
                    var opt = $('<option>').text(data['name'])
                        .attr('value', data['id'])
                    selectTypes.append(opt);
                    selectTypes.parent('div').show();
//                        selectLines.trigger("change");
                    selectTypes.selectpicker("refresh");
                    if(data['required'] == 'required'){
                        $('.issue_date').show();
                        $('.expiry_date').show();
                    }
                    if(data['required'] == 'no'){
                        $('.issue_date').hide();
                        $('.expiry_date').hide();
                    }
                    if(data['required'] == 'optional'){
                        $('.issue_date').show();
                        $('.expiry_date').show();
                    }
                });
            }
            else {
                ajax.jsonRpc("/search/all/document_type",'call',{}).then(function (data) {
                    selectTypes.html('');
                    var opt = $('<option>').text('Select...')
                                .attr('value', '');
                    selectTypes.append(opt);
                    _.each(data.types, function (x) {
                        var opt = $('<option>').text(x[1])
                            .attr('value', x[0])
                        selectTypes.append(opt);
                    });
                    selectTypes.parent('div').show();
//                        selectLines.trigger("change");
                    selectTypes.selectpicker("refresh");
                });
            }
            $("#document_modal").modal('toggle');
//            $("#document_modal input[name='doc_type']").val($(this).siblings($('.doc_id')).val());
        });
        $("#services").on('change', function () {
            var service_id = $('#services').val();

            if (service_id){
            ajax.jsonRpc("/search/group_service",'call',{'group_id':service_id}).then(function (data) {
                    if (data.services_name.length > 0){
                       $('.servicebtn').hide();
                       $('#model_btn').show();
                    }
                    else{
                        $('.servicebtn').show();
                        $('#model_btn').hide();
                    }
                });

            }
            else{
                $('.servicebtn').show();
                $('#model_btn').hide();
            }
            });
            $("#model_btn").on('click', function () {
            var service_id = $('#services').val();
            ajax.jsonRpc("/search/group_service",'call',{'group_id':service_id}).then(function (data) {
                    if (data.services_name){
                       var i;
                       $('#model_body').find('p').remove()
                       $('#model_id_header').find('b').remove()
                        for (i = 0; i < data.services_name.length; i++) {
                            var service = $("<p></p>").text(data.services_name[i]);
                            $("#model_body").append(service);
                        }

                        var group = $("<b><p></p></b>").text('The service contains the following services:');
                        $("#model_id_header").append(group);
                    }
                });
        });
        $("#model_btn").on('click', function () {
            var service_id = $('#services').val();
            ajax.jsonRpc("/search/group_service",'call',{'group_id':service_id}).then(function (data) {
                    if (data.services_name){
                       var i;
                       $('#model_body').find('p').remove()
                       $('#model_id_header').find('b').remove()
                        for (i = 0; i < data.services_name.length; i++) {
                            var service = $("<p></p>").text(data.services_name[i]);
                            $("#model_body").append(service);
                        }

                        var group = $("<b><p></p></b>").text('The service contains the following services:');
                        $("#model_id_header").append(group);
                    }
                });
        });

        $('.sort_by_code').click(function(ev){
            console.log("=============",$(ev.currentTarget))
//            $(ev.currentTarget).
            window.location = window.location.origin + '/my/service_orders'+ '?' + "sortby=name"
        });
         $('.sort_by_service_date').click(function(ev){
            window.location = window.location.origin + '/my/service_orders'+ '?' + "sortby=service_order_date"
        });
         $('.sort_by_service_status').click(function(ev){
            window.location = window.location.origin + '/my/service_orders'+ '?' + "sortby=stage"
        });
         $('.sort_by_service_start_date').click(function(ev){
            window.location = window.location.origin + '/my/service_orders'+ '?' + "sortby=start_date"
        });
        $('.sort_by_service_end_date').click(function(ev){
            window.location = window.location.origin + '/my/service_orders'+ '?' + "sortby=due_date"
        });

//        $('select[name="pricelist_category"]').on('change', function(ev) {
//            var pricelist_id = $('#pricelist').val();
//            var category = $("#pricelist_category").val();
//            console.log(category,"@@");
//            if (!category) {
//                return;
//            }
//            ajax.jsonRpc("/search/pricelist_category",'call',{'pricelist_id':pricelist_id,'pricelist_category':category}).then(function (data) {
//                var selectLines = $("select[name='pricelist_line']");
//                if (selectLines.data('init')===0 || selectLines.find('option').length===1) {
//                    if (data.lines.length) {
//                        selectLines.html('');
//                        var opt = $('<option>').text('Select...')
//                                    .attr('value', '');
//                        selectLines.append(opt);
//                        _.each(data.lines, function (x) {
//                            var opt = $('<option>').text(x[1])
//                                .attr('value', x[0])
//                            selectLines.append(opt);
//                        });
//                        selectLines.parent('div').show();
////                        selectLines.trigger("change");
//                        selectLines.selectpicker("refresh");
//                    } else {
//                        selectLines.val('').parent('div').hide();
//                    }
//                    selectLines.data('init', 0);
//                } else {
//                    selectLines.data('init', 0);
//                }
//
//            });
//        });
//        $('select[name="company"]').on('change', function(ev) {
//            var company = $('#company').val();
//            var individual = $('#individual').is(':checked');
//            var selectPricelistCateg = $("select[name='pricelist_category']");
////            var selectLines = $("select[name='pricelist_line']");
//            console.log('Company..',company);
//            if (!company) {
////            console.log(selectPricelistCateg.find('option').not(':first'),"KK");
//                $("select[name='pricelist_category'] option").remove();
//                selectPricelistCateg.html('');
//                selectPricelistCateg.find('option').not(':first').remove();
////                selectLines.find('option').not(':first').remove();
//                return;
//            }
//            ajax.jsonRpc("/search/company",'call',{'company':company,'individual':individual}).then(function (result) {
//                $('#pricelistname').val(result['name']);
//                $('#pricelist').val(result['id']);
//                ajax.jsonRpc("/search/pricelist",'call',{'pricelist':result['id']}).then(function (data) {
//
//                if (selectPricelistCateg.data('init')===0 || selectPricelistCateg.find('option').length===1) {
//                    if (data.categories.length) {
//                        selectPricelistCateg.html('');
//                        var opt = $('<option>').text('Select...')
//                                    .attr('value', '');
//                        selectPricelistCateg.append(opt);
//                        _.each(data.categories, function (x) {
//                            var opt = $('<option>').text(x[1])
//                                .attr('value', x[0])
//                            selectPricelistCateg.append(opt);
//                        });
//                        selectPricelistCateg.parent('div').show();
//                        $("#category_label").show();
//                        $("#line_label").show();
//                        $(".alert").hide();
////                        selectPricelistCateg.trigger("change");
//                        selectPricelistCateg.selectpicker("refresh");
//                    } else {
//                        selectPricelistCateg.val('').parent('div').hide();
////                        selectLines.val('').parent('div').hide();
//                        $("#category_label").hide();
//                        $("#line_label").hide();
//                        $(".comments").hide();
//                        $(".fees").hide();
//                        $('.alert').show();
//                    }
//                    selectPricelistCateg.data('init', 0);
//                } else {
//                    selectPricelistCateg.data('init', 0);
//                }
//
//            });
//            });
//        });
//        $('input[name="individual"]').on('change', function(ev) {
//            var company = $('#company').val();
//            var individual = $('#individual').is(':checked');
////            var selectLines = $("select[name='pricelist_line']");
//            if(individual == true){
//               selectContacts.parent('div').show();
//               $(".contacts_row").show();
//               selectContacts.attr('required',true);
//               ajax.jsonRpc("/search/contacts",'call',{'individual':individual}).then(function (data) {
//                    console.log('joijojd',data);
//
//                    if (selectContacts.data('init')===0 || selectContacts.find('option').length===1) {
//                        if (data.contacts.length) {
//                            selectContacts.html('');
//                            var opt = $('<option>').text('Select...')
//                                        .attr('value', '');
//                            selectContacts.append(opt);
//                            _.each(data.contacts, function (x) {
//                                console.log('111');
//                                var opt = $('<option>').text(x[1])
//                                    .attr('value', x[0])
////                                    .attr('data-tokens',x[1])
//                                selectContacts.append(opt);
//                            });
//                            selectContacts.parent('div').show();
////                            selectContacts.trigger("change");
//                            $("#contacts").selectpicker("refresh");
//                        } else {
//                            selectContacts.val('').parent('div').hide();
//                        }
//                        selectContacts.data('init', 0);
//                    } else {
//                        selectContacts.data('init', 0);
//                    }
//                });
//            }
//            else {
//                selectContacts.parent('div').hide();
////                $(".contacts_row").hide();
//                selectContacts.attr('required',false);
//            }
//            if(company){
//                console.log($('#individual').prop('checked'),"LL");
//                ajax.jsonRpc("/search/company",'call',{'company':company,'individual':individual}).then(function (result) {
//                    $('#pricelistname').val(result['name']);
//                    $('#pricelist').val(result['id']);
////                    if (category == 'Select...') {
////                        return;
////                    }
//                    ajax.jsonRpc("/search/pricelist",'call',{'pricelist':result['id']}).then(function (data) {
//                    var selectPricelistCateg = $("select[name='pricelist_category']");
//                    if (selectPricelistCateg.data('init')===0 || selectPricelistCateg.find('option').length===1) {
//                        if (data.categories.length) {
//                            selectPricelistCateg.html('');
//                            var opt = $('<option>').text('Select...')
//                                        .attr('value', '');
//                            selectPricelistCateg.append(opt);
//                            _.each(data.categories, function (x) {
//                                var opt = $('<option>').text(x[1])
//                                    .attr('value', x[0])
//                                selectPricelistCateg.append(opt);
//                            });
//                            selectPricelistCateg.parent('div').show();
//                            $("#category_label").show();
//                            $("#line_label").show();
//                            $(".alert").hide();
////                            selectPricelistCateg.trigger("change");
//                            selectPricelistCateg.selectpicker("refresh");
//                        } else {
//                            selectPricelistCateg.val('').parent('div').hide();
////                            selectLines.val('').parent('div').hide();
//                            $("#category_label").hide();
//                            $("#line_label").hide();
//                            $(".comments").hide();
//                            $(".fees").hide();
//                            $(".alert").show();
//                        }
//                        selectPricelistCateg.data('init', 0);
////                        selectLines.data('init', 0);
//                    } else {
//                        selectPricelistCateg.data('init', 0);
////                        selectLines.data('init', 0);
//                    }
//
//                });
//                });
//            }
//
//        });
//        $('select[name="pricelist_line"]').on('change', function(ev) {
//            var pricelist_line = $('select[name="pricelist_line"]');
//            ajax.jsonRpc("/search/pricelistline",'call',{'pricelist_line':pricelist_line.val()}).then(function (data) {
//                console.log(data,"######%$445");
//                if($('input[name="urgent"]').prop('checked')){
//                    $('#fusion_fees').text(data['fusion_urgent']);
//                    $('#govt_fees').text(data['govt_urgent']);
//                }
//                else {
//                    $('#fusion_fees').text(data['fusion']);
//                    $('#govt_fees').text(data['govt']);
//                }
//                console.log("__________========",data['currency']);
//                $('.currency').text(data['currency']);
//                if(data['comments']){
//                    $('#comments').text(data['comments']);
//                    $(".comments").show();
//                }
//                $('.fees').show();
//            });
//        });
        $('input[name="urgent"]').on('change', function(ev) {
            var urgent = $('input[name="urgent"]');
//            var pricelist_line = $('select[name="pricelist_line"]');
//            if(pricelist_line.val()){
//                ajax.jsonRpc("/search/pricelistline",'call',{'pricelist_line':pricelist_line.val()}).then(function (data) {
//                    console.log(data,"######%$445");
//                    if($('input[name="urgent"]').prop('checked')){
//                        $('#fusion_fees').text(data['fusion_urgent']);
//                        $('#govt_fees').text(data['govt_urgent']);
//                    }
//                    else {
//                        $('#fusion_fees').text(data['fusion']);
//                        $('#govt_fees').text(data['govt']);
//                    }
//                    $('.fees').show();
//                });
//            }

        });
//        $('select[name="services"]').on('change', function(ev) {
//            var service = $('select[name="services"]').val();
//            console.log(service);
//            var ta = $('select[name="service_option"]');
//            ajax.jsonRpc("/get/service_options",'call',{'service':service}).then(function (data) {
//                ta.html('');
//                if(!data['new'] && !data['renew'] && !data['manage']){
//                    $("#option_label").hide();
//                    ta.parent('div').hide();
//                }
//                else{
//                    if(data['new']){
//                        var opt = $('<option>').text('New')
//                                .attr('value', 'New');
//                        ta.append(opt);
//                    }
//                    if(data['renew']){
//                        var opt = $('<option>').text('Renew')
//                                .attr('value', 'Renew');
//                        ta.append(opt);
//                    }
//                    if(data['manage']){
//                        var opt = $('<option>').text('Manage')
//                                .attr('value', 'Manage');
//                        ta.append(opt);
//                    }
//                    $("#option_label").show();
//                    ta.parent('div').show();
//                    ta.selectpicker("refresh");
//                }
//
//
//            });
//        });
//        $('select[name="services"]').on('change', function(ev) {
//            var service = $('select[name="services"]').val();
//            console.log(service);
//            var ta = $('select[name="service_option"]');
//            ajax.jsonRpc("/get/service_options",'call',{'service':service}).then(function (data) {
//                ta.html('');
//                if(data['new']){
//                    var opt = $('<option>').text('New')
//                            .attr('value', 'New');
//                    ta.append(opt);
//                    $(".company_input").show();
//                    ajax.jsonRpc("/get/company",'call',{}).then(function (data) {
//                        console.log('data---------',data);
//                        if(data){
//                            selectCompany.html('');
//                            var opt = $('<option>').text(data['company'][0][1])
//                                        .attr('value', data['company'][0][0]);
//                            console.log(opt,"PPP");
//                            selectCompany.append(opt);
//                            selectCompany.selectpicker("refresh");
//                        }
//                    });
//                    $(".company_input").removeClass('d-none');
//                    $(".contact_input").hide();
//                    $(".employee_input").hide();
//                    $(".dependant_input").hide();
//                }
//                if(data['employee']){
//                    var opt = $('<option>').text('Employee')
//                            .attr('value', 'Employee');
//                    console.log(opt,"PPP");
//                    ta.append(opt);
//
//                    if(!data['company']){
//                        $(".employee_input").show();
//                        ajax.jsonRpc("/get/contacts",'call',{'type':'employee'}).then(function (data) {
//                            console.log('data---------',data);
//                            if(data){
//                                selectEmployee.html('');
//                                var opt = $('<option>').text('Select...')
//                                        .attr('value', '');
//                                selectEmployee.append(opt);
//                                _.each(data.contacts, function (x) {
//                                    console.log('111');
//                                    var opt = $('<option>').text(x[1])
//                                        .attr('value', x[0])
//        //                                    .attr('data-tokens',x[1])
//                                    selectEmployee.append(opt);
//                                });
//                                selectEmployee.selectpicker("refresh");
//                            }
//                        });
//                        $(".employee_input").removeClass('d-none');
//                        $(".company_input").hide();
//        //                $(".employee_input").hide();
//                        $(".dependant_input").hide();
//                    }
//                }
//                if(data['visitor']){
//                    var opt = $('<option>').text('Visitor')
//                            .attr('value', 'Visitor');
//                    console.log(opt,"PPP");
//                    ta.append(opt);
//                }
//                if(!data['company'] && !data['employee'] && !data['visitor']){
//                    $(".company_input").hide();
//                    $(".employee_input").hide();
//                    $("#target_label").hide();
//                    ta.parent('div').hide();
//                }
//                else {
//                    $("#target_label").show();
//                    ta.parent('div').show();
//                    ta.selectpicker("refresh");
//                }
//            });
//;
//        });
//        $('select[name="target_audience"]').on('change', function(ev) {
//            var ta = $('select[name="target_audience"]').val();
//            var flag = false;
//            console.log(ta,"@@@");
//            $(".new_row").css("display","block !important");
//            if(ta == 'Company'){
//                $(".company_input").show();
//                ajax.jsonRpc("/get/company",'call',{}).then(function (data) {
//                    console.log('data---------',data);
//                    if(data){
//                        selectCompany.html('');
//                        var opt = $('<option>').text(data['company'][0][1])
//                                    .attr('value', data['company'][0][0]);
//                        console.log(opt,"PPP");
//                        selectCompany.append(opt);
//                        selectCompany.selectpicker("refresh");
//                        flag = true;
//                    }
//                });
//                $(".company_input").removeClass('d-none');
//                $(".contact_input").hide();
//                $(".employee_input").hide();
//                $(".dependant_input").hide();
//            }
//            if(ta == 'Employee'){
//                $(".employee_input").show();
//                ajax.jsonRpc("/get/contacts",'call',{'type':'employee'}).then(function (data) {
//                    console.log('data---------',data);
//                    if(data){
//                        selectEmployee.html('');
//                        var opt = $('<option>').text('Select...')
//                                .attr('value', '');
//                        selectEmployee.append(opt);
//                        _.each(data.contacts, function (x) {
//                            console.log('111');
//                            var opt = $('<option>').text(x[1])
//                                .attr('value', x[0])
////                                    .attr('data-tokens',x[1])
//                            selectEmployee.append(opt);
//                        });
//                        selectEmployee.selectpicker("refresh");
//                        flag = true;
//                    }
//                });
//                $(".employee_input").removeClass('d-none');
//                $(".company_input").hide();
////                $(".employee_input").hide();
//                $(".dependant_input").hide();
//            }
////            else if(type == 'contact'){
////                $(".contact_input").removeClass('d-none');
////                $(".contact_input").show();
////                $(".client_input").hide();
////                $(".employee_input").hide();
////                $(".dependant_input").hide();
////            }
////            else if(type == 'employee'){
////                $(".employee_input").removeClass('d-none');
////                $(".contact_input").hide();
////                $(".client_input").hide();
////                $(".employee_input").show();
////                $(".dependant_input").hide();
////            }
////            else{
////                $(".dependant_input").removeClass('d-none');
////                $(".contact_input").hide();
////                $(".client_input").hide();
////                $(".employee_input").hide();
////                $(".dependant_input").show();
////            }
//            $(".contacts_row").show();
////            var select = selectClients;
////            ajax.jsonRpc("/get/contacts",'call',{'type':$('select[name="partner_type"]').val()}).then(function (data) {
////                    if(data['type'] == 'contact'){
////                        select = selectContacts;
////                    }
////                    if(data['type'] == 'dependant'){
////                        select = selectDependant;
////                    }
////                    if(data['type'] == 'client'){
////                        select = selectClients;
////                    }
////                    if(data['type'] == 'employee'){
////                        select = selectEmployee;
////                    }
////                    select.show();
////                    if (true && !flag) {
////                        if (data.contacts.length) {
////                            select.html('');
////                            var opt = $('<option>').text('Select...')
////                                        .attr('value', '');
////                            select.append(opt);
////                            _.each(data.contacts, function (x) {
////                                console.log('111');
////                                var opt = $('<option>').text(x[1])
////                                    .attr('value', x[0])
////    //                                    .attr('data-tokens',x[1])
////                                select.append(opt);
////                            });
////                            select.parent('div').show();
////    //                            select.trigger("change");
////                            select.selectpicker("refresh");
////                        } else {
////                            select.val('').parent('div').hide();
////                        }
////                        select.data('init', 0);
////                    } else {
////                        select.data('init', 0);
////                    }
////                });
////            }
////            else {
////                select.parent('div').hide();
////                $(".contacts_row").hide();
////                select.attr('required',false);
////            }
//        });
    });
});