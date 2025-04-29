odoo.define('ebs_fusion_documents.portal_documents', function (require) {
'use strict';
    var core = require('web.core');
    var ajax = require('web.ajax');
    var _t = core._t;
    var rpc = require('web.rpc')

    jQuery( document ).ready(function() {
        $('.issue_date').hide();
        $('.expiry_date').hide();
        $('input[name="issue_date"]').change(function(ev){
            $('input[name="expiry_date"]').attr('min', $('input[name="issue_date"]').val());
        });
        $('select[name="doc_type"]').change(function(ev){
            var doc_type_id = $('select[name="doc_type"]').val();
            ajax.jsonRpc("/search/document_type",'call',{'doc_type_id':doc_type_id}).then(function (data) {
                console.log(data);
                if(data['required'] == 'required'){
                    $('.issue_date').show();
                    $('.expiry_date').show();
                    $('input[name="issue_date"]').attr('required',"true");
                    $('input[name="expiry_date"]').attr('required',"true");
                }
                if(data['required'] == 'no'){
                    $('.issue_date').hide();
                    $('.expiry_date').hide();
                    $('input[name="issue_date"]').removeAttr('required');
                    $('input[name="expiry_date"]').removeAttr('required');
                }
                if(data['required'] == 'optional'){
                    $('.issue_date').show();
                    $('.expiry_date').show();
                    $('input[name="issue_date"]').removeAttr('required');
                    $('input[name="expiry_date"]').removeAttr('required');
                }
            });
        });
        $('.sort_by_number').click(function(ev){
            console.log("=============",$(ev.currentTarget))
//            $(ev.currentTarget).
            window.location = window.location.origin + '/my/docs'+ '?' + "sortby=number"
        });
         $('.sort_by_name').click(function(ev){
            window.location = window.location.origin + '/my/docs'+ '?' + "sortby=name"
        });
         $('.sort_by_issue_date').click(function(ev){
            window.location = window.location.origin + '/my/docs'+ '?' + "sortby=issue_date"
        });
         $('.sort_by_expire_date').click(function(ev){
            window.location = window.location.origin + '/my/docs'+ '?' + "sortby=expiry_date"
        });
        $('.sort_by_status').click(function(ev){
            window.location = window.location.origin + '/my/docs'+ '?' + "sortby=status"
        });
        $(".folder-click").click(function(ev){
            console.log($(this).children('input[name="folder_id"]').val(),"LKKKKKKKKK");
            window.location = window.location.origin + '/my/docs'+ '?' + "folder=" + $(this).children('input[name="folder_id"]').val();
        });
        var urlParams = new URLSearchParams(window.location.search);
        if(urlParams.get('folder')){
            console.log(urlParams.get('folder'),"LLLLL");
            $("input[name='folder_id']").each(function() {
                if($(this).val() == urlParams.get('folder')){
                    console.log($(this).closest('tr'),"LLL");
                    $(this).parents('tr').addClass('active');
                }
            });
        };

    });
});