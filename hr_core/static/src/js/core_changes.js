odoo.define('hr_core.CoreChanges', function (require) {
    "use strict";

    var UserMenu = require('web.UserMenu');

    UserMenu.include({
        render: function () {
            $('[data-menu="account"]').hide();
        },

        _onMenuSupport: function () {
            window.open('https://albvl1plmmcs002.services.mdc/glpi/', '_blank');
        }
    });

});
