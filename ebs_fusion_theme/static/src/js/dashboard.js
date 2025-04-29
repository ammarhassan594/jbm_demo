odoo.define('ebs_fusion_theme.dashboard', function (require) {

    var ajax = require('web.ajax');
    function hide_job_position(residency_type,job_position, job_position_div){
        if ( residency_type.val() == 'family'){
           job_position_div.addClass('d-none');
            job_position.val('');
        }else{
            job_position_div.removeClass('d-none');
        }
    }

    $(document).on('click', '.portal_search_input_field', function(ev) {
        var type = $(this).attr('data-value');
        $('#portal_search_input').attr('type', type);
    });

    $('.sort_by_payment_code').click(function(ev){
        window.location = window.location.origin + '/my/payments'+ '?' + "sortby=name"
    });

    $('.sort_by_payment_date').click(function(ev){
        window.location = window.location.origin + '/my/payments'+ '?' + "sortby=date"
    });

    $('.sort_by_payment_status').click(function(ev){
        window.location = window.location.origin + '/my/payments'+ '?' + "sortby=stage"
    });

    $( "input[name='submit_qid_radio']" ).click(function() {
        $("#employee_userinfo_accordion").removeClass('d-none');
        $("#collapseOne1").removeClass('show');
        if($("#submit_qid_radio_yes").prop('checked') == true){
            $("#employee_qid_accordion").removeClass('d-none');
            $("#collapseThree1").addClass('show');
            //                     $("#update_qid_accordion").collapse('toggle');
            $("#employee_passport_accordion").addClass('d-none');
        }else{
            $("#employee_qid_accordion").addClass('d-none');
            $("#collapseTwo1").addClass('show');
            $("#employee_passport_accordion").removeClass('d-none');
        }
    });

    $(document).on('click', '#submit_new_service_button', function(){
        $.each($(".service_drop_down option:selected"), function () {
            $(this).prop('selected', '');
        });
        $("#qid_radio_yes").prop('checked', false);
        $("#submit_qid_radio_yes").prop('checked', false);
        $("#submit_qid_radio_no").prop('checked', false);
        $("#employee_qid_accordion").addClass('d-none');
        $("#employee_passport_accordion").addClass('d-none');
        $("#employee_userinfo_accordion").addClass('d-none');
        $('.first_page_field').addClass("d-none");
        $('.first_to_second_page_btn').addClass("d-none");
        $('.service_to_employee').addClass("d-none");
        $("#service_radio_section").removeClass("d-none");
        $("body").removeClass("service_form_second_page");
        $("body").removeClass("employee_second_page");
        //         $("#corporate_radio").prop('checked', false);
        //         $("#individual_radio").prop('checked', false);
    });

    $( "#employee_name_english" ).change(function() {
        $('#employee_name_id').val($('#employee_name_english').val());
    });

    $( "#employee_name_ar" ).change(function() {
        $('#employee_name_id_ar').val($('#employee_name_ar').val());
    });

    $( "#employee_passport_name" ).change(function() {
        $('#employee_name_id').val($('#employee_passport_name').val());
    });

    $( "#employee_passport_name_ar" ).change(function() {
        $('#employee_name_id_ar').val($('#employee_passport_name_ar').val());
    });

    $( "#employee_passport_gender" ).change(function() {
        $('#select_gender').val($('#employee_passport_gender').val());
    });

    $( "#employee_passport_nationality" ).change(function() {
        $('#employee_nationality').val($('#employee_passport_nationality').val());
    });

    $( "#employee_qid_nationality" ).change(function() {
        $('#employee_nationality').val($('#employee_qid_nationality').val());
    });

    $( "#employee_job_position" ).change(function() {
        $('#employee_job').val($('#employee_job_position').val());
    });

    $(document).on('click', '.first_to_second_page_btn', function(){
        if($("#service_order_form").valid()){
            $("body").removeClass("service_form_second_page");
            $("body").addClass("service_form_third_page");
            $("#service_radio_section").addClass("d-none");
            $(".service_to_employee").addClass('d-none');
        }
    });

    $(document).on('click', '.second_to_first_page_btn', function(){
    //            $("body").addClass("service_form_first_page");
        if($("#service_order_form").valid()){
            $("body").removeClass("service_form_second_page");
        }
    });

    $(document).on('click', '.third_to_second_page_btn', function(){
        $("body").removeClass("service_form_third_page");
        $("body").removeClass("service_form_second_page");
        $('.first_page_field').removeClass("d-none");
        if($("#individual_radio").prop('checked') == true){
            $(".service_to_employee").removeClass('d-none');
        }
    });

    $(document).on('change', '#select_appointments_team', function(ev) {
        var appointments_crm_team_id = ev.target.value
        var ta = $('#select_member_id');
        ajax.jsonRpc("/get/team_member",'call',{'team':appointments_crm_team_id}).then(function (data) {
            ta.html('');
            var first_option = $('<option>').text('Select Team Member').attr('value', '');
            ta.append(first_option)
            _.each(data.member_ids, function (x) {
                console.log(x);
                var opt = $('<option>').text(x[1])
                    .attr('value', x[0])
                ta.append(opt);
            });
        });
    });

    $(document).on('change', '#select_related_fusion_company', function(ev) {
        var related_fusion_company = $("#select_related_fusion_company").children("option:selected").val()
        var service_order_type = $("#select_service_order_type").children("option:selected").val()
        var ele_list = ["select_service_order_type", "select_related_fusion_company"]
        _.each($(".service_drop_down option:selected"), function () {
            var parent_ele_id = $(this).parent().attr('id');
            if (!ele_list.includes(parent_ele_id)) {
                $(this).prop('selected', '');
            }
        });
        var service_element = $('#select_service_id');
        if (service_order_type && related_fusion_company) {
            ajax.jsonRpc("/get/service_ids",'call',{'service_order_type':service_order_type}).then(function (data) {
                service_element.html('');
                var first_option = $('<option>').text('Select Service').attr('value', '');
                service_element.append(first_option)
                _.each(data.service_ids, function (x) {
                    var opt = $('<option>').text(x[1])
                        .attr('value', x[0])
                    service_element.append(opt);
                });
                service_element.parent('div').show();
            });
            if(service_order_type == 'company' || service_order_type == 'visitor'){
                $("body").removeClass("service_form_second_page");
                $('.first_page_field').removeClass("d-none");
                $('.service_to_employee').addClass("d-none");
                $('.first_to_second_page_btn').removeClass("d-none");
                $("body").removeClass("service_form_second_page");
            }else{
                $("body").addClass("service_form_second_page");
                $(".service_to_employee").addClass('d-none');
                $('.first_page_field').removeClass("d-none");
            }
        }
    });

    $(document).on('change', '#select_service_order_type', function(ev) {
        var related_fusion_company = $("#select_related_fusion_company").children("option:selected").val()
        var service_order_type = $("#select_service_order_type").children("option:selected").val()
        var ele_list = ["select_service_order_type", "select_related_fusion_company"]
        _.each($(".service_drop_down option:selected"), function () {
            var parent_ele_id = $(this).parent().attr('id')
            if (!ele_list.includes(parent_ele_id)) {
                $(this).prop('selected', '');
            }
        });
        var service_element = $('#select_service_id');
        if (service_order_type && related_fusion_company) {
            ajax.jsonRpc("/get/service_ids",'call',{'service_order_type':service_order_type}).then(function (data) {
                service_element.html('');
                var first_option = $('<option>').text('Select Service').attr('value', '');
                service_element.append(first_option)
                _.each(data.service_ids, function (x) {
                    var opt = $('<option>').text(x[1])
                        .attr('value', x[0])
                    service_element.append(opt);
                });
                service_element.parent('div').show();
            });
            if(service_order_type == 'company' || service_order_type == 'visitor'){
                $("body").removeClass("service_form_second_page");
                $('.first_page_field').removeClass("d-none");
                $('.service_to_employee').addClass("d-none");
                $('.first_to_second_page_btn').removeClass("d-none");
                $("body").removeClass("service_form_second_page");
            }else{
                $("body").addClass("service_form_second_page");
                $(".service_to_employee").addClass('d-none');
                $('.first_page_field').removeClass("d-none");
            }
        }
    });

    $(document).on('click', '.second_to_third_page_btn', function(){
        if($("#service_order_form").valid()){
            $("body").removeClass("service_form_second_page");
            $('.first_page_field').removeClass("d-none");
            $('.service_to_employee').removeClass("d-none");
            $('.first_to_second_page_btn').removeClass("d-none");
            $("#select_service_id").next().remove();
            $("#select_service_id").removeClass("error");
        }
    });

    $(".service_to_employee").click(function(){
        $("body").addClass("service_form_second_page");
        $(".service_to_employee").addClass("d-none");
    });

    $(".new_employee_btn_to_third_page").click(function(){
        if($("#service_order_form").valid()){
            $("body").removeClass("employee_second_page");
            $('.first_page_field').removeClass("d-none");
            $('.service_to_employee').removeClass("d-none");
            $('.first_to_second_page_btn').removeClass("d-none");
            $("#select_service_id").next().remove();
            $("#select_service_id").removeClass("error");
        }
    });

    $(".third_to_second_page_btn").click(function(){
        $("#service_radio_section").removeClass("d-none");
    });

    $(document).on('click', '.new_employee_id', function(){
        $("body").addClass("employee_second_page");
        $("body").removeClass("service_form_second_page");
    });

    $(document).on('click', '.exiting_employee_id', function(){
        $("body").addClass("service_form_second_page");
        $("body").removeClass("employee_second_page");
    });

    $(document).on('click', '.new_employee_btn_to_first_page', function(){
    //             $("body").addClass("service_form_third_page");
        if($("#service_order_form").valid()){
            $("body").removeClass("employee_second_page");
        }
    });

    $(document).on('change', '#select_employee_id', function(ev){
        var employee = ev.target.value
        if (employee == '') {
            $('.first_page_field').addClass("d-none");
        }
        else {
            $('.first_page_field').removeClass("d-none");
        }
    });


    $(document).on('change', '#select_service_id', function(ev){
        var service = ev.target.value
        var related_company = $("#select_related_fusion_company").children("option:selected").val();
        var ta = $('#select_options_id');

        ajax.jsonRpc("/get/service_options",'call',{'service':service, 'related_company':related_company}).then(function (data) {
            ta.html('');
            var first_option = $('<option>').text('Select service option').attr('value', '');
            ta.append(first_option)
            _.each(data.option_ids, function (x) {
                console.log(x);
                var opt = $('<option>').text(x[1])
                    .attr('value', x[0])
                ta.append(opt);
            });
            ta.parent('div').show();
            $(".select_options_label_class").show();
            if (!data['depend_service_list'][0]) {
                $(".depend_service_div_class").hide();
                $(".depend_ul_service_class").empty();

            }
            else{
                $(".depend_service_div_class").show();
                $(".depend_ul_service_class").empty();
                $('.depend_service_title').empty();
                for ( i = 0; i < data['depend_service_list'].length; i++) {
                    $(".depend_ul_service_class").append("<b><li class='depend_ul_li_service_class' rel="+ [i] +">"+data['depend_service_list'][i]+"</li></b>");
                }
                $('.depend_service_title').append('<span>The following services will be initiated</span>');
            }
        });
    });

    $(document).on('change', '#select_options_id', function(ev) {
        var option_id = ev.target.value;
        var urgent = $("#select_urgent_id").children("option:selected").val()
        ajax.jsonRpc("/get/service_options_fees",'call',{'service_option':option_id, 'urgent':urgent}).then(function (data) {
            $('#govt_fees').val(data.govt_fees);
            $('#fusion_fees').val(data.fusion_fees);
        });
    });

    $(document).on('change', '#select_urgent_id', function(ev) {
        var urgent = ev.target.value;
        if (urgent == 'yes') {
            $('.urgent_msg').removeClass("d-none");
        }
        else {
            $('.urgent_msg').addClass("d-none");
        }

        var option_id = $("#select_options_id").children("option:selected").val()
        ajax.jsonRpc("/get/service_options_fees",'call',{'service_option':option_id, 'urgent':urgent}).then(function (data) {
            $('#govt_fees').val(data.govt_fees);
            $('#fusion_fees').val(data.fusion_fees);
        });
    });

//    $(document).on('click', '.submit_service_btn', function(ev){
//        var form = $("#service_order_form");
//        var data = new FormData(form[0]);
//        $.ajax({
//            type: 'POST',
//            url: form.attr('action'),
//            data: data,
//            processData: false,
//            contentType: false,
//            dataType: "json",
//            success: function(result) {
//                window.location.href = window.location.origin + '/my/service_orders';
//            }
//        });
//    });

    // job position hide new service
    $( "#employee_residency_type" ).change(function() {
        hide_job_position($('#employee_residency_type'),$('#employee_job_position'), $('#employee_job_position_div'))
    });

    $(document).on("click", ".pay_proforma_invoice", function (ev) {
         var payment_id = ev.target.id;
         $(".modal-body #proforma_invoice_id").val(payment_id);
         $(".modal-body #payment_amount").val(ev.target.value);
    });

    $(document).on('click', '#confirm_proforma_invoice', function(ev){
        var payment_id = $('#proforma_invoice_id').val()
        ajax.jsonRpc('/confirm_proforma_invoice', 'call', {
            'payment_id': payment_id,
        }).then(function(result){
            location.reload();
        });
    });

    $(document).on('click', '#confirm_appointment', function(ev){
        var member_id = $('#select_member_id').val()
        console.log('99999999member_id',member_id)
        if ($('#appointments_form').valid()) {
            ajax.jsonRpc('/confirm_appointment', 'call', {
                'member_id': member_id,
            }).then(function(result){
                $("#before_appointment_confirm_msg").addClass('d-none');
                $("#confirm_appointment").addClass('d-none');
                $("#appointment_confirm_msg").removeClass('d-none');
                $("#close_appointment_modal").removeClass('d-none');
            });
        }
    });


    $(document).on("click", ".pay_invoice", function (ev) {
         var invoice_id = ev.target.id;
         $(".modal-body #invoice_id").val(invoice_id);
         $(".modal-body #invoice_amount").val(ev.target.value);
    });

    $(document).on('click', '#confirm_invoice', function(ev){
        var invoice_id = $('#invoice_id').val()
        ajax.jsonRpc('/confirm_invoice', 'call', {
            'invoice_id': invoice_id,
        }).then(function(result){
            location.reload();
        });
    });

});