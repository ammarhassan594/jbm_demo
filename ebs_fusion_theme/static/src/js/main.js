// Example starter JavaScript for disabling form submissions if there are invalid fields
odoo.define('ebs_fusion_theme.portal_theme', function (require) {

var ajax = require('web.ajax');
var rpc = require('web.rpc');
var form = $("#form-register");




$(function(){

    var primary_person = [];
    var person = [];
    var partner = [];
    var manager = [];
    var authorizer = [];

     $(document).on("click","#open_model_contact_person,#open_model_primary_contact_person,#open_model_partner,#open_model_manager,#open_model_authoriser", function () {
//         $(".underline_new_contact").addClass("d-none");
         $(".underline_exiting_contact").removeClass("d-none");
//         $(".next_btn").removeClass("d-none");
         $('.underline_exiting_contact').addClass('contact_underline');
         $('#new_contact_form').addClass('d-none');
         $('#exiting_contact_form').removeClass('d-none');
         $('.underline_new_contact').removeClass('contact_underline');
         $('.create_exists_contact_person').removeClass('d-none');
         $('.create_new_contact_person').addClass('d-none');
         $("#exampleModalContactPerson").modal("show");
         $.each($(".drop_down"), function () {
            $(this).prop('selectedIndex', false);
        });
     });

     $(document).on("click","#remove_manager_file_table", function () {
        $("#manager_in_charge_passport_document").removeClass('d-none');
        $("#file_name_table_commercial_license_contact").addClass('d-none');
     });
     $(document).on("click","#remove_manager_file_table_qid", function () {
        $("#manager_in_charge_qid_document").removeClass('d-none');
        $("#file_name_table_commercial_license_contact_cl_qid").addClass('d-none');
     });

    $(document).on("click","#update_remove_manager_file_table_passport", function () {
        $("#update_passport_document_extra_contact").removeClass('d-none');
        $("#file_name_table_commercial_license_contact_passport").addClass('d-none');
     });
     $(document).on("click","#update_remove_manager_file_table_qid", function () {
        $("#update_qid_document_extra_contact").removeClass('d-none');
        $("#file_name_table_commercial_license_contact_qid").addClass('d-none');
     });
     $(document).on("click",".remove_passport_file_table_contract", function () {
        a = $(".remove_passport_file_table_contract").closest('.ndn_input_hidden_id').find(".input_hidden_id").val()
        $("#"+a+"-contract_passport_document").removeClass('d-none');
        $("#"+a+"-contract_passport_table").addClass('d-none');
     });
     $(document).on("click",".remove_qid_file_table_contract", function () {
        a = $(".remove_qid_file_table_contract").closest('.ndn_input_hidden_id').find(".input_hidden_id").val()
        $("#"+a+"-contract_qid_document").removeClass('d-none');
        $("#"+a+"-contract_qid_table").addClass('d-none');
     });
    if($('input[name="error_msg"]').val()){
        console.log("$$$$$$$################",$('input[name="error_msg"]').val());
        $("#exampleModalError").modal("show");
//        $("#error_msg_body").empty();
    }
    function clear_value(nationality,date,name){

            nationality.prop('selectedIndex',false);
//            nationality.val([]);
            date.val("");
            name.val("");
    }
    function check_validation(value,clr_value){
        ajax.jsonRpc("/date_name_nationality/checker",'call',value).then(function (data) {
            console.log("dataaaaaaaaa",data);
               if(data){
                    $("#error_msg_body").empty();
                    console.log("data found ",data);
                    var warning = document.createElement("p");
                    warning.innerHTML = "A contact with the same name, birth date and nationality already exists."
                    $("#error_msg_body").append(warning);
                    $("#exampleModalContactPerson").modal("hide");
                    $("#update_contact_person_modal").modal("hide");
                    $("#exampleModalError").modal("show");
                    clear_value(clr_value['na'],clr_value['date'],clr_value['name'])
               }
        });
    }
    $(document).on("click",".service_checkbox", function () {
           console.log($(this).parent().find(".service_status").children()[0].innerText.trim());
        if(!$(this).parent().find(".service_status").children()[0].innerText.trim()){
            $(this).parent().find(".service_status").children()[0].innerText = "Awaiting Approval";
        }
        if($(this).prop('checked') == true){
            $(this).parent().find(".service_status").removeClass("d-none")
        }else{
            $(this).parent().find(".service_status").addClass("d-none")
        }
     });
    function call_on_change_validation(nationality, birth_date, name){
        if ( nationality.val() != "" && birth_date.val() != "" && name.val() != ""){
               value = {
                'nationality': nationality.val(),
                'birth_date': birth_date.val(),
                'name': name.val(),
                }
                clr_value = {
                    'na':nationality,
                    'date':birth_date,
                    'name':name,
                }
                check_validation(value,clr_value)
            }
    }
    $(document).on("change",".ndn_validation1", function () {
        a = $("#"+this.id).closest('.ndn_input_hidden_id').find('.input_hidden_id').val().trim();
        call_on_change_validation($('#'+a+'-contract_qid_nationality'),$('#'+a+'-contract_qid_birth_date'),$('#'+a+'-contract_name_english'))
    });
    $(document).on("change",".ndn_validation", function () {
        a = $("#"+this.id).closest('.ndn_input_hidden_id').find('.input_hidden_id').val().trim();
        call_on_change_validation($('#'+a+'-contract_nationality'),$('#'+a+'-contract_birth_date'),$('#'+a+'-contract_passport_name'))
    });

    $("#erase_client_err_msg").on('click',function(){
        ajax.jsonRpc("/set/client_err_msg",'call',{"last_client_value":$("#last_client_hidden_value").val()})
    });


    $(document).on('change', '#manager_in_charge_qid_nationality,#manager_in_charge_qid_birth_date,#manager_in_charge_name_english', function(){
            call_on_change_validation($('#manager_in_charge_qid_nationality'),$('#manager_in_charge_qid_birth_date'),$('#manager_in_charge_name_english'))

    });
    $(document).on('change', '#manager_in_charge_nationality,#manager_in_charge_birth_date,#manager_in_charge_passport_name', function(){
            call_on_change_validation($('#manager_in_charge_nationality'),$('#manager_in_charge_birth_date'),$('#manager_in_charge_passport_name'))

    });

    $(document).on('change', '#qid_nationality_extra_contact,#qid_birth_date_extra_contact,#name_english_extra_contact', function(){
             call_on_change_validation($('#qid_nationality_extra_contact'),$('#qid_birth_date_extra_contact'),$('#name_english_extra_contact'))

    });
    $(document).on('change', '#nationality_extra_contact,#birth_date_extra_contact,#passport_name_extra_contact', function(){
        call_on_change_validation($('#nationality_extra_contact'),$('#birth_date_extra_contact'),$('#passport_name_extra_contact'))

    });
    $(document).on('change', '#update_nationality_extra_contact,#update_birth_date_extra_contact,#update_passport_name_extra_contact', function(){
        call_on_change_validation($('#update_nationality_extra_contact'),$('#update_birth_date_extra_contact'),$('#update_passport_name_extra_contact'))

    });
    $(document).on('change', '#update_qid_nationality_extra_contact,#update_qid_birth_date_extra_contact,#update_name_english_extra_contact', function(){
        call_on_change_validation($('#update_qid_nationality_extra_contact'),$('#update_qid_birth_date_extra_contact'),$('#update_name_english_extra_contact'))

    });

    function remove_next_button(){
        $('ul[aria-label=Pagination] input[value="Submit"]').remove();
        $('ul[aria-label=Pagination] a[href="#next"]').remove();
        var $input = $('<input  id="submit_button" type="submit" class="submit_button" value="Submit" />');
        $input.appendTo($('ul[aria-label=Pagination]'));
        if ($('.current-info').next().children()[1]){
            $("#hidden_input_current_page_id").val($('.current-info').next().children()[1].innerHTML);
            if ($('.current-info').next().children()[1].innerHTML == "Summary"){
                $('ul[aria-label=Pagination] input[value="Submit"]').remove();
            }
        }
    }
    jQuery.validator.addMethod("emailExt", function(value, element, param) {
         return value.match(/^[a-zA-Z0-9_\.%\+\-]+@[a-zA-Z0-9\.\-]+\.[a-zA-Z]{2,}$/);
     },'Please enter valid email address.');
    $(document).on("click",".title", function () {
         remove_next_button()
        if ($('.current-info').next().children()[1]){
            $("#hidden_input_current_page_id").val($('.current-info').next().children()[1].innerHTML);
        }
    });

    $("#no_of_branches").defaultValue = "0";


    var main_data = false;
    var activity_ids_list = [];
    hide_unhide_table_header();

    $("#form-register").validate({
//    debug: true,
        invalidHandler: function(form, validator) {
            var errors = validator.numberOfInvalids();
            console.log(validator.errorList,"@@@@@########");
             if (errors) {
                validator.errorList[0].element.focus();
                for (var i=0;i<validator.errorList.length;i++){
//                    if(validator.errorList[i].element.id ==  'fileelem_name3'){
//                        alert("please add document");
//                    }
                    $(validator.errorList[i].element).closest('.collapse').collapse('show');
                }
            }
        },
    //    errorPlacement: function errorPlacement(error, element) {

    //    error.appendTo(element.closest("form-group").prev());
    //     },
        ignore: function (index, el) {
         var $el = $(el);
         if ($el._id() == "primary_in_charge_job_position"&& $('#primary_in_charge_residency_type').val() && $("#primary_qid_radio_yes").prop('checked')){
           if ($('#primary_in_charge_residency_type').val() == "family"){
            return true
           }else{
            return false
           }
       }

        if ($el.parents('.user_information_section_validation').length) {
            if ($("#primary_qid_radio_no").prop('checked')) {
                if ($el.parents('.qid_section_user').length) {
                   return true;
                }
           }
           else if ($("#primary_qid_radio_yes").prop('checked')) {
                if ($el.parents('.passport_section_user').length) {
                   return true;
                }
           }
          }
           else if($el.parents('.commercial_registration_section_validation').length){
           if($('.current-info').next().children()){
            if($('.current-info').next().children()[1].innerHTML == 'Commercial Registration'){
                 if($('#fileelem_name').val() == ''){
                    return false;
                }
                return false;
            }else{
            return true;
            }
            }
            else{
            return true;
            }
           }
           else if($el.parents('.establishment_card_section_validation').length){
               if($('.current-info').next().children()[1]){
                   if($('.current-info').next().children()[1].innerHTML == 'Establishment Card'){
                        if($('#fileelem_name4').val() == ''){
                                return false;
                            }
                    }else{
                        return true;
                    }
               }else{
                   return true;
               }

           }
           else if($el.parents('.commercial_license_section_validation').length){
           if($('.current-info').next().children()){
            if($('.current-info').next().children()[1].innerHTML == 'Commercial License'){

                if($('#fileelem_name3').val() == ''){
                    return false
                }
                 if ($el._id() == "manager_in_charge_job_position"&& $('#manager_in_charge_residency_type').val() && $("#manager_qid_radio_yes").prop('checked')){
                       if ($('#manager_in_charge_residency_type').val() == "family"){
                        return true
                       }else{
                        return false
                       }
                 }

            if ($("#manager_qid_radio_no").prop('checked')) {
                if ($el.parents('.qid_section_manager').length) {
                   return true;
                }
                if ($el.parents('.user_section_manager').length) {
                   return false;
                }
           }
           else if ($("#manager_qid_radio_yes").prop('checked')) {

                if ($el.parents('.passport_section_manager').length) {
                   return true;
                }
                if ($el.parents('.user_section_manager').length) {
                   return false;
                }
           }

            }else{
            return true;
            }
            }else{
            return true;
            }

           }
           else if($el.parents('.national_address_section_validation').length){
           if($('.current-info').next().children()){
            if($('.current-info').next().children()[1].innerHTML == 'National Address'){
                return false;
            }else{
            return true;
            }
            }
             else{
            return true;
            }
           }
           else if($('.current-info').next().children()[1]){
           if($('.current-info').next().children()[1].innerHTML == 'Contract Info'){
                if ($el._id()){
                   var check_id =  $el._id().toString()[0]
                   if (typeof(parseInt((check_id.charAt(0)))) == "number"){
                   var contract_id =  $el._id().split('-')[0];
                       if( $("#"+$el._id()).closest('.'+contract_id+'-contract_client').length){
                                 if ($el._id() == contract_id+"-contract_job_position"&& $('#'+contract_id+'-contract_residency_type').val() && $('#'+contract_id+'-contract_qid_radio_yes').prop('checked')){
                                   if ($('#'+contract_id+'-contract_residency_type').val() == "family"){
                                    return true;
                                   }else{
                                    return false;
                                   }
                                 }
                                if ($('#'+contract_id+'-contract_qid_radio_no').prop('checked')) {
                                    if ($el.parents('.'+contract_id+'-qid_section_contract').length) {
                                       return true;
                                    }
                                     if ($("#"+$el._id()).parents('.'+contract_id+'-user_section_contract').length) {
                                       return false;
                                     }
                                     else{
                                        return $el.is(':hidden');
                                     }
                               }
                               else if ($('#'+contract_id+'-contract_qid_radio_yes').prop('checked')) {
                                    if ($el.parents('.'+contract_id+'-passport_section_contract').length) {
                                       return true;
                                    }
                                     if ($("#"+$el._id()).parents('.'+contract_id+'-user_section_contract').length) {
                                       return false;
                                    }
                                    else{
                                        return $el.is(':hidden');
                                    }
                               }
                               else{
                                      return $el.is(':hidden');
                               }
                       }
                   }else{
                        return true;
                   }
               }

           }
           else{
                return $el.is(':hidden');
           }
           }
           else{
                return true;
           }
           },
           rules:{
                 primary_in_charge_gender: {required:true,},
                primary_in_charge_name_english: {required:true,},
                primary_in_charge_qid_name_ar: {required:true,},
                primary_in_charge_qid_nationality: {required:true,},
                primary_in_charge_qid_birth_date: {required:true,},
                primary_in_charge_qid_expiry_date: {required:true,},
                primary_in_charge_residency_type:{required:true,},
                primary_in_charge_job_position:{required:true,},
                primary_in_charge_email: {
                required:true,
                emailExt:true,
                },
                primary_in_charge_phone: {required:true,number:true},
                primary_in_charge_permission: {required:true,},
                primary_in_charge_qid: {
                    required:true,
                    minlength:11,
                    maxlength:11,
                },
                primary_in_charge_passport_name:{required:true,},

                primary_in_charge_passport_name_ar: {required:true,},
                primary_in_charge_passport_type: {required:true,},
                primary_in_charge_passport: {required:true},
                primary_in_charge_birth_date: {required:true,},
                primary_in_charge_date_of_issue: {required:true,},
                primary_in_charge_email: {
                required:true,
                emailExt:true,
                },
                primary_in_charge_phone: {required:true,number:true},
                primary_in_charge_permission: {required:true,},
                primary_in_charge_expiry_date: {required:true,},
                primary_in_charge_nationality: {required:true,},
//                'card mb-2 shadow-lg' if primary_contact else 'card mb-2 shadow-lg d-none'
                 commercial_reg_no: {required:true,number:true,},
                trade_name: {required:true,},
                trade_name_ar: {required:true,},
                commercial_registration_file_name: {required:true,},
                commercial_license_file_name: {required:true,},
                establishment_card_file_name: {required:true,},
                tax_reg_no: {required:true,number:true,},
                na_zone: "required",
                na_building: "required",
                na_street: "required",
                license_number: {required:true,number:true,},

                est_id: {number:true},
                update_full_name_extra_contact: "required",
                update_phone_extra_contact: {required:true,number:true},
                update_email_extra_contact: {
                required:true,
                emailExt:true,
                },

                contract_start_date: {required:true},
                contract_end_date: {required:true},
                contract_full_name: {required:true},
                contract_phone: {required:true},
                contract_email: {
                required:true,
                emailExt:true,
                },

                manager_in_charge_passport: {required:true},
                manager_in_charge_passport_name: {required:true},
                manager_in_charge_passport_name_ar: {required:true},
                manager_in_charge_birth_date: {required:true},
                manager_in_charge_gender: {required:true},
                manager_in_charge_passport_type: {required:true},
                manager_in_charge_nationality: {required:true},
                manager_in_charge_date_of_issue: {required:true},
                manager_in_charge_expiry_date: {required:true},

                manager_in_charge_qid: {required:true},
                manager_in_charge_name_english: {required:true},
                manager_in_charge_qid_nationality: {required:true},
                manager_in_charge_qid_birth_date: {required:true},
                manager_in_charge_residency_type: {required:true},
                manager_in_charge_qid_expiry_date: {required:true},
                manager_in_charge_job_position: {required:true},

                manager_in_charge_email: {
                required:true,
                emailExt:true,
                },
                manager_in_charge_phone:  {required:true,number:true},
                manager_in_charge_permission: {required:true},
                },
//        messages:
     });

    stepWizard = $("#form-total").steps({
        headerTag: "h2",
        bodyTag: "section",
        transitionEffect: "fade",
        enableAllSteps: false,
        enablePagination: true,
        enableFinishButton: false,
        autoFocus: true,
        transitionEffectSpeed: 500,
        titleTemplate : '<div class="title">#title#</div>',
        labels: {
            previous : 'Back',
            next : 'Next',
            finish : 'Confirm',
            current : ''
        },
        onStepChanging: function (event, currentIndex, newIndex) {
            if (!$("#form-register").valid()){
                return false;
            }
             if (newIndex === 7){
             console.log("this is on step 8");
                $('ul[aria-label=Pagination] input[value="Submit"]').remove();
            }
//            $("input[name='contract_page']").val(false);
            if (newIndex === 5 || newIndex === 6) { //services catalog
                $('ul[aria-label=Pagination] input[value="Submit"]').remove();
               var $input = $('<input  id="submit_button" type="submit" class="submit_button" value="Submit" />');
                  $input.appendTo($('ul[aria-label=Pagination]'));
            }
            else {
               $('ul[aria-label=Pagination] input[value="Submit"]').remove();
//                $('ul[aria-label=Pagination] a[href="#next"]').css('background-color','#b79854');
//                $("input[name='contract_page']").val(false);
                  $('ul[aria-label=Pagination] a[href="#next"]').remove();
                  var $input = $('<input  id="submit_button" type="submit" class="submit_button" value="Submit" />');
                  $input.appendTo($('ul[aria-label=Pagination]'));
//                return $("#form-register").valid();
            }
            if (newIndex === 6){
                $("input[name='contract_page']").val(true);
            }
            else{
                $("input[name='contract_page']").val(false);
            }
             $(".classToValidate").each(function () {
                    if ($(this).hasClass('phone')){
                         $(this).rules('add', {
                            required: true,
                            number: true
                        });
                    }
                    if ($(this).hasClass('qid')){

                         $(this).rules('add', {
                            required:true,
                            minlength:11,
                            maxlength:11,
                        });

                    }else{
                         if ($(this).attr("type") == "email"){
                            $(this).rules('add', {
                                required: true,
                                emailExt: true,
                            });
                         }else{
                            $(this).rules('add', {
                                required: true,
                            });
                         }
                    }
                });
            return $("#form-register").valid();
//            return true;
        },
    });
     $(".last_client_value").on('click',function(){
        $("#selected").text(this.innerHTML.trim())
        $("#last_client_hidden_value").text(this.value);
        ajax.jsonRpc("/set/last_client_value",'call',{"last_client_value":this.value}).then(function (data) {
            window.location.replace("/my");
         });
    });
     function create_error_message(){
            var warning = document.createElement("p");
            warning.innerHTML = "There is no record!"
            warning.classList.add('text-danger');
            warning.classList.add('text-center');
            return warning
     }
     $("#activity_search_btn").on('click',function(){
         $("#search_result_activity_section p").remove();
            if ($("#activity_search").val().trim()){
            if($('#activity_name').val()){
                $("#activity_name").find("option[value="+$('#activity_name').val()+"]").attr("selected", false);
            }
                ajax.jsonRpc("/search/activity",'call',{"name":$("#activity_search").val().trim()}).then(function (data) {
                    if (data){
                        if (data['activity_code']){
                           $("#activity_name").find("option[value="+data['activity_code']+"]").attr("selected", "selected");
                        }
                        else if (data['activity_name']){
                             $("#activity_name").find("option[value="+data['activity_name']+"]").attr("selected", "selected");
                        }
                        else{
                            var error = create_error_message()
                            $('#search_result_activity_section').append(error);
                        }
                    }
                 });
             }
    });
    $("#submit_contract_button").click(function(ev){
     if ($("#form-register").valid()){
        var form = $("#form-register");
        var data = new FormData(form[0]);

        data['contract'] = true;

         $.ajax({
            type: 'POST',
            url: form.attr('action'),
            data: data,
            processData: false,
            contentType: false,
            dataType: "json",
            success: function(result) {
                console.log('form submitted !!!!!!!!!1 -return data ggggggggggggg');
//                row = create_new_row_record(result);
//                $('#table_body_manager').append(row);
//                hide_unhide_table_header();
//                $("#exampleModal_manager").modal("toggle");
            }
         });
         }

    });
    function nextUpWizard(number){
        for(var i=0; i<number; i++) {
                stepWizard.steps("next");
        }
    }
    var urlParams = new URLSearchParams(window.location.search);
    if(urlParams.get('ui')=='true'){
        nextUpWizard(1);
    }
    if(urlParams.get('cr')=='true'){
        nextUpWizard(2);
    }
    if(urlParams.get('cl')=='true'){
        nextUpWizard(3);
        ajax.jsonRpc("/get/authorizer",'call').then(function (data) {
            if (data['auth_ids']){
                authorizer = authorizer.concat(data['auth_ids'])
                $('#authorizer_input').val(JSON.stringify(authorizer));
            }
         });

    }
    if(urlParams.get('ec')=='true'){
        nextUpWizard(4);
    }
    if(urlParams.get('na')=='true'){
        nextUpWizard(5);
    }
    if(urlParams.get('submitted')=='true'){
        nextUpWizard(6);
    }
    if(urlParams.get('summary')=='true'){
        nextUpWizard(7);
    }

    $(".form-register .form-group").hover(function(ev){
        if ($(this).find("input") && !$(this).find("input").hasClass('date_picker')){
            $(this).find("input").focus();
        }
    });
    $("#exampleModalContactPerson .form-group").hover(function(ev){
        if ($(this).find("input") && !$(this).find("input").hasClass('date_picker')){
            $(this).find("input").focus();
        }
    });
    $("#update_contact_person_modal .form-group").hover(function(ev){
        if ($(this).find("input") && !$(this).find("input").hasClass('date_picker')){
            $(this).find("input").focus();
        }
    });


    $("#new_contact").validate({
        invalidHandler: function(form, validator) {
            var errors = validator.numberOfInvalids();
            if (errors) {
                validator.errorList[0].element.focus();
                for (var i=0;i<validator.errorList.length;i++){
                    console.log("collapse show");
                    // "uncollapse" section containing invalid input/s:
                    $(validator.errorList[i].element).closest('.collapse').collapse('show');
                }
            }
        },
        ignore: function (index, el) {
           var $el = $(el);

           if ($el.parents('.validate_section').length) {
               return false;
           }
           else if ($("#qid_radio_no").prop('checked')) {

                if ($el.parents('.qid_section').length) {
                   return true;
                }

           }
           else if ($("#qid_radio_yes").prop('checked')) {

                if ($el.parents('.passport_section').length) {
                   return true;
                }

           }
           else{
                return $el.is(':hidden');
           }

           // Default behavior

        },
        rules: {
            passport_name_extra_contact: "required",
            passport_name_ar_extra_contact: "required",
            birth_date_extra_contact: "required",
            gender_extra_contact: "required",
            passport_type_extra_contact: "required",
            date_of_issue_extra_contact: "required",
            nationality_extra_contact: "required",
            expiry_date_extra_contact: "required",
            qid_extra_contact: {
                required:true,
                minlength:11,
                maxlength:11,
            },
            name_english_extra_contact: "required",
            name_ar_extra_contact: "required",
            qid_birth_date_extra_contact: "required",
            qid_nationality_extra_contact: "required",
            qid_expiry_date_extra_contact: "required",
            sponsor_name_extra_contact: "required",
            residency_type_extra_contact: "required",
            qid_document_extra_contact: "required",
            email_extra_contact: {
                required:true,
                emailExt:true,
                },
            phone_extra_contact: {required:true,number:true},
            passport_extra_contact: "required",
            passport_document_extra_contact: "required",

        }
    });

    $("#update_contact").validate({
        invalidHandler: function(form, validator) {
            var errors = validator.numberOfInvalids();
            if (errors) {
                validator.errorList[0].element.focus();
                for (var i=0;i<validator.errorList.length;i++){
                    console.log("collapse show");
                    // "uncollapse" section containing invalid input/s:
                    $(validator.errorList[i].element).closest('.collapse').collapse('show');
                }
            }
        },
        ignore: function (index, el) {
           var $el = $(el);

           if ($el.parents('.validate_section').length) {
               return false;
           }
           else if ($("#update_qid_radio_no").prop('checked')) {
                if ($el.parents('.update_qid_section').length) {
                   return true;
                }
           }
           else if ($("#update_qid_radio_yes").prop('checked')) {
                if ($el.parents('.update_passport_section').length) {
                   return true;
                }
           }
           else{
                return $el.is(':hidden');
           }
           // Default behavior

        },
        rules: {
            update_passport_extra_contact:"required",
            update_passport_name_extra_contact:"required",
            update_passport_name_ar_extra_contact:"required",
            update_birth_date_extra_contact:"required",
            update_gender_extra_contact:"required",
            update_passport_type_extra_contact:"required",
            update_nationality_extra_contact:"required",
            update_date_of_issue_extra_contact:"required",
            update_expiry_date_extra_contact:"required",


            update_qid_extra_contact:{
                    required:true,
                    minlength:11,
                    maxlength:11,
            },
            update_name_english_extra_contact:"required",
            update_name_ar_extra_contact:"required",
            update_qid_nationality_extra_contact:"required",
            update_residency_type_extra_contact:"required",
            update_job_position_extra_contact:"required",
            update_qid_expiry_date_extra_contact:"required",


            update_email_extra_contact:{
                required:true,
                emailExt:true,
                },
            update_phone_extra_contact:"required",
            update_extra_contact_permission:"required",

        }
    });
    $("#service_order_form").validate({
        rules: {
            service_id: "required",
            employee_phone_number: {number:true,}

        }
    });
    $("#new_partner").validate({
        invalidHandler: function(form, validator) {
            var errors = validator.numberOfInvalids();
            if (errors) {
                validator.errorList[0].element.focus();
            }
        },
        rules: {
            full_name_extra_partner: "required",
            email_extra_partner: "required",
            phone_extra_partner: {required:true,number:true},
            passport_extra_partner: "required",
            passport_document_extra_partner: "required",
        }
    });
    $("#new_manager").validate({
        invalidHandler: function(form, validator) {
            var errors = validator.numberOfInvalids();
            if (errors) {
                validator.errorList[0].element.focus();
            }
        },
        rules: {
            full_name_extra_manager: "required",
            email_extra_manager: "required",
            phone_extra_manager: {required:true,number:true},
            passport_extra_manager: "required",
            passport_document_extra_manager: "required",
        }
    });
    var extra_manager_name_list = [];
    var extra_activity_name_list = [];
    var extra_partner_list = [];
    var extra_contact_person_list = [];
    manager_radio_click();
    function manager_radio_click(){
    $("#person_accordionLicense").removeClass('d-none');
    $("#collapseOneLicense").removeClass('show');
    if($("#manager_qid_radio_yes").prop('checked') == true){
             $("#qid_accordionLicense").removeClass('d-none');
             $("#collapseThreeLicense").addClass('show');
             $("#passport_accordionLicense").addClass('d-none');
        }else{
            $("#qid_accordionLicense").addClass('d-none');
            $("#collapseTwoLicense").addClass('show');
            $("#passport_accordionLicense").removeClass('d-none');
        }
    }
    function create_new_row_record(result){
        var row = document.createElement("tr");
                    var full_name = document.createElement("td");
                    var phone = document.createElement("td");
                    var email = document.createElement("td");
                    var passport = document.createElement("td");
                    var qid_no = document.createElement("td");
//                    var visa = document.createElement("td");
                    var permission = document.createElement("td");
                    var id = document.createElement("td");

                    if(result['name']){
                    full_name.innerHTML =result['name'];
                    }
                    if (result['mobile']){
                    phone.innerHTML = result['mobile'];
                    }
                    if(result['email']){
                        email.innerHTML =result['email'];
                    }
                    if (result['qid_resident'] == true){
                        if (result['qid_ref_no']){
                        qid_no.innerHTML = result['qid_ref_no'];
                        }
                    }else{
                        if (result['ps_passport_ref_no']){
                            passport.innerHTML = result['ps_passport_ref_no'];
                        }
                    }



//                    visa.innerHTML = result['visa_ref_no'];
                    if (result['permission']){
                        permission.innerHTML = result['permission'].charAt(0).toUpperCase() + result['permission'].slice(1);
                    }


                    id.innerHTML = result['id'];
                    id.classList.add("d-none");
                    row.appendChild(full_name);
                    row.appendChild(phone);
                    row.appendChild(email);
                    row.appendChild(passport);
                    row.appendChild(qid_no);
//                    row.appendChild(visa);
                    row.appendChild(permission);

                    var icon_td = document.createElement("td");
                    var i = document.createElement("i");
                    i.classList.add("fas");
                    i.classList.add("fa-trash");
                    i.classList.add("icon");
                    var icon_td2 = document.createElement("td");
                    var i2 = document.createElement("i");
                    i2.classList.add("fas");
                    i2.classList.add("fa-edit");
                    i2.classList.add("icon");

                    icon_td.append(i);
                    row.append(icon_td);
                      icon_td2.append(i2);
                    row.append(icon_td2);
                    row.appendChild(id);
                    if($('#form_name').val() == 'person' || $('#form_name').val() == 'primary_person'){
                        var grant = document.createElement("td");
                        var grant_i = document.createElement("i");
                        grant_i.classList.add("fas");
                        grant_i.classList.add("fa-universal-access");
                        grant_i.classList.add("icon");
                        grant.append(grant_i);
                        row.appendChild(grant);

                    }

                    return row;
    }
    function create_row(current_row){
            var row = document.createElement("tr");
                    var full_name = document.createElement("td");
                    var phone = document.createElement("td");
                    var email = document.createElement("td");
                    var passport = document.createElement("td");
                    var qid_no = document.createElement("td");
//                    var visa = document.createElement("td");
                    var id = document.createElement("td");
                    var permission = document.createElement("td");
                    full_name.innerHTML = current_row.children()[0].textContent.trim();
                    phone.innerHTML = current_row.children()[1].textContent.trim();
                    email.innerHTML = current_row.children()[2].textContent.trim();
                    passport.innerHTML =current_row.children()[3].textContent.trim();
                    qid_no.innerHTML = current_row.children()[4].textContent.trim();
//                    visa.innerHTML = current_row.children()[5].textContent.trim();
                    permission.innerHTML = current_row.children()[5].textContent.trim().charAt(0).toUpperCase() + current_row.children()[5].textContent.trim().slice(1);
                    id.innerHTML = current_row.children()[6].textContent.trim();
                    id.classList.add('d-none');
                    row.appendChild(full_name);
                    row.appendChild(phone);
                    row.appendChild(email);
                    row.appendChild(passport);
                    row.appendChild(qid_no);
//                    row.appendChild(visa);
                    row.appendChild(permission);

                    var icon_td = document.createElement("td");
                    var i = document.createElement("i");
                    i.classList.add("fas");
                    i.classList.add("fa-trash");
                    i.classList.add("icon");
                    var icon_td2 = document.createElement("td");
                    var i2 = document.createElement("i");
                    i2.classList.add("fas");
                    i2.classList.add("fa-edit");
                    i2.classList.add("icon");

                    icon_td.append(i);
                    row.append(icon_td);
                     icon_td2.append(i2);
                    row.append(icon_td2);
                    row.appendChild(id);
                       console
                    if($('#form_name').val() == 'person' || $('#form_name').val() == 'primary_person'){
                        var grant = document.createElement("td");
                        var grant_i = document.createElement("i");
                        grant_i.classList.add("fas");
                        grant_i.classList.add("fa-universal-access");
                        grant_i.classList.add("icon");
                        grant.append(grant_i);
                        row.appendChild(grant);

                    }
                    return row;
    }
    $('#document_number_search_contact_person').keypress(function(event){
        var keycode = (event.keyCode ? event.keyCode : event.which);
        if(keycode == '13'){
            $("#contact_person_search").click();
        }
    });
    $(document).on("click",".selected_row", function () {
        if ($(this).hasClass("user_selected_row")){
            $(this).removeClass("select_row_background_color")
            $(this).removeClass("user_selected_row")
            $(this).children().removeClass("font-weight-bold")
        }else{
            $('.selected_row').removeClass('select_row_background_color')
            $('.selected_row').removeClass('user_selected_row')
            $('.selected_row').children().removeClass("font-weight-bold")
            $(this).addClass("select_row_background_color")
            $(this).addClass("user_selected_row")
            $(this).children().addClass("font-weight-bold")
        }
     });
    function create_row_search_modal(data){
        var row = document.createElement("tr");
        var full_name = document.createElement("td");
        var phone = document.createElement("td");
        var email = document.createElement("td");
        var passport = document.createElement("td");
        var qid_no = document.createElement("td");
//                            var visa = document.createElement("td");
        var permission = document.createElement("td");
        var id = document.createElement("td");
        if (data.name){
            full_name.innerHTML = data.name;
        }else{
            full_name.innerHTML = ''
        }
        if (data.mobile){
            phone.innerHTML = data.mobile;
        }else{
            phone.innerHTML = ''
        }
        if(data.email){
            email.innerHTML =data.email;
        }else{
            email.innerHTML = ''
        }
        if(data.ps_passport_ref_no){
        passport.innerHTML = data.ps_passport_ref_no;
        }else{
        passport.innerHTML = ''
        }
        if(data.qid_ref_no){
        qid_no.innerHTML = data.qid_ref_no;
        }else{
        qid_no.innerHTML = ''
        }
        if(data.permission){
        permission.innerHTML = data.permission.charAt(0).toUpperCase() + data.permission.slice(1);
        }else{
        permission.innerHTML = ''
        }
        id.innerHTML = data.id;
        id.classList.add('d-none');
        row.classList.add('icon');
        row.classList.add('selected_row');
        row.appendChild(full_name);
        row.appendChild(phone);
        row.appendChild(email);
        row.appendChild(passport);
        row.appendChild(qid_no);
        row.appendChild(permission);
        row.appendChild(id);
        return row;
    }


//    $("#day").datepicker({
//        dateFormat: "MM - DD - yy",
//        showOn: "both",
//        buttonText : '<i class="zmdi zmdi-chevron-down"></i>',
//    });
    $('.create_new_activity').click(function(ev){
            if($('#activity_name').val() != ""){
                ajax.jsonRpc("/create_new_activity",'call',{'activity_name':$('#activity_name').val()}).then(function (result) {
                if (result){
                    console.log(';;;;;;;crate new activity');
                    var row = document.createElement("tr");
                    var data = document.createElement("td");
                    var id = document.createElement("td");
                    data.innerHTML = result['activity_name'];
                    id.innerHTML = result['activity_id'];
                    id.classList.add("d-none");
                    row.appendChild(data);
                    row.appendChild(id);
                    var icon_td = document.createElement("td");
                    var i = document.createElement("i");
                    i.classList.add("fas");
                    i.classList.add("fa-trash");
                    i.classList.add("icon");
                    var icon_td2 = document.createElement("td");
                    var i2 = document.createElement("i");
                    i2.classList.add("fas");
                    i2.classList.add("fa-edit");
                    i2.classList.add("icon")

                    icon_td.append(i);
                    row.append(icon_td);
                    icon_td2.append(i2);
                    row.append(icon_td2);
                    console.log("@@@@@@@@2");
                    $('#table_body_activity').append(row);
                    hide_unhide_table_header();
                 }
               });
            }
        });
        function create_activity_row(){
            var row = document.createElement("tr");
            var full_name = document.createElement("td");
            var id = document.createElement("td");
            full_name.innerHTML = $('#activity_name').find(":selected").text().trim();
            id.innerHTML = $('#activity_name').val().trim();
            id.classList.add('d-none');
            row.appendChild(full_name);
            row.appendChild(id);
            var icon_td = document.createElement("td");
            var i = document.createElement("i");
            i.classList.add("fas");
            i.classList.add("fa-trash");
            i.classList.add("icon");
            var icon_td2 = document.createElement("td");
//            var i2 = document.createElement("i");
//            i2.classList.add("fas");
//            i2.classList.add("fa-edit");
//            i2.classList.add("icon");
//            icon_td2.append(i2);
            row.append(icon_td2);
            icon_td.append(i);
            row.append(icon_td);
            $('#table_body_activity').append(row);
            hide_unhide_table_header();
        }
        $(document).on('click', '.create_exist_activity', function(){
                var current_row = $('#table_body_activity_search').children();
                const index = activity_ids_list.indexOf($("#activity_name").val().trim());
                if ($("#activity_name").val() != "" && index == -1){
                    ajax.jsonRpc("/activity_exist/create",'call',{'id':$("#activity_name").val().trim()}).then(function (data) {
                        data = JSON.parse(data);
                        if (data['msg'] == 'error'){
                            activity_ids_list.push($("#activity_name").val().trim());
                             $('#activity_hidden_ids').val(JSON.stringify(activity_ids_list));
                             create_activity_row();
                        }else{
                            create_activity_row();
                        }
                    });
                }
              });
        $(document).on('click', '#open_model_service', function(){
            $("#select_service").prop('selectedIndex', false);
            $("#option_new_div").addClass("d-none");
            $("#option_renew_div").addClass("d-none");
            $("#option_manage_div").addClass("d-none");
            $("#exampleModalServices").modal('show');
        });
        $(document).on('change', '#select_service', function(){
            var service = $("#select_service").val()
            ajax.jsonRpc("/get/service_options",'call',{'service':service}).then(function (data) {
                if(!data['new'] && !data['renew'] && !data['manage']){
                    $("#exampleModalServices").modal("hide");
                    $("#error_msg").text("There are no service options configured in this service. Please contact your administrator.");
                    $("#exampleModalError").modal("show");
                    return;
                }
                $("#option_new").prop('checked',false);
                $("#option_renew").prop('checked',false);
                $("#option_manage").prop('checked',false);
                if(data['new']){
                    $("#option_new_div").removeClass('d-none');
                }
                else {
                    $("#option_new_div").addClass('d-none');
                }
                if(data['renew']){
                    $("#option_renew_div").removeClass('d-none');
                }
                else {
                    $("#option_renew_div").addClass('d-none');
                }
                if(data['manage']){
                    $("#option_manage_div").removeClass('d-none');
                }
                else {
                    $("#option_manage_div").addClass('d-none');
                }
            });

        });
        $(document).on('click', '.add_service', function(){
            var service = $("#select_service").val()
            if (service != ""){
                if(!($("#option_new").is(':checked')) && !($("#option_renew").is(':checked')) && !($("#option_manage").is(':checked'))){
                    $("#error_msg").text("Please select atleast one service option!");
                    $("#exampleModalError").modal("show");
                    return;
                }
                ajax.jsonRpc("/add/service_opportunity",'call',{'service':service, 'new': $("#option_new").is(':checked'),
                'renew': $("#option_renew").is(':checked'), 'manage': $("#option_manage").is(':checked')}).then(function (data) {
                    console.log(data,"@@@@@@@data");
                    if(data){
                        var html_string = "<div><div class='card-title'>"
                        html_string += "<div class='custom-control custom-checkbox custom-control-inline service_radio form-check'>"
                        html_string += "<input class='form-check-input custom-control-input service-checked' type='checkbox' name='"
                        html_string += data['service'] + "' id='"+ service +"' checked='checked'/>"
                        html_string += "<label class='form-check-label custom-control-label service_radio_label' for='"+service+"'>"
                        html_string += data['service']
                        html_string += "</label></div></div>"
                        html_string += "<div class='row service-option-hide' style='margin-left: 0px !important;'>"
                        if('new' in data){
                            html_string += "<div class='col-3 custom-control custom-checkbox custom-control-inline service_radio form-check'>"
                            html_string += "<input class='form-check-input custom-control-input service_checkbox' type='checkbox' name='"
                            html_string += service + "-new' id='"+ service +"-new' value='new'"
                            if (data['new']){
                                html_string += "checked = 'checked'"
                            }
                            html_string += "/>"
                            html_string += "<label class='form-check-label custom-control-label service_radio_label' for='"+ service
                            if (data['new']){
                                html_string += "-new'>New</label><div class='ml-2 custom-control-inline service_status'><span class='badge badge-pill badge-dark'>Awaiting Approval</span></div></div>"
                            }else{
                                html_string += "-new'>New</label></div>"
                            }
                        }
                        if('renew' in data)
                        {
                            html_string += "<div class='col-3 custom-control custom-checkbox custom-control-inline service_radio form-check'>"
                            html_string += "<input class='form-check-input custom-control-input service_checkbox' type='checkbox' name='"
                            html_string += service + "-renew' id='"+ service +"-renew' value='renew'"
                            if (data['renew']){
                                html_string += "checked = 'checked'"
                            }
                            html_string += "/>"
                            html_string += "<label class='form-check-label custom-control-label service_radio_label' for='"+ service
                            if (data['renew']){
                                html_string += "-renew'>New</label><div class='ml-2 custom-control-inline service_status'><span class='badge badge-pill badge-dark'>Awaiting Approval</span></div></div>"
                            }else{
                                html_string += "-renew'>New</label></div>"
                            }

                        }
                        if('manage' in data)
                        {
                            html_string += "<div class='col-3 custom-control custom-checkbox custom-control-inline service_radio form-check'>"
                            html_string += "<input class='form-check-input custom-control-input service_checkbox' type='checkbox' name='"
                            html_string += service + "-manage' id='"+ service +"-manage' value='manage' "
                            if (data['manage']){
                                html_string += "checked = 'checked'"
                            }
                            html_string += "/>"
                            html_string += "<label class='form-check-label custom-control-label service_radio_label'for='"+ service
                            if (data['manage']){
                                html_string += "-manage'>New</label><div class='ml-2 custom-control-inline service_status'><span class='badge badge-pill badge-dark'>Awaiting Approval</span></div></div>"
                            }else{
                                html_string += "-manage'>New</label></div>"
                            }

                        }
                        html_string += "</div>"
                        // Add subservices if service is group
                        if(data['group']){
                            html_string += "<div class='row' >"
                            if(data['subservices']){
                                for(i=0;i<data['subservices'].length;i++){
                                    html_string += "<div class='col-xl-3 my-2'><div class='service_box'><span>"
                                    html_string += data['subservices'][i]
                                    html_string += "</span></div></div>"
                                }
                            }
                            html_string += "</div>"
                        }

                        html_string += "</div>"
                        html = $.parseHTML(html_string);
                        $(".service_catalog_form").append(html);

                    }
                    else {
                        $("#error_msg").text("This service has already been added to the opportunity.");
                        $("#exampleModalError").modal("show");
                    }
                });
             }
          });
         $(document).on('change', '#activity_name,#update_activity_name', function(){
            $("#search_result_activity_section p").remove();
         });

      function hide_unhide_table_header(){
        var manager_tbody = $('.table_body_contact_manager');
        var manger_thead1 = $("#manger_thead1");
        var activity_tbody = $('#table_body_activity');
        var activity_thead1 = $("#activity_thead1");
        var partner_thead1 = $("#partner_thead1");
        var partner_tbody = $('.table_body_contact_partner');
        var authoriser_thead1 = $("#authoriser_thead1");
        var authoriser_tbody = $('.table_body_contact_authorizer');
        var contact_person_tbody = $('.table_body_contact_person');
        var primary_contact_person_tbody = $('.table_body_primary_contact_person');
        var contact_person_thead1 = $("#contact_person_thead1");
        var primary_contact_person_thead1 = $("#primary_contact_person_thead1");
        if (manager_tbody.children().length == 0) {
                  manger_thead1.addClass("d-none");
        }else{
             manger_thead1.removeClass("d-none");
        }

        if (activity_tbody.children().length == 0) {
              activity_thead1.addClass("d-none");
        }else{
             activity_thead1.removeClass("d-none");
        }

        if (partner_tbody.children().length == 0) {
              partner_thead1.addClass("d-none");
        }else{
             partner_thead1.removeClass("d-none");
        }
        if (authoriser_tbody.children().length == 0) {
              authoriser_thead1.addClass("d-none");
        }else{

             authoriser_thead1.removeClass("d-none");
        }
        if (contact_person_tbody.children().length == 0) {
              contact_person_thead1.addClass("d-none");
        }else{
            contact_person_thead1.removeClass("d-none");
            }

        if (primary_contact_person_tbody.children().length == 0) {
              primary_contact_person_thead1.addClass("d-none");
        }else{
            primary_contact_person_thead1.removeClass("d-none");
            }
      }

      $('.create_new_manager').click(function(ev){
            var form = $("#new_manager");
            var data = new FormData(form[0]);
             $.ajax({
                type: 'POST',
                url: form.attr('action'),
                data: data,
                processData: false,
                contentType: false,
                dataType: "json",
                success: function(result) {
                    row = create_new_row_record(result);
                    $('#table_body_manager').append(row);
                    hide_unhide_table_header();
                    $("#exampleModal_manager").modal("toggle");
                }
             });
        });
     $('.create_new_partner').click(function(ev){
            var form = $("#new_partner");
            var data = new FormData(form[0]);
             $.ajax({
                type: 'POST',
                url: form.attr('action'),
                data: data,
                processData: false,
                contentType: false,
                dataType: "json",
                success: function(result) {
                    row = create_new_row_record(result);
                    $('#table_body_partner').append(row);
                    hide_unhide_table_header();
                }
             });
             $("#exampleModal_partner").modal("toggle");
        });
    function add_authorizer(row, result){
            file = $('#hidden_file_table')
        if (file.children().length == 0) {
            authorizer.push(parseInt(result['id']));
            $('#authorizer_input').val(JSON.stringify(authorizer));
             console.log("in authorizer row aaped",row);
        }
    }
     $('.create_new_contact_person').click(function(ev){
            console.log("clicked-------");
            if(!$("#new_contact").valid()){
                return false;
            }
            console.log("validated-----");
            var form = $("#new_contact");
            var data = new FormData(form[0]);
             $.ajax({
                type: 'POST',
                url: form.attr('action'),
                data: data,
                processData: false,
                contentType: false,
                dataType: "json",
//                error: function(){
//                    console.log("error-------------");
//                    window.location.replace("/registration?");
//                },
                success: function(result){
                    console.log('result--------',result);
                    if(result['error']){
                        $("#exampleModalError").modal("show");
                    }
                    else if(result['id']){
                        row = create_new_row_record(result);
                        if (result['form_name'] == 'person'){
                            person.push(result['id']);
                            $('#person_input').val(JSON.stringify(person));
                            $('.table_body_contact_person').append(row);
                        }
                        if (result['form_name'] == 'primary_person'){
                            primary_person.push(result['id']);
                            $('#primary_person_input').val(JSON.stringify(primary_person));
                            $('.table_body_primary_contact_person').append(row);
                        }
                        if (result['form_name'] == 'partner'){
                            partner.push(result['id']);
                            $('#partner_input').val(JSON.stringify(partner));
                            $('.table_body_contact_partner').append(row);
                        }
                        if (result['form_name'] == 'manager'){
                            manager.push(result['id']);
                            $('#manager_input').val(JSON.stringify(manager));

                            $('.table_body_contact_manager').append(row);
                            console.log("in manager row aaped",row);
                            add_authorizer(row,result);

                        }
                        if (result['form_name'] == 'authorizer'){
                            authorizer.push(result['id']);
                            $('#authorizer_input').val(JSON.stringify(authorizer));
                            $('.table_body_contact_authorizer').append(row);
                        }
                        hide_unhide_table_header();
                    }
                }
            });

        });

    $('.modal').on('hidden.bs.modal', function(){

    $(this).find('input[type=text]').val('');
    $(this).find('input[type=file]').val('');
    $(this).find('input[type=email]').val('');
    $(this).find('input[type=date]').val('');
    if ($('#collapseOneUpdate').hasClass( "show" )){
         $( "#collapseOneUpdate" ).removeClass("show");
         $( "#collapseTwoUpdate" ).addClass("show");
    }
    if( $('#collapseThreeUpdate').hasClass( "show" )){
         $( "#collapseTwoUpdate" ).addClass("show");
    }
    if ($('#updatecollapseOne').hasClass( "show" )){
         $( "#updatecollapseOne" ).removeClass("show");
         $( "#updatecollapseTwo" ).addClass("show");
    }
    if( $('#updatecollapseThree').hasClass( "show" )){
         $( "#updatecollapseTwo" ).addClass("show");
    }

    if ( this.id == 'exampleModalContactPerson'){
        $.each($(".drop_down"), function () {
        $(this).prop('selectedIndex', false);
    });
        $("#qid_check_box").prop('checked', false)
         $("#qid_accordion").addClass('d-none');
    }
    });

    $('.update_activity_submit_button').on('click',function(){
        edit_mode_row = $(".edit_mode");
        const index = activity_ids_list.indexOf($("#update_activity_name").val().trim());
        if(edit_mode_row && $('#update_activity_name').val() != "" && index == -1){
        value = {
            'old_activity_id':edit_mode_row.children()[1].textContent.trim(),
            'new_activity_id':$('#update_activity_name').val(),
        }
         ajax.jsonRpc("/activity/update",'call',value).then(function (data) {
            edit_mode_row.children()[0].textContent = $('#update_activity_name').find(":selected").text().trim();
            edit_mode_row.children()[1].textContent = $('#update_activity_name').val();
            const index = activity_ids_list.indexOf(value['old_activity_id']);
            if (index > -1) {
              activity_ids_list.splice(index, 1);
              activity_ids_list.push($("#update_activity_name").val().trim());
              $('#activity_hidden_ids').val(JSON.stringify(activity_ids_list));
            }
           edit_mode_row.removeClass('edit_mode');

         });
        }

    });
     $('.update_contact_person_submit_button').on('click',function(){
        if(!$("#update_contact").valid()){
                return false;
        }
        var form = $("#update_contact");
        var edit_mode_row = $(".edit_mode");
        $("#contact_id").val(edit_mode_row.children()[8].textContent.trim());
            var data = new FormData(form[0]);
             $.ajax({
                type: 'POST',
                url: form.attr('action'),
                data: data,
                processData: false,
                contentType: false,
                dataType: "json",
                success: function(result) {
                    console.log("");
                    if(result['error']){
                        $("#exampleModalError").modal("show");
                    }
//                    $("#update_contact_person_modal").modal("toggle");
                }
             });
        edit_mode_row = $(".edit_mode");
                if($("#update_qid_radio_yes").prop('checked') == true){
                    edit_mode_row.children()[4].textContent = $('#update_qid_extra_contact').val();
                    edit_mode_row.children()[3].textContent = '';
                }else{
                   edit_mode_row.children()[4].textContent = '';
                   edit_mode_row.children()[3].textContent = $('#update_passport_extra_contact').val();
                }
        edit_mode_row.children()[0].textContent = $('#update_full_name_extra_contact').val().toUpperCase();
        edit_mode_row.children()[1].textContent = $('#update_phone_extra_contact').val();
        edit_mode_row.children()[2].textContent = $('#update_email_extra_contact').val();
//        edit_mode_row.children()[5].textContent = $('#update_visa_extra_contact').val();

        edit_mode_row.children()[5].textContent = $('#update_extra_contact_permission').val().charAt(0).toUpperCase() + $('#update_extra_contact_permission').val().slice(1);
        edit_mode_row.removeClass('edit_mode');




    });
    function set_input_field_for_update(current_row){

    ajax.jsonRpc("/edit/search_id",'call',{'id':current_row.children()[8].textContent.trim()}).then(function (data) {
            if(data) {
                $("#update_full_name_extra_contact").val(data['en_name']);
                $("#update_phone_extra_contact").val(data['mobile']);
                $("#update_email_extra_contact").val(data['email']);
                $("#update_passport_extra_contact").val(data['ps_passport_ref_no']);
                $("#update_passport_name_extra_contact").val(data['en_name']);
                $("#update_passport_name_ar_extra_contact").val(data['ar_name']);
                $("#update_full_name_ar_extra_contact").val(data['ar_name']);
                $("#update_name_ar_extra_contact").val(data['ar_name']);
                $("#update_birth_date_extra_contact").val(data['ps_birth_date']);
                $("#update_qid_check_box").attr("checked", data['qid_resident'] );
                if(data['qid_resident'] == true){
                         $("#update_qid_accordion").removeClass('d-none');
                         $("#updatecollapseTwo").removeClass('show');
                         $("#updatecollapseThree").addClass('show');
                         $("#update_passport_accordion").addClass('d-none');
                         $('#update_qid_radio_yes').prop('checked',true);
                    }else{
                    $("#update_qid_accordion").addClass('d-none');
                         $("#update_passport_accordion").removeClass('d-none');
                         $("#updatecollapseThree").removeClass('show');
                         $("#updatecollapseTwo").addClass('show');
                      $('#update_qid_radio_no').prop('checked',true);
                        $("#update_qid_accordion").addClass('d-none');
                    }
                    $("#updateheadingOne").removeClass('d-none');
                $("#update_date_of_issue_extra_contact").val(data['passport_issue_date']);
                $("#update_expiry_date_extra_contact").val(data['passport_expiry_date']);
                $("#update_name_english_extra_contact").val(data['en_name']);
                $("#update_name_ar_extra_contact").val(data['ar_name']);
                $("#update_qid_extra_contact").val(data['ps_qid_no']);
                $("#update_qid_birth_date_extra_contact").val(data['qid_birth_date']);
                $("#update_qid_expiry_date_extra_contact").val(data['qid_expiry_date']);
                if(data['permission'] != ""){
                    $("#update_extra_contact_permission").find("option[value="+data['permission']+"]").attr("selected", "selected");
                }
                if(data['gender'] != ""){
                    $("#update_gender_extra_contact").find("option[value="+data['gender']+"]").attr("selected", "selected");
                }
                 if(data['passport_type'] != ""){
                    $("#update_passport_type_extra_contact").find("option[value="+data['passport_type']+"]").attr("selected", "selected");
                }
                if (data['qid_attachment_id'] != ""){
                    console.log("file found qid");
                    if (data['qid_document_name'] != ""){
                     $("#update_qid_name_document").text(data['qid_document_name']);
                    }
                       $("#file_name_table_commercial_license_contact_qid").removeClass('d-none');
                    $("#update_qid_document_extra_contact").addClass('d-none');
                    $("#update_qid_data_document").attr("href", "/web/content/ir.attachment/"+data['qid_attachment_id']+"/datas?download=true")
                }else{
                    console.log("file not found qid");
                    $("#file_name_table_commercial_license_contact_qid").addClass('d-none');
                }
                if (data['passport_attachment_id'] != ""){
                    console.log("file found pass");
                    if (data['passport_attachment_name'] != ""){
                    $("#update_passport_name_document").text(data['passport_attachment_name']);
                    }

                    $("#file_name_table_commercial_license_contact_passport").removeClass('d-none');
                    $("#update_passport_document_extra_contact").addClass('d-none');
                    $("#update_passport_data_document").attr("href", "/web/content/ir.attachment/"+data['passport_attachment_id']+"/datas?download=true")
                }else{
                    console.log("file not found passport");
                    $("#file_name_table_commercial_license_contact_passport").addClass('d-none');
                }
                 if(data['passport_country'] != ""){
                 $("#update_nationality_extra_contact").prop('selectedIndex', parseInt(data['passport_country']));
//                    $("#update_nationality_extra_contact").find("option[value="+data['passport_country']+"]").attr("selected", "selected");
                }
                 if(data['job_position'] != ""){
                    $("#update_job_position_extra_contact").find("option[value="+data['job_position']+"]").attr("selected", "selected");
                }
                 if(data['residency_type'] != ""){
                 if(data['residency_type'] == "family"){
                    $('#update_job_position_extra_contact_div').addClass('d-none');
                    $("#update_job_position_extra_contact").val('');
                 }
                    $("#update_residency_type_extra_contact").find("option[value="+data['residency_type']+"]").attr("selected", "selected");
                }
                 if(data['qid_country'] != ""){
                  $("#update_qid_nationality_extra_contact").prop('selectedIndex', parseInt(data['qid_country']));
//                    $("#update_qid_nationality_extra_contact").find("option[value="+data['qid_country']+"]").attr("selected", "selected");
                }
                 $('#update_contact_person_modal').modal();
             }
         });
    }
    $(document).on("click",".fa-edit", function () {
        edit_mode_row = $(".edit_mode");
        if(edit_mode_row){
        edit_mode_row.removeClass('edit_mode');
        }
        current_row = $(this).parent().parent();
        current_row.addClass("edit_mode");
        $("#contact_id").val(current_row.children()[8].textContent.trim());
        if($(this).parent().parent().parent()._id() == 'table_body_contact_person'){
            set_input_field_for_update(current_row);
        }
        if($(this).parent().parent().parent()._id() == 'table_body_activity'){
        $("#update_activity_name").val(current_row.children()[1].textContent.trim());

        $('#update_activity_modal').modal();
        }
    });
     $(document).on("click",".fa-trash", function () {
        if($(this).parent().parent().parent().hasClass("table_body_contact_manager")){
           var id_tag = $(this).parent().parent().children()[8];

            var id = id_tag.textContent.trim();
               if(id != ""){
                    ajax.jsonRpc("/manager/remove",'call',{'id':id}).then(function (data) {
                        if (manager.indexOf(parseInt(id)) > -1){
                            const index = manager.indexOf(parseInt(id));
                            if (index > -1) {
                              manager.splice(index, 1);
                              $('#manager_input').val(JSON.stringify(manager));
                            }
                        }

                   });
                    $(this).parent().parent().remove();
                    hide_unhide_table_header();
               }
        }else if($(this).parent().parent().parent().hasClass("table_body_contact_partner")){
            var id_tag = $(this).parent().parent().children()[8];


            var id = id_tag.textContent.trim();
               if(id != ""){
                    ajax.jsonRpc("/partner/remove",'call',{'id':id}).then(function (data) {
                        if (partner.indexOf(parseInt(id)) > -1){
                            const index = partner.indexOf(parseInt(id));
                            if (index > -1) {
                               console.log("indexxxxxxxxxxxxxxxxxx",index)
                              partner.splice(index, 1);
                              $('#partner_input').val(JSON.stringify(partner));
                            }
                        }
                   });
                    $(this).parent().parent().remove();
                    hide_unhide_table_header();

               }

        }else if($(this).parent().parent().parent().hasClass("table_body_contact_authorizer")){
            var id_tag = $(this).parent().parent().children()[8];

            var id = id_tag.textContent.trim();
            console.log("iddddddddddddddddddddddddddd",id);
               if(id != ""){
                    ajax.jsonRpc("/authorizer/remove",'call',{'id':id}).then(function (data) {
                    console.log('rrrrrrrrrrrrrrrrrrr',authorizer);
                      if (authorizer.indexOf(parseInt(id)) > -1){
                            const index = authorizer.indexOf(parseInt(id));
                            if (index > -1) {
                             console.log('ppppppppppppppppp',authorizer);
                              authorizer.splice(index, 1);
                               console.log('tttttttttttttttttt',authorizer);
                              $('#authorizer_input').val(JSON.stringify(authorizer));
                            }
                        }
                   });
                    $(this).parent().parent().remove();
                    hide_unhide_table_header();

               }

        }
        else if($(this).parent().parent().parent()._id() == 'table_body_activity'){
            var id_tag = $(this).parent().parent().children()[1];
            var delete_line_row = $(this).parent().parent();
            var id = id_tag.textContent.trim();
               if(id != ""){
                    ajax.jsonRpc("/activity/remove",'call',{'id':id}).then(function (data) {
                        data = JSON.parse(data);
                        if (data['msg'] == 'error'){
                            if (activity_ids_list.indexOf(id) > -1){
                                const index = activity_ids_list.indexOf(id.toString());
                                if (index > -1) {
                                  activity_ids_list.splice(index, 1);
                                  $('#activity_hidden_ids').val(JSON.stringify(activity_ids_list));
                                }
                            }
                            delete_line_row.remove();
                            hide_unhide_table_header();
                        }else{
                            delete_line_row.remove();
                            hide_unhide_table_header();
                        }
                   });
               }

        }
        else if($(this).parent().parent().parent().hasClass('table_body_primary_contact_person')){
            var id_tag = $(this).parent().parent().children()[8];

            var id = id_tag.textContent.trim();
            ajax.jsonRpc("/contact/delete",'call',{'id':id,'primary_contact':true}).then(function (data) {
                 if (primary_person.indexOf(parseInt(id)) > -1){
                    const index = primary_person.indexOf(parseInt(id));
                    if (index > -1) {
                      primary_person.splice(index, 1);
                      $('#primary_person_input').val(JSON.stringify(primary_person));
                    }
                }
            });
            $(this).parent().parent().remove();
            hide_unhide_table_header();
        }
        else if($(this).parent().parent().parent()._id() == 'table_body_contact_person' && $(this).parent().parent().parent().hasClass('table_body_contact_person')){
            var id_tag = $(this).parent().parent().children()[8];

            var id = id_tag.textContent.trim();
            ajax.jsonRpc("/contact/delete",'call',{'id':id}).then(function (data) {
                if (person.indexOf(parseInt(id)) > -1){
                    const index = person.indexOf(parseInt(id));
                    if (index > -1) {
                      person.splice(index, 1);
                      $('#person_input').val(JSON.stringify(person));
                    }
                }
            });
            $(this).parent().parent().remove();
            hide_unhide_table_header();
        }
        else if($(this).parent().parent().parent()._id() == 'table_body_activity'){
           extra_activity_name_list.splice(extra_activity_name_list.indexOf($(this).parent().prev().text()),1);
           $("#input_activity_name_list").val(extra_activity_name_list);
           $(this).parent().parent().remove();
           hide_unhide_table_header();
        }
     });
     $('.drop_zone').on('dragover', function(event){
        event.preventDefault();
        drag_text = document.getElementById("drag_text");
         if(drag_text.classList.contains('d-none')){
             return false;
         }else{
            this.classList.add('drop_zone_over');
         }

    });

    $('.drop_zone').on('click', function(event){
          var inputElement = $('#fileElem');
          inputElement.click();
    });
    $('.drop_zone').on('dragleave dragend', function(event){
         event.preventDefault();
        this.classList.remove('drop_zone_over');
    });

    $('.drop_zone').on('drop', function(event){
        event.preventDefault();
        drag_text = document.getElementById("drag_text");
        if(drag_text.classList.contains('d-none')){
             return false;
         }else{
            this.classList.remove('drop_zone_over');
//        $('.Add-Document').addClass('d-none');
        $('#drag_text').addClass('d-none');

        var inputElement = document.getElementById("fileelem");
        if (event.originalEvent.dataTransfer.files.length){
            $('#file_name_table').removeClass('d-none');
//            $('.drop_zone').addClass('file_zone');
//            $('.file_zone').removeClass('drop_zone');
            inputElement.files = event.originalEvent.dataTransfer.files;

            var files = event.originalEvent.dataTransfer.files;
            for (let i = 0; i < 1; i++) {
                var row = document.createElement("tr");
            var data = document.createElement("td");
            var icon = document.createElement("i");
            var icon_td = document.createElement("td");
            icon.classList.add("fa");
            icon.classList.add("fa-times");
            icon.classList.add("icon");
                const file = files[i];
                data.innerHTML = file.name;
                row.appendChild(data);
                icon_td.append(icon);
                row.append(icon_td);
                var download_icon = document.createElement("i");
                var download_icon_td = document.createElement("td");
                download_icon.classList.add("fa");
                download_icon.classList.add("fa-download");
                download_icon.classList.add("icon");
                download_icon_td.append(download_icon);
                row.append(download_icon_td);

                $('#file_tbody').append(row);
         }

            }
        }

    });

    $('#fileelem').on('change', function(event){
        event.preventDefault();
        drag_text = document.getElementById("drag_text");
        if(drag_text.classList.contains('d-none')){
             return false;
         }else{
        this.classList.remove('drop_zone_over');
//        $('.Add-Document').addClass('d-none');
        $('#drag_text').addClass('d-none');

        var inputElement = document.getElementById("fileelem");

        if (event.target.files){
//            $("#file_name_table").empty();
            $('#file_name_table').removeClass('d-none');
//            $('.drop_zone').addClass('file_zone');
//            $('.file_zone').removeClass('drop_zone');
            var files = event.target.files;
            for (let i = 0; i < 1; i++) {
             var row = document.createElement("tr");
            var data = document.createElement("td");
            var icon = document.createElement("i");
            var icon_td = document.createElement("td");
            icon.classList.add("fa");
            icon.classList.add("fa-times");
            icon.classList.add("icon");
                const file = files[i];
                $('#fileelem_name').val(file.name);
                data.innerHTML = file.name;
                row.appendChild(data);
                icon_td.append(icon);
                row.append(icon_td);
                var download_icon = document.createElement("i");
                var download_icon_td = document.createElement("td");
                download_icon.classList.add("fa");
                download_icon.classList.add("fa-download");
                download_icon.classList.add("icon");
                download_icon_td.append(download_icon);
                row.append(download_icon_td);
                $('#file_tbody').append(row);
                }
            }
        }

    });
    $('.drop_zone3').on('dragover', function(event){
        event.preventDefault();
        drag_text3 = document.getElementById("drag_text3");
        if(drag_text3.classList.contains('d-none')){
             return false;
         }else{
        this.classList.add('drop_zone_over');
        }
    });
    $('.drop_zone3').on('dragleave dragend', function(event){
         event.preventDefault();
        this.classList.remove('drop_zone_over');
    });
    $('.drop_zone3').on('drop', function(event){
        event.preventDefault();
        drag_text3 = document.getElementById("drag_text3");
        if(drag_text3.classList.contains('d-none')){
             return false;
         }else{
        this.classList.remove('drop_zone_over');
//        $('.Add-Document3').addClass('d-none');
        $('#drag_text3').addClass('d-none');

        var inputElement3 = document.getElementById("fileelem3");;
        if (event.originalEvent.dataTransfer.files.length){
            $('#file_name_table_commercial_license').removeClass('d-none');
//            $('.drop_zone3').addClass('file_zone3');
//            $('.file_zone3').removeClass('drop_zone3');
            inputElement3.files = event.originalEvent.dataTransfer.files;

            var files = event.originalEvent.dataTransfer.files;
            for (let i = 0; i < 1; i++) {
                var row = document.createElement("tr");
            var data = document.createElement("td");
            var icon = document.createElement("i");
            var icon_td = document.createElement("td");
            icon.classList.add("fa");
            icon.classList.add("fa-times");
            icon.classList.add("icon");
                const file = files[i];
                data.innerHTML = file.name;
                row.appendChild(data);
                icon_td.append(icon);
                row.append(icon_td);
                var download_icon = document.createElement("i");
                var download_icon_td = document.createElement("td");
                download_icon.classList.add("fa");
                download_icon.classList.add("fa-download");
                download_icon.classList.add("icon");
                download_icon_td.append(download_icon);
                row.append(download_icon_td);
                $('#file_tbody_commercial_license').append(row);
                }
            }
        }
    });

//    $('.service_options').on('change',function(event){
//        var service_id = $(event.currentTarget.parentElement).find('.service_options').find('option:selected').val();
//        if(service_id){
//            rpc.query({
//                    model: 'ebs.service.option',
//                    method: "search_read",
//                    domain: [['id','=',service_id]],
//                    fields : ['id', 'govt_fees', 'fusion_fees']
//                }).then((result => {
//                        $(event.currentTarget.parentElement.parentElement).find('.govt_fees').val(result[0]['govt_fees']);
//                        $(event.currentTarget.parentElement.parentElement).find('.fusion_fees').val(result[0]['fusion_fees']);
//                    }));
//        }
//        else{
//            $(event.currentTarget.parentElement.parentElement).find('.govt_fees').val("");
//            $(event.currentTarget.parentElement.parentElement).find('.fusion_fees').val("");
//        }
//    });


    $('.service-checked').on('click', function(event){
        $(this).click();
        var service_option_row = $(event.currentTarget.parentElement.parentElement.parentElement).find('.service-option-hide')
        if ($(event.currentTarget)[0].checked == true){
            $(service_option_row)[0].hidden = false;
        }
        else{
            $(service_option_row)[0].hidden = true;
        }
    });

    $('#fileelem3').on('change', function(event){
        event.preventDefault();
        drag_text3 = document.getElementById("drag_text3");
        if(drag_text3.classList.contains('d-none')){
             return false;
         }else{
        this.classList.remove('drop_zone_over');
//        $('.Add-Document3').addClass('d-none');
        $('#drag_text3').addClass('d-none');

        var inputElement3 = document.getElementById("fileelem3");

        if (event.target.files){
//            $("#file_name_table").empty();
            $('#file_name_table_commercial_license').removeClass('d-none');
//            $('.drop_zone3').addClass('file_zone3');
//            $('.file_zone3').removeClass('drop_zone3');
            var files = event.target.files;

            for (let i = 0; i < 1; i++) {
                var row = document.createElement("tr");
                var data = document.createElement("td");
                var icon = document.createElement("i");
                var icon_td = document.createElement("td");
                icon.classList.add("fa");
                icon.classList.add("fa-times");
                icon.classList.add("icon");
                const file = files[i];
                $('#fileelem_name3').val(file.name);
                data.innerHTML = file.name;
                row.appendChild(data);
                icon_td.append(icon);
                row.append(icon_td);
                var download_icon = document.createElement("i");
                var download_icon_td = document.createElement("td");
                download_icon.classList.add("fa");
                download_icon.classList.add("fa-download");
                download_icon.classList.add("icon");
                download_icon_td.append(download_icon);
                row.append(download_icon_td);
                $('#file_tbody_commercial_license').append(row);
                }
            }
        }

    });
    $('.drop_zone4').on('dragover', function(event){
        event.preventDefault();
        drag_text4 = document.getElementById("drag_text4");
        if(drag_text4.classList.contains('d-none')){
             return false;
         }else{
        this.classList.add('drop_zone_over');
        }
    });
    $('.drop_zone4').on('dragleave dragend', function(event){
         event.preventDefault();
        this.classList.remove('drop_zone_over');
    });
    $('.drop_zone4').on('drop', function(event){
        event.preventDefault();
        drag_text4 = document.getElementById("drag_text4");
        if(drag_text4.classList.contains('d-none')){
             return false;
         }else{
        this.classList.remove('drop_zone_over');
//        $('.Add-Document4').addClass('d-none');
        $('#drag_text4').addClass('d-none');

        var inputElement3 = document.getElementById("fileelem4");
        if (event.originalEvent.dataTransfer.files.length){
            $('#file_name_table_establishment_card').removeClass('d-none');
//            $('.drop_zone4').addClass('file_zone4');
//            $('.file_zone4').removeClass('drop_zone4');
            inputElement3.files = event.originalEvent.dataTransfer.files;

            var files = event.originalEvent.dataTransfer.files;
            for (let i = 0; i < 1; i++) {
                var row = document.createElement("tr");
            var data = document.createElement("td");
            var icon = document.createElement("i");
            var icon_td = document.createElement("td");
            icon.classList.add("fa");
            icon.classList.add("fa-times");
            icon.classList.add("icon");
                const file = files[i];

                data.innerHTML = file.name;
                row.appendChild(data);
                icon_td.append(icon);
                row.append(icon_td);
                var download_icon = document.createElement("i");
                var download_icon_td = document.createElement("td");
                download_icon.classList.add("fa");
                download_icon.classList.add("fa-download");
                download_icon.classList.add("icon");
                download_icon_td.append(download_icon);
                row.append(download_icon_td);
                $('#file_tbody_establishment_card').append(row);
                }
            }
        }

    });
    $('#fileelem4').on('change', function(event){
        event.preventDefault();
        drag_text4 = document.getElementById("drag_text4");
        if(drag_text4.classList.contains('d-none')){
             return false;
         }else{
        this.classList.remove('drop_zone_over');
//        $('.Add-Document4').addClass('d-none');
        $('#drag_text4').addClass('d-none');

        var inputElement4 = document.getElementById("fileelem3");
        inputElement4.files = event.target.files
        if (event.target.files){
//            $("#file_name_table").empty();
            $('#file_name_table_establishment_card').removeClass('d-none');
//            $('.drop_zone4').addClass('file_zone4');
//            $('.file_zone4').removeClass('drop_zone4');
            var files = event.target.files;
            for (let i = 0; i < 1; i++) {
             var row = document.createElement("tr");
            var data = document.createElement("td");
            var icon = document.createElement("i");
            var icon_td = document.createElement("td");
            icon.classList.add("fa");
            icon.classList.add("fa-times");
            icon.classList.add("icon");
                const file = files[i];
                 $('#fileelem_name4').val(file.name);
                data.innerHTML = file.name;
                row.appendChild(data);
                icon_td.append(icon);
                row.append(icon_td);
                var download_icon = document.createElement("i");
                var download_icon_td = document.createElement("td");
                download_icon.classList.add("fa");
                download_icon.classList.add("fa-download");
                download_icon.classList.add("icon");
                download_icon_td.append(download_icon);
                row.append(download_icon_td);
                $('#file_tbody_establishment_card').append(row);
                }
            }
        }

    });

    $(document).on("click",".fa-times", function () {
    if($(this).parent().parent().parent()._id() == "file_tbody_commercial_license"){
        $('#fileelem_name3').val('');
        var inputElement3 = document.getElementById("fileelem3");
        var inputFile = inputElement3.files;
        const dt = new DataTransfer()
        for(let i=0; i<inputElement3.files.length; i++){

            file = inputFile[i];
            if(file.name != $(this).parent().prev().text()){
              dt.items.add(file)
            }
        }
        inputElement3.files = dt.files;
        $(this).parent().parent().remove();
            var file_tbody = $('#file_tbody_commercial_license');
            if (file_tbody.children().length == 0) {
                    $('.Add-Document3').removeClass('d-none');
                    $('#drag_text3').removeClass('d-none');
                    $('.file_zone3').addClass('drop_zone3');
                    $('.drop_zone3').removeClass('file_zone3');
            }
    }else if ($(this).parent().parent().parent()._id() == "file_tbody"){
    $('#fileelem_name').val('');
        var inputElement = document.getElementById("fileelem");
        var inputFile = inputElement.files;
        const dt = new DataTransfer()
        for(let i=0; i<inputElement.files.length; i++){
            file = inputFile[i];
            if(file.name != $(this).parent().prev().text()){
              dt.items.add(file)
            }
        }
        inputElement.files = dt.files;
        $(this).parent().parent().remove();
        var file_tbody = $('#file_tbody');
        if (file_tbody.children().length == 0) {
                $('.Add-Document').removeClass('d-none');
                $('#drag_text').removeClass('d-none');
                $('.file_zone').addClass('drop_zone');
                $('.drop_zone').removeClass('file_zone');
        }
    }else if($(this).parent().parent().parent()._id() == "file_tbody_establishment_card"){
    $('#fileelem_name4').val('');
        var inputElement4 = document.getElementById("fileelem4");
        var inputFile = inputElement4.files;
        const dt = new DataTransfer()
        for(let i=0; i<inputElement4.files.length; i++){
            file = inputFile[i];
            if(file.name != $(this).parent().prev().text()){
              dt.items.add(file)
            }
        }
        inputElement4.files = dt.files;
        $(this).parent().parent().remove();
            var file_tbody = $('#file_tbody_establishment_card');
            if (file_tbody.children().length == 0) {
                    $('.Add-Document4').removeClass('d-none');
                    $('#drag_text4').removeClass('d-none');
                    $('.file_zone4').addClass('drop_zone4');
                    $('.drop_zone4').removeClass('file_zone4');
            }
    }
     });
//     download file
$(document).on("click",".fa-download", function () {
    if($(this).parent().parent().parent()._id() == "file_tbody"){
        var inputElement = document.getElementById("fileelem");
        var inputFile = inputElement.files;

        for(let i=0; i<inputElement.files.length; i++){
            file = inputFile[i];
            if(file.name == $(this).parent().parent().children()[0].textContent){
              var element = document.createElement('a');
              var url = window.URL || window.webkitURL;
               link = url.createObjectURL(file);
                element.setAttribute('href', link);
                element.setAttribute('download', file.name);
                $(this).parent().parent().append(element);
                element.click();


            }
        }
    }else if($(this).parent().parent().parent()._id() == "file_tbody_commercial_license"){
        var inputElemen3 = document.getElementById("fileelem3");
        var inputFile = inputElemen3.files;

        for(let i=0; i<inputElemen3.files.length; i++){
            file = inputFile[i];
            if(file.name == $(this).parent().parent().children()[0].textContent){
              var element = document.createElement('a');
              var url = window.URL || window.webkitURL;
               link = url.createObjectURL(file);
                element.setAttribute('href', link);
                element.setAttribute('download', file.name);
                $(this).parent().parent().append(element);
                element.click();


            }
        }
    }else if($(this).parent().parent().parent()._id() == "file_tbody_establishment_card"){
        var inputElemen4 = document.getElementById("fileelem4");
        var inputFile = inputElemen4.files;

        for(let i=0; i<inputElemen4.files.length; i++){
            file = inputFile[i];
            if(file.name == $(this).parent().parent().children()[0].textContent){
              var element = document.createElement('a');
              var url = window.URL || window.webkitURL;
               link = url.createObjectURL(file);
                element.setAttribute('href', link);
                element.setAttribute('download', file.name);
                $(this).parent().parent().append(element);
                element.click();


            }
        }
    }
     });
 //     secondary person create document section
     $(document).on('click', '.underline_passport_type', function(){
        $('.underline_passport_type').addClass('doc_type_underline');
        $('.qid_section').addClass('d-none');
        $('.visa_section').addClass('d-none');
        $('.passport_section').removeClass('d-none');
        $('.underline_qid_type').removeClass('doc_type_underline');
        $('.underline_visa_type').removeClass('doc_type_underline');
     });
     $(document).on('click', '.underline_qid_type', function(){
        $('.underline_qid_type').addClass('doc_type_underline');
        $('.passport_section').addClass('d-none');
        $('.visa_section').addClass('d-none');
        $('.qid_section').removeClass('d-none');
        $('.underline_visa_type').removeClass('doc_type_underline');
        $('.underline_passport_type').removeClass('doc_type_underline');
     });
     $(document).on('click', '.underline_visa_type', function(){
        $('.underline_visa_type').addClass('doc_type_underline');
        $('.passport_section').addClass('d-none');
        $('.qid_section').addClass('d-none');
        $('.visa_section').removeClass('d-none');
        $('.underline_qid_type').removeClass('doc_type_underline');
        $('.underline_passport_type').removeClass('doc_type_underline');
     });
    //     secondary person update document section
     $(document).on('click', '#update_contact_underline_passport_type', function(){
        $('#update_contact_underline_passport_type').addClass('doc_type_underline');
        $('.update_contact_qid_section').addClass('d-none');
        $('.update_contact_visa_section').addClass('d-none');
        $('.update_contact_passport_section').removeClass('d-none');
        $('#update_contact_underline_qid_type').removeClass('doc_type_underline');
        $('#update_contact_underline_visa_type').removeClass('doc_type_underline');
     });
     $(document).on('click', '#update_contact_underline_qid_type', function(){
        $('#update_contact_underline_qid_type').addClass('doc_type_underline');
        $('.update_contact_passport_section').addClass('d-none');
        $('.update_contact_visa_section').addClass('d-none');
        $('.update_contact_qid_section').removeClass('d-none');
        $('#update_contact_underline_visa_type').removeClass('doc_type_underline');
        $('#update_contact_underline_passport_type').removeClass('doc_type_underline');
     });
     $(document).on('click', '#update_contact_underline_visa_type', function(){
        $('#update_contact_underline_visa_type').addClass('doc_type_underline');
        $('.update_contact_passport_section').addClass('d-none');
        $('.update_contact_qid_section').addClass('d-none');
        $('.update_contact_visa_section').removeClass('d-none');
        $('#update_contact_underline_qid_type').removeClass('doc_type_underline');
        $('#update_contact_underline_passport_type').removeClass('doc_type_underline');
     });

//     secondary person
//          $(document).on('click', '.next_btn', function(){
//                $('.next_btn').addClass('d-none');
//           });
          $(document).on('click', '.underline_new_contact', function(){

                    $('.underline_new_contact').addClass('contact_underline');
//                     $('.next_btn').addClass('d-none');
                     $('#exiting_contact_form').addClass('d-none');
                     $('#new_contact_form').removeClass('d-none');
                     $('.underline_exiting_contact').removeClass('contact_underline');
                     $('.create_new_contact_person').removeClass('d-none');
                     $('.create_exists_contact_person').addClass('d-none');
              });

         $(document).on('click', '#open_model_contact_person', function(){
                    $("#table_body_contact_person_search tr").remove();
                    var search_record_section = document.getElementById("search_record_section");
                    $("#form_name").val('person');
                    if(search_record_section){
                    search_record_section.classList.add('d-none');
                    }
                    $("#search_result_section p").remove();
                     $("#qid_radio_yes").prop('checked', false);
                    $("#qid_radio_no").prop('checked', false);
                    $("#person_accordion").addClass('d-none');
                    $("#passport_accordion").addClass('d-none');
              });
           $(document).on('click', '#open_model_primary_contact_person', function(){
                    $("#table_body_contact_person_search tr").remove();
                    var search_record_section = document.getElementById("search_record_section");
                    $("#form_name").val('primary_person');
                    if(search_record_section){
                    search_record_section.classList.add('d-none');
                    }
                    $("#search_result_section p").remove();
                     $("#qid_radio_yes").prop('checked', false);
                    $("#qid_radio_no").prop('checked', false);
                    $("#person_accordion").addClass('d-none');
                    $("#passport_accordion").addClass('d-none');
              });

       $(document).on('click', '#open_model_partner', function(){
                     $("#table_body_contact_person_search tr").remove();
                    var search_record_section = document.getElementById("search_record_section");
                    if(search_record_section){
                    search_record_section.classList.add('d-none');
                    }
                    $("#search_result_section p").remove();
                    $("#form_name").val('partner');
                     $("#person_accordion").addClass('d-none');
                     $("#passport_accordion").addClass('d-none');
                     $("#qid_radio_yes").prop('checked', false);
                    $("#qid_radio_no").prop('checked', false);

              });
        $(document).on('click', '#open_model_manager', function(){
                    $("#table_body_contact_person_search tr").remove();
                    var search_record_section = document.getElementById("search_record_section");
                    if(search_record_section){
                    search_record_section.classList.add('d-none');
                    }
                    $("#search_result_section p").remove();
                    $("#form_name").val('manager');
                    $("#qid_radio_yes").prop('checked', false);
                    $("#qid_radio_no").prop('checked', false);
                    $("#person_accordion").addClass('d-none');
                    $("#passport_accordion").addClass('d-none');
              });
           $(document).on('click', '#open_model_authoriser', function(){
                    $("#table_body_contact_person_search tr").remove();
                    var search_record_section = document.getElementById("search_record_section");
                    if(search_record_section){open_model_manager
                    search_record_section.classList.add('d-none');
                    }
                    $("#search_result_section p").remove();
                    $("#form_name").val('authorizer');
                     $("#qid_radio_yes").prop('checked', false);
                    $("#qid_radio_no").prop('checked', false);
                    $("#person_accordion").addClass('d-none');
                    $("#passport_accordion").addClass('d-none');
              });
           $(document).on('click', '#open_model', function(){
                    $("#table_body_manager_search tr").remove();
                    $("#activity_name").val("");
                    var search_record_section = document.getElementById("search_record_activity_section");
                    if (search_record_section){
                    search_record_section.classList.add('d-none');
                    }
                    $("#search_result_activity_section p").remove();
              });
           $(document).on('click', '#open_model_service', function(){
                console.log('Opening Modal');

           });

          //          Activity
        $(document).on('click', '#underline_exiting_activity', function(){
                             $('#underline_exiting_activity').addClass('contact_underline');
                             $('#new_activity_form').addClass('d-none');
                             $('#exiting_activity_form').removeClass('d-none');
                             $('#underline_new_activity').removeClass('contact_underline');
                             $('.create_new_activity').addClass('d-none');
                             $('.create_exist_activity').removeClass('d-none');
                      });
         $(document).on('click', '#underline_new_activity', function(){
                    $('#underline_new_activity').addClass('contact_underline');
                     $('#exiting_activity_form').addClass('d-none');
                     $('#new_activity_form').removeClass('d-none');
                     $('#underline_exiting_activity').removeClass('contact_underline');
                     $('.create_new_activity').removeClass('d-none');
                     $('.create_exist_activity').addClass('d-none');
              });

         $(document).on('click', '#contact_person_search', function(){
            console.log('#contact_person_search')

             if ($('#document_number_search_contact_person').val()){
                if ($('#form_name').val() == 'person'){
                    parameter = {
                    'document_id':$('#document_number_search_contact_person').val().trim(),
                    'who_call':'person'
                    }
                }
                if ($('#form_name').val() == 'partner'){
                   parameter = {
                    'document_id':$('#document_number_search_contact_person').val().trim(),
                    'who_call':'partner'
                    }
                }
                if ($('#form_name').val() == 'manager'){
                   parameter = {
                    'document_id':$('#document_number_search_contact_person').val().trim(),
                    'who_call':'manager'
                    }
                }
                if ($('#form_name').val() == 'authorizer'){
                   parameter = {
                    'document_id':$('#document_number_search_contact_person').val().trim(),
                    'who_call':'authorizer'
                    }
                }
                if ($('#form_name').val() == 'primary_person'){
                   parameter = {
                    'document_id':$('#document_number_search_contact_person').val().trim(),
                    'who_call':'primary_person'
                    }
                }

                ajax.jsonRpc("/search/partner/manager/person",'call',parameter).then( function (data) {
                console.log('datadatadatdatdatdatdatdatdtadatd',data);
                if(data){
                    if (data['contact_list']){
                        $("#table_body_contact_person_search tr").remove();
                        for(var i = 0; i < data['contact_list'].length; i++){
                            var already_added = false;
                            if (data['contact_list'][i]){
                                var id = data['contact_list'][i].id;
                                console.log("eeeeeeeeeeee",data)
                                console.log("ttttttttttttttttt",data['contact_list'][i])
                                console.log("iiiiiiiiiiiiii",data['contact_list'][i].id)
                                if ($('#form_name').val() == 'person'){
                                console.log("in person",person,id);
                                    if (person.indexOf(id) > -1 || primary_person.indexOf(id) > -1){
                                        console.log("in person true");
                                          already_added = true
                                    }
                                }
                                if ($('#form_name').val() == 'partner'){
                                 console.log("in person",partner,id);
                                    if (partner.indexOf(id) > -1){
                                     console.log("in person inside",partner,id);
                                          already_added = true
                                    }
                                }
                                if ($('#form_name').val() == 'manager'){
                                    if (manager.indexOf(id) > -1){
                                          already_added = true
                                    }
                                }
                                if ($('#form_name').val() == 'authorizer'){
                                    if (authorizer.indexOf(id) > -1){
                                          already_added = true
                                    }
                                }
                                if ($('#form_name').val() == 'primary_person'){
                                console.log("in primary_person",primary_person);
                                    if (primary_person.indexOf(id) > -1 || person.indexOf(id) > -1){
                                        console.log("in primary_person true");
                                          already_added = true
                                    }
                                }
                             }
                             console.log("already_addedalready_added",already_added);
                             if(data['contact_list'][i] && !already_added){
                                $("#search_result_section p").remove();
                                console.log('data found', data['contact_list'][i]);
                                var search_record_section = document.getElementById("search_record_section");
                                search_record_section.classList.remove('d-none');
                                row = create_row_search_modal(data['contact_list'][i]);
                                console.log("rrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrr",row);
                                $('#table_body_contact_person_search').append(row);
                            }else{
                                console.log('data in main ekse  not found');
                                if ($("#table_body_contact_person_search").children().length == 0){
                                    $("#search_result_section p").remove();
                                    var search_record_section = document.getElementById("search_record_section");
                                    search_record_section.classList.add('d-none');
                                    $('#search_result_section').append(create_error_message());
                                }
                            }
                        }
                    }
                }else{
                    console.log('data in else part  not found');
                    $("#search_result_section p").remove();
                    var search_record_section = document.getElementById("search_record_section");
                    search_record_section.classList.add('d-none');
                    $('#search_result_section').append(create_error_message());
                }
            });

            }

         });
       $('.sort_by_qid_no').click(function(ev){
            console.log("=============",$(ev.currentTarget))
//            $(ev.currentTarget).
            window.location = window.location.origin + '/my/employees'+ '?' + "sortby=qid_no"
        });
         $('.sort_by_employee_name').click(function(ev){
            window.location = window.location.origin + '/my/employees'+ '?' + "sortby=name"
        });
         $('.sort_by_passport_no').click(function(ev){
            window.location = window.location.origin + '/my/employees'+ '?' + "sortby=passport_id"
        });
         $('.sort_by_sponsor').click(function(ev){
            window.location = window.location.origin + '/my/employees'+ '?' + "sortby=sponsor"
        });
        $('.sort_by_emp_status').click(function(ev){
            window.location = window.location.origin + '/my/employees'+ '?' + "sortby=stage"
        });

         $(document).on('click', '.create_exists_contact_person', function(){
         search_table_record = $('#table_body_contact_person_search');
         var current_row = $('#table_body_contact_person_search').find(".user_selected_row");
         if (current_row.length != 0) {

                value  = {
                    'id':current_row.children()[6].textContent.trim(),
                    'form_name':$('#form_name').val()
                }
//                  ajax.jsonRpc("/contact_exist/create",'call',value).then(function (data) {
//                    console.log("record contact updated####################");
//                });
                    row = create_row(current_row);
                    if(value['id'] != ""){
                        if ($('#form_name').val() == 'person'){
                            console.log("aaded person");
                            person.push(parseInt(value['id']));
                            $('#person_input').val(JSON.stringify(person));
                        $('.table_body_contact_person').append(row);
                        }
                         if ($('#form_name').val() == 'primary_person'){
                             console.log("aaded person");
                             primary_person.push(parseInt(value['id']));
                             $('#primary_person_input').val(JSON.stringify(primary_person));

                        $('.table_body_primary_contact_person').append(row);
                        }
                        if ($('#form_name').val() == 'partner'){
                            console.log("aaded partner");
                            partner.push(parseInt(value['id']));
                            $('#partner_input').val(JSON.stringify(partner));
                        $('.table_body_contact_partner').append(row);
                        }
                        if ($('#form_name').val() == 'manager'){
                            console.log("aaded manager");
                            manager.push(parseInt(value['id']));
                            $('#manager_input').val(JSON.stringify(manager));

                            $('.table_body_contact_manager').append(row);
                            add_authorizer(row,value);


                        }
                        if ($('#form_name').val() == 'authorizer'){
                            console.log("aaded authorizer");
                            authorizer.push(parseInt(value['id']));
                            $('#authorizer_input').val(JSON.stringify(authorizer));
                        $('.table_body_contact_authorizer').append(row);
                        }
                    }
                    hide_unhide_table_header();
                    $("#exampleModalContactPerson").modal("hide");
                    }else{
                        $(".underline_new_contact").click();
                    }
              });


//         $(document).on('click', '#partner_search', async function(){
//         if ($('#document_number_search_partner').val() != "" ){
//                    await search_data_of_modal_partner_manager_person($('#document_number_search_partner').val().trim(),'partner');
//                    data = main_data;
//                    main_data = "";
//                    data.then(function(result){
//                        console.log("=============",result)
//                    })
//                        if(data){
//                           $("#table_body_partner_search tr").remove();
//                            $("#search_result_partner_section p").remove();
//                        console.log('data found');
//                            var search_record_section = document.getElementById("search_record_partner_section");
//                            search_record_section.classList.remove('d-none');
//                            row = create_row_search_modal(data);
//                            $('#table_body_partner_search').append(row);
//                        }else{
//                        console.log('data  not found');
//                            var search_record_section = document.getElementById("search_record_partner_section");
//                            search_record_section.classList.add('d-none');
//
//                            $('#search_result_partner_section').append(create_error_message());
//                        }
//                }
//
//              });
//         $(document).on('click', '.create_exist_partner', function(){
//         search_table_record = $('#table_body_partner_search');
//         if (search_table_record.children().length != 0) {
//                var current_row = $('#table_body_partner_search').children();
//                  ajax.jsonRpc("/partner_exist/create",'call',{'id':current_row.children()[6].textContent.trim()}).then(function (data) {
//                    console.log("record contact updated####################");
//                });
//
//                    row = create_row(current_row);
//                    $('.table_body_contact_partner').append(row);
//                    hide_unhide_table_header();
////                    $("#exampleModal_partner").modal("toggle");
//                    }
//              });
//
//              $(document).on('click', '#manager_search', async function(){
//         if ($('#document_number_search_manager').val()){
//
//                        await search_data_of_modal_partner_manager_person($('#document_number_search_manager').val().trim(),'manager');
//                        console.log('call json');
//                        data = main_data;
//                        main_data = "";
//                        if(data){
//                        $("#table_body_manager_search tr").remove();
//                        $("#search_result_manager_section p").remove();
//                        console.log('data found');
//                            var search_record_section = document.getElementById("search_record_manager_section");
//                            search_record_section.classList.remove('d-none');
//                            row = create_row_search_modal(data);
//                            $('#table_body_manager_search').append(row);
//                        }else{
//                        console.log('data  not found');
//                            var search_record_section = document.getElementById("search_record_manager_section");
//                            search_record_section.classList.add('d-none');
//                            $('#search_result_manager_section').append(create_error_message());
//                        }
//
//                }
//
//              });
//              $(document).on('click', '.create_exist_manager', function(){
//         search_table_record = $('#table_body_manager_search');
//         if (search_table_record.children().length != 0) {
//                var current_row = $('#table_body_manager_search').children();
//                  ajax.jsonRpc("/manager_exist/create",'call',{'id':current_row.children()[6].textContent.trim()}).then(function (data) {
//                    console.log("record manager updated####################");
//                });
//
//                    row = create_row(current_row);
//                    $('.table_body_contact_manager').append(row);
//                    hide_unhide_table_header();
////                    $("#exampleModal_manager").modal("toggle");
//                    }
//              });
              $(document).on("click",".contract_open", function () {
                    var id = $(this).parent().next().val();
                    loader = document.getElementById("loader_preview");
                    contract_view = document.getElementById("contract_preview_show");
                    loader.classList.remove('d-none');
                    contract_view.classList.add('d-none');
                    var pre_save_data = false;
                     ajax.jsonRpc("/render/report",'call',{'id':id}).then(function (data) {
                        if(data){
                             pre_save_data= data;
                              contract_view.src = `data:application/pdf;base64,${data['pdf_data']}`;
                              contract_view.classList.remove('d-none');
                              loader.classList.add('d-none');
                        }else{
                            var no_contract = document.createElement("h4");
                            no_contract.innerHtml = 'There is no contract';
                            $('#contract_preview_id').append(no_contract);

                        }


                    });

                });

                $(document).on("click",".fa-universal-access", function () {
                    var id_tag = $(this).parent().parent().children()[8];
                    var id = id_tag.textContent.trim();
                    $("#portal_access_Modal").modal("toggle");
                    console.log("id_atgggggggggggggggggggggggggg", id);
                    ajax.jsonRpc("/grant_portal_access",'call',{'id':id}).then(function (data) {

                        if (data){
                            if (data['success_message']){
                                console.log("success");
                                $("#portal_access_message").removeClass();
                                $('#loader_preview_portal').addClass('d-none');
                                $('#portal_access_message').text(data['success_message']);
                                $("#portal_access_message").addClass("alert");
                                $("#portal_access_message").addClass("alert-success");

                            }else if (data['error_message']){
                                $("#portal_access_message").removeClass();
                                $('#loader_preview_portal').addClass('d-none');
                                console.log("error",data['success_message']);
                                $('#portal_access_message').text(data['error_message']);
                                 $("#portal_access_message").addClass("alert");
                                $("#portal_access_message").addClass("alert-warning");

                            }
                        }
                    });
                });

                $( "#passport_name_extra_contact" ).change(function() {
                   $('#full_name_extra_contact').val($('#passport_name_extra_contact').val());
                });
                 $( "#passport_name_ar_extra_contact" ).change(function() {
                   $('#full_name_ar_extra_contact').val($('#passport_name_ar_extra_contact').val());
                });

                $( "#name_english_extra_contact" ).change(function() {
                   $('#full_name_extra_contact').val($('#name_english_extra_contact').val());
                });

                $( "#name_ar_extra_contact" ).change(function() {
                   $('#full_name_ar_extra_contact').val($('#name_ar_extra_contact').val());
                });

                $( "#employee_passport_name" ).change(function() {
                   $('#employee_name_id').val($('#employee_passport_name').val());
                });

                function hide_job_position(residency_type,job_position, job_position_div){
                    if ( residency_type.val() == 'family'){
                       job_position_div.addClass('d-none');
                        job_position.val('');
                    }else{
                    job_position_div.removeClass('d-none');
                    }
                }
                // Primary contact
                // hide job position
                $( "#primary_in_charge_residency_type" ).change(function() {
                    hide_job_position($('#primary_in_charge_residency_type'),$('#primary_in_charge_job_position'), $('#primary_in_charge_job_position_div'))
                });
                // radio change
                $( "input[name='primary_qid_radio']" ).click(function() {
                $("#primary_person_accordionUser").removeClass('d-none');
                $("#collapseOneUser").removeClass('show');
                if($("#primary_qid_radio_yes").prop('checked') == true){
                     $("#primary_qid_accordionUser").removeClass('d-none');
                         $("#collapseThreeUser").addClass('show');
                     $("#primary_passport_accordionUser").addClass('d-none');
                }else{
                    $("#primary_qid_accordionUser").addClass('d-none');
                         $("#collapseTwoUser").addClass('show');
                    $("#primary_passport_accordionUser").removeClass('d-none');
                }

                });

                function onchange_en_ar_name(get_val,set_val){
                 $(set_val).val($(get_val).val());
                }
                 $( "#primary_in_charge_passport_name" ).change(function() {
                 onchange_en_ar_name('#primary_in_charge_passport_name','#primary_in_charge_name');

                });
                $( "#primary_in_charge_passport_name_ar" ).change(function() {
                 onchange_en_ar_name('#primary_in_charge_passport_name_ar','#primary_in_charge_user_name_ar');

                });
                $( "#primary_in_charge_name_english" ).change(function() {
                 onchange_en_ar_name('#primary_in_charge_name_english','#primary_in_charge_name');
                });
                $( "#primary_in_charge_qid_name_ar" ).change(function() {
                 onchange_en_ar_name('#primary_in_charge_qid_name_ar','#primary_in_charge_user_name_ar');
                });
                 //contact residency type
                $( "#residency_type_extra_contact" ).change(function() {
                    hide_job_position($('#residency_type_extra_contact'),$('#job_position_extra_contact'), $('#job_position_extra_contact_div'))
                });


                //contact residency type
                $( "#residency_type_extra_contact" ).change(function() {
                    hide_job_position($('#residency_type_extra_contact'),$('#job_position_extra_contact'), $('#job_position_extra_contact_div'))
                });
                //contact residency type
                $( ".contract_residency_type").change(function() {
                    console.log("changing-----");
                    hide_job_position($('.contract_residency_type'),$('.contract_job_position'), $('.contract_job_position_div'))
                });

                //update contact residency type
                $( "#update_residency_type_extra_contact" ).change(function() {
                    hide_job_position($('#update_residency_type_extra_contact'),$('#update_job_position_extra_contact'), $('#update_job_position_extra_contact_div'))
                });

                 $( "#passport_name_extra_contact" ).change(function() {
                   $('#name_english_extra_contact').val($('#passport_name_extra_contact').val());
                });
                $( "#passport_name_ar_extra_contact" ).change(function() {
                   $('#name_ar_extra_contact').val($('#passport_name_ar_extra_contact').val());
                });

                $( "#update_passport_name_extra_contact" ).change(function() {
                   $('#update_full_name_extra_contact').val($('#update_passport_name_extra_contact').val());
                });
                $( "#update_passport_name_ar_extra_contact" ).change(function() {
                   $('#update_full_name_ar_extra_contact').val($('#update_passport_name_ar_extra_contact').val());
                });

                $( "#update_name_english_extra_contact" ).change(function() {
                   $('#update_full_name_extra_contact').val($('#update_name_english_extra_contact').val());
                });
                $( "#update_name_ar_extra_contact" ).change(function() {
                   $('#update_full_name_ar_extra_contact').val($('#update_name_ar_extra_contact').val());
                });


                $( "#update_birth_date_extra_contact" ).change(function() {

                   $('#update_qid_birth_date_extra_contact').val($("#update_birth_date_extra_contact" ).val());
                });
                $( "#update_qid_birth_date_extra_contact" ).change(function() {

                   $('#update_birth_date_extra_contact').val($("#update_qid_birth_date_extra_contact" ).val())
                });

                $( "#birth_date_extra_contact" ).change(function() {
                   $('#qid_birth_date_extra_contact').val($("#birth_date_extra_contact" ).val());
                });
                $( "#qid_birth_date_extra_contact" ).change(function() {

                   $('#birth_date_extra_contact').val($("#qid_birth_date_extra_contact" ).val())
                });
                $( "input[name='qid_radio']" ).click(function() {
                console.log('radio click');
                    $("#person_accordion").removeClass('d-none');
                    $("#collapseOneUpdate").removeClass('show');
                  if($("#qid_radio_yes").prop('checked') == true){
                     $("#qid_accordion").removeClass('d-none');
                     $("#collapseThreeUpdate").addClass('show');

                     $("#passport_accordion").addClass('d-none');
                }else{
                    $("#qid_accordion").addClass('d-none');
                     $("#collapseTwoUpdate").addClass('show');
                    $("#passport_accordion").removeClass('d-none');
                }
                });


                //manager in charge detail
                //passport
                $( "#manager_in_charge_passport_name" ).change(function() {
                   $('#manager_in_charge_name').val($('#manager_in_charge_passport_name').val());
                });
                 $( "#manager_in_charge_passport_name_ar" ).change(function() {
                   $('#manager_in_charge_user_name_ar').val($('#manager_in_charge_passport_name_ar').val());
                });

                //QID
                 $( "#manager_in_charge_name_english" ).change(function() {
                   $('#manager_in_charge_name').val($('#manager_in_charge_name_english').val());
                });
                 $( "#manager_in_charge_name_ar" ).change(function() {
                   $('#manager_in_charge_user_name_ar').val($('#manager_in_charge_name_ar').val());
                });
                // radio button

                $( "input[name='manager_qid_radio']" ).click(function() {

                  manager_radio_click();
                });
                // job position hide
                $( "#manager_in_charge_residency_type" ).change(function() {
                    hide_job_position($('#manager_in_charge_residency_type'),$('#manager_in_charge_job_position'), $('#manager_in_charge_job_position_div'))
                });


                //contract accordion

                // radio button
//                $( "input[name='contract_qid_radio']" ).click(function() {
                 $(document).on("click",".contract_accordion_radio", function () {
                    id = this.id.split('-')
                    $('#'+this.id).closest('.radio_row').next().find('#person_accordionContract' + id[0]).removeClass('d-none');
                     $('#collapseOneContract'+id[0]).removeClass('show');
                      if($('#'+this.id).val() == 'yes'){
                          $('#'+this.id).closest('.radio_row').next().find('#qid_accordionContract' + id[0]).removeClass('d-none');
                          $('#collapseThreeContract'+id[0]).addClass('show');
                         $('#'+this.id).closest('.radio_row').next().find('#passport_accordionContract' + id[0]).addClass('d-none');
                    }else{
                        $('#'+this.id).closest('.radio_row').next().find('#qid_accordionContract' + id[0]).addClass('d-none');
                        $('#collapseTwoContract'+id[0]).addClass('show');
                        $('#'+this.id).closest('.radio_row').next().find('#passport_accordionContract' + id[0]).removeClass('d-none');
                    }
                });
                $(document).on("change","#qid_extra_contact", function () {
                    var val = $("#qid_extra_contact").val()
                    ajax.jsonRpc("/check/duplicate_document",'call',{'val': val, 'type': 'QID'}).then(function (data) {
                        if(data == true){
                            var msg = "A document with this document number already exists!"
                            $("#error_msg").text(msg);
                            $("#exampleModalContactPerson").modal("toggle");
                            $("#exampleModalError").modal("show");
                        }

                    });
                });
                $(document).on("change","#passport_extra_contact", function () {
                    var val = $("#passport_extra_contact").val()
                    ajax.jsonRpc("/check/duplicate_document",'call',{'val': val, 'type': 'Passport'}).then(function (data) {
                        if(data == true){
                            var msg = "A document with this document number already exists!"
                            $("#error_msg").text(msg);
                            $("#exampleModalContactPerson").modal("toggle");
                            $("#exampleModalError").modal("show");
                        }

                    });
                });
                $(document).on("change","#update_passport_extra_contact", function () {
                    var val = $("#update_passport_extra_contact").val()
                    ajax.jsonRpc("/check/duplicate_document",'call',{'val': val, 'type': 'Passport', 'contact_id': $("#contact_id").val()}).then(function (data) {
                        if(data == true){
                            var msg = "A document with this document number already exists!"
                            $("#error_msg").text(msg);
                            $("#update_contact_person_modal").modal("toggle");
                            $("#exampleModalError").modal("show");
                        }

                    });
                });
                $(document).on("change","#update_qid_extra_contact", function () {
                    var val = $("#update_qid_extra_contact").val()
                    ajax.jsonRpc("/check/duplicate_document",'call',{'val': val, 'type': 'QID', 'contact_id': $("#contact_id").val()}).then(function (data) {
                        if(data == true){
                            var msg = "A document with this document number already exists!"
                            $("#error_msg").text(msg);
                            $("#update_contact_person_modal").modal("toggle");
                            $("#exampleModalError").modal("show");
                        }

                    });
                });

                $(document).on("change","#commercial_reg_no", function () {
                    var val = $("#commercial_reg_no").val()
                    ajax.jsonRpc("/check/duplicate_document",'call',{'val': val, 'type': 'Commercial Registration (CR) Application'}).then(function (data) {
                        if(data == true){
                            var msg = "A document with this document number already exists!"
                            $("#error_msg").text(msg);
//                            $("#exampleModalContactPerson").modal("toggle");
                            $("#exampleModalError").modal("show");
                            $("#commercial_reg_no").val('');
                        }

                    });
                });
                $(document).on("change","#license_number", function () {
                    var val = $("#license_number").val()
                    ajax.jsonRpc("/check/duplicate_document",'call',{'val': val, 'type': 'Commercial License'}).then(function (data) {
                        if(data == true){
                            var msg = "A document with this document number already exists!"
                            $("#error_msg").text(msg);
//                            $("#exampleModalContactPerson").modal("toggle");
                            $("#exampleModalError").modal("show");
                            $("#license_number").val('');
                        }

                    });
                });
                $(document).on("change","#manager_in_charge_passport", function () {
                    var val = $('#manager_in_charge_passport').val()
                    ajax.jsonRpc("/check/duplicate_document",'call',{'val': val, 'type': 'Passport'}).then(function (data) {
                        if(data == true){
                            var msg = "A document with this document number already exists!"
                            $("#error_msg").text(msg);
//                            $("#exampleModalContactPerson").modal("toggle");
                            $("#exampleModalError").modal("show");
                            $('#manager_in_charge_passport').val('');
                        }

                    });
                });
                $(document).on("change","#manager_in_charge_qid", function () {
                    var val = $('#manager_in_charge_qid').val()
                    ajax.jsonRpc("/check/duplicate_document",'call',{'val': val, 'type': 'QID'}).then(function (data) {
                        if(data == true){
                            var msg = "A document with this document number already exists!"
                            $("#error_msg").text(msg);
//                            $("#exampleModalContactPerson").modal("toggle");
                            $("#exampleModalError").modal("show");
                            $('#manager_in_charge_qid').val('');
                        }

                    });
                });
                $(document).on("change","#est_id", function () {
                    var val = $("#est_id").val()
                    ajax.jsonRpc("/check/duplicate_document",'call',{'val': val, 'type': 'Establishment Card'}).then(function (data) {
                        if(data == true){
                            var msg = "A document with this document number already exists!"
                            $("#error_msg").text(msg);
//                            $("#exampleModalContactPerson").modal("toggle");
                            $("#exampleModalError").modal("show");
                            $("#est_id").val('');
                        }

                    });
                });
                $(document).on("change",".contract_passport_no", function () {
                    var val = $(this).val()
                    ajax.jsonRpc("/check/duplicate_document",'call',{'val': val, 'type': 'Passport'}).then(function (data) {
                        if(data == true){
                            var msg = "A document with this document number already exists!"
                            $("#error_msg").text(msg);
//                            $("#exampleModalContactPerson").modal("toggle");
                            $("#exampleModalError").modal("show");
                            $(this).val('');
                        }

                    });
                });
                $(document).on("change",".contract_qid_no", function () {
                    var val = $(this).val()
                    ajax.jsonRpc("/check/duplicate_document",'call',{'val': val, 'type': 'QID'}).then(function (data) {
                        if(data == true){
                            var msg = "A document with this document number already exists!"
                            $("#error_msg").text(msg);
//                            $("#exampleModalContactPerson").modal("toggle");
                            $("#exampleModalError").modal("show");
                            $(this).val('');
                        }
                    });
                });

                $(document).on("change","#na_zone", function () {
                    var selectStreet = $("#na_street");
                   ajax.jsonRpc("/get/street",'call',{'zone':$("#na_zone").val()}).then(function (data) {
                        selectStreet.html('');
                        var opt = $('<option>').text('Select...')
                                    .attr('value', '');
                        selectStreet.append(opt);
                        _.each(data.streets, function (x) {
                            var opt = $('<option>').text(x[1])
                                .attr('value', x[0])
                            selectStreet.append(opt);
                        });
                        selectStreet.parent('div').show();
                    });
                });

                $(document).on("change","#na_street", function () {
                    var selectBuilding = $("#na_building");
                   ajax.jsonRpc("/get/building",'call',{'street':$("#na_street").val()}).then(function (data) {
                        selectBuilding.html('');
                        var opt = $('<option>').text('Select...')
                                    .attr('value', '');
                        selectBuilding.append(opt);
                        _.each(data.buildings, function (x) {
                            var opt = $('<option>').text(x[1])
                                .attr('value', x[0])
                            selectBuilding.append(opt);
                        });
                        selectBuilding.parent('div').show();
                    });
                });


                $(document).on("change",".contract_qid_english_name", function () {
                    id = this.id.split('-');
                    $('#'+id[0]+'-contract_full_name').val(this.value);
                });
                $(document).on("change",".contract_qid_arabic_name", function () {
                    id = this.id.split('-');
                    $('#'+id[0]+'-contract_name_ar').val(this.value);
                });
                $(document).on("change",".contract_passport_english_name", function () {
                    id = this.id.split('-');
                    $('#'+id[0]+'-contract_full_name').val(this.value);
                });
                $(document).on("change",".contract_passport_arabic_name", function () {
                    id = this.id.split('-');
                    $('#'+id[0]+'-contract_name_ar').val(this.value);
                });

                $(document).on("change",".contract_residency_type", function () {
                    id = this.id.split('-');
                    hide_job_position($('#'+id[0] +'-contract_residency_type'),$('#'+id[0]+'-job_position_extra_contact'), $('#'+id[0]+'-job_position_div'))
                });

                // job position hide
                $( "#contract_residency_type" ).change(function() {
                    hide_job_position($('#contract_residency_type'),$('#contract_job_position'), $('#contract_job_position_div'))
                });





//                $( "#qid_check_box" ).change(function() {
//                  if($("#qid_check_box").prop('checked') == true){
//                     $("#qid_accordion").removeClass('d-none');
//                }else{
//                    $("#qid_accordion").addClass('d-none');
//                }
//                });

                 $( "input[name='update_qid_radio']" ).click(function() {
                 $('#updatecollapseOne').removeClass('show');
                  if($("#update_qid_radio_yes").prop('checked') == true){
                     $("#update_qid_accordion").removeClass('d-none');
                     $("#updatecollapseThree").addClass('show');
//                     $("#update_qid_accordion").collapse('toggle');
                     $("#update_passport_accordion").addClass('d-none');
                }else{
                    $("#update_qid_accordion").addClass('d-none');
                    $("#updatecollapseTwo").addClass('show');
                    $("#update_passport_accordion").removeClass('d-none');
                }
                });



                $( "#employee_qid_check_box" ).change(function() {
                  if($("#employee_qid_check_box").prop('checked') == true){
                     $("#employee_qid_accordion").removeClass('d-none');
                }else{
                    $("#employee_qid_accordion").addClass('d-none');
                }
                });


remove_next_button();
});
});