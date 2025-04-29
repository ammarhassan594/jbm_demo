odoo.define('ebs_fusion_theme.portal_service', function (require) {

    var ajax = require('web.ajax');

    $(document).ready(function() {
        console.log("@@@@@@@2",$('#creation_date'));
        $('.datepicker').datepicker({
            dateFormat: 'dd/mm/yy',
            onClose: function() {
                $(this).removeClass("hasDatepicker");
             }
        });
        $('#creation_date').focus(function(ev) {
            console.log("8888888888888888(((");
            if($('#ui-datepicker-div').css('display') === 'block'){
                $("#creation_date").datepicker("hide");
            }
            else{
                $("#creation_date").datepicker("show");
            }
        });

        $(".o_website_form_send").click(function(ev){
            let searchParams = new URLSearchParams(window.location.search);
            if(searchParams.has('service')){
                $("input[name='service_type']").val(searchParams.get('service'));
            }

        });
        $('#togglePassword').click(function(ev){
            var password = document.querySelector('#password');
            var type = password.getAttribute('type') === 'password' ? 'text' : 'password';
            password.setAttribute('type', type);
            this.classList.toggle('fa-eye-slash');
        });
        $('#togglePassword1').click(function(ev){
            var password1 = document.querySelector('#password');
            var type = password1.getAttribute('type') === 'password' ? 'text' : 'password';
            password1.setAttribute('type', type);
            this.classList.toggle('fa-eye-slash');
        });
        $('#togglePassword2').click(function(ev){
            var confirm_password = document.querySelector('#confirm_password');
            var type = confirm_password.getAttribute('type') === 'password' ? 'text' : 'password';
            confirm_password.setAttribute('type', type);
            this.classList.toggle('fa-eye-slash');
        });

         $('.sort_by_invoice_name').click(function(ev){
//            $(ev.currentTarget).
            window.location = window.location.origin + '/my/invoices'+'?'+'sortby=name'
        });
         $('.sort_invoice_date').click(function(ev){
            window.location = window.location.origin + '/my/invoices'+'?'+'sortby=date'
        });
         $('.sort_by_due_date').click(function(ev){
            window.location = window.location.origin + '/my/invoices'+'?'+'sortby=duedate'
        });
         $('.sort_by_invoice_state').click(function(ev){
            window.location = window.location.origin + '/my/invoices'+'?'+'sortby=state'
        });
//        $('.sort_by_status').click(function(ev){
//            window.location = window.location.origin + '/my/docs'+ '?' + "sortby=status"
//        });

    });
});