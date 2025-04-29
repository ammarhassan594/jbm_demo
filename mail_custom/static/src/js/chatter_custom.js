/** @odoo-module **/

import { registerInstancePatchModel } from "@mail/model/model_core";

registerInstancePatchModel("mail.chatter", "mail_custom/static/src/js/chatter_custom.js", {

        /**
         * Handles click on "schedule activity" button.
         *
         * @param {MouseEvent} ev
         Override To Change in context of the action
         */
        onClickScheduleActivity(ev) {
            const action = {
                type: 'ir.actions.act_window',
                name: this.env._t("Schedule Activity"),
                res_model: 'mail.activity',
                view_mode: 'form',
                views: [[false, 'form']],
                target: 'new',
                context: {
                    default_res_id: this.thread.id,
                    default_res_model: this.thread.model,
                    default_from_view: true,
                },
                res_id: false,
            };
            return this.env.bus.trigger('do-action', {
                action,
                options: {
                    on_close: () => {
                        if (!this.componentChatterTopbar) {
                            return;
                        }
                        this.componentChatterTopbar.trigger('reload', { keepChanges: true });
                    },
                },
            });
        }


});

