/** @odoo-module **/

import { registerNewModel } from '@mail/model/model_core';
import { attr, many2one, one2one } from '@mail/model/model_field';
import { clear, insert, insertAndReplace, link, unlink } from '@mail/model/model_field_command';
import { OnChange } from '@mail/model/model_onchange';

console.log('in js file');

function factory(dependencies) {
    console.log('in function');
    class SLA extends dependencies['mail.model']{
            /**
             * @override
             */
            _created() {
                this.onClickScheduleActivityType = this.onClickScheduleActivityType.bind(this);
            }
            /**
             * Handles click on "schedule activity" button.
             *
             * @param {MouseEvent} ev
             */
            onClickScheduleActivityType(ev) {
                const action = {
                    type: 'ir.actions.act_window',
                    name: this.env._t("Schedule Activity"),
                    res_model: 'mail.activity',
                    view_mode: 'form',
                    views: [[false, 'form']],
                    target: 'new',
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


        }

    SLA.fields = {

    componentChatterTopbar: attr(),

    id: attr({
            readonly: true,
            required: true,
        }),

    };
    SLA.identifyingFields = ['id'];
    SLA.modelName = 'sla.activity.type';
    console.log('SLA object');
    console.log(SLA);
    return SLA;

}
registerNewModel('sla.activity.type', factory);