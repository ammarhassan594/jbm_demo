/** @odoo-module **/

import { registerInstancePatchModel } from "@mail/model/model_core";

registerInstancePatchModel("mail.chatter", "sla_activity_type/static/src/js/new_chatter.js", {

    /**
     * @override
     */
    _created() {
        const res = this._super(...arguments);
//        console.log("In Created ")
        this.onClickScheduleActivityType = this.onClickScheduleActivityType.bind(this);
        return res;
    },


    //----------------------------------------------------------------------
    // Handlers
    //----------------------------------------------------------------------

    onClickScheduleActivityType(ev) {
             console.log("This ", this)
             console.log("This thread ", this.thread)
                const action = {
                    type: 'ir.actions.act_window',
                    name: this.env._t("SLA Activity"),
                    res_model: 'sla.activity.wizard',
                    view_mode: 'form',
                    views: [[false, 'form']],
                    target: 'new',
                    context: {
                            default_res_id: this.thread.id,
                            default_res_model: this.thread.model,
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
    },

});
