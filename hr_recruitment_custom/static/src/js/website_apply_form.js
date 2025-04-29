odoo.define('hr_recruitment_custom.website_apply_form', function (require) {
    'use strict';

    var ajax = require('web.ajax');
    var publicWidget = require('web.public.widget');


    publicWidget.registry.WebsiteMyPortal = publicWidget.Widget.extend({
        selector: '.s_website_form',
        events: {
            'change #country_select': '_onChangeGenderAndNation',
            'change #gender_select': '_onChangeGenderAndNation',
        },


        /**
         * @override
         */
        start: function () {

            this.$related_country = this.$('#country_select');
            this.$related_gender = this.$('#gender_select');
            this.$related_service = this.$('#national_service_div');
            this.$related_service_field = this.$('#national_service_field');

            return this._super.apply(this, arguments);
        },

        //--------------------------------------------------------------------------
        // Private
        //--------------------------------------------------------------------------

        /**
         * @private
         */

        _onChangeGenderAndNation: function () {
            var CountrySelectedField = $(this.$related_country[0].selectedOptions).data("code");
            var GenderSelectedField = $(this.$related_gender[0].selectedOptions).val();
            debugger;
            if (GenderSelectedField === 'male' && CountrySelectedField === "AE") {
                this.$related_service.show();
            } else {
                this.$related_service_field.prop('checked', false);
                this.$related_service.hide();
            }


        },

        //--------------------------------------------------------------------------
        // Handlers
        //--------------------------------------------------------------------------

        /**
         * @private
         */
        // _onCGVCheckboxClick: function () {
        //     this._adaptPayButton();
        // },
    });
});


// odoo.define('website_calendar.appointment_form', function (require) {
//     'use strict';
//
//     require('web_editor.ready');
//
//     if (!$('.o_website_calendar_form').length) {
//         return $.Deferred().reject("DOM doesn't contain '.o_website_calendar_form'");
//     }
//
//     $(".appointment_submit_form select[name='country_id']").change(function () {
//         var country_code = $(this).find('option:selected').data('phone-code');
//         $('.appointment_submit_form #phone_field').val(country_code);
//     });
// });
