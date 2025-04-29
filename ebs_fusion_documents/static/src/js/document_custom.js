odoo.define('ebs_fusion_documents.DocumentsInspectorCustom', function (require) {
"use strict";

var core = require('web.core');
var _t = core._t;
var qweb = core.qweb;
var fieldRegistry = require('web.field_registry');
var FieldMany2One = require('documents.DocumentsInspector');

console.log("sdfsdfsdfsdsd")
    FieldMany2One.include({


     _renderField: function (fieldName, options) {
        options = options || {};

        // generate the record to pass to the FieldWidget
        var values = _.uniq(_.map(this.records, function (record) {
            return record.data[fieldName] && record.data[fieldName].res_id;
        }));
        var record;
        if (values.length > 1) {
            record = this._generateCommonRecord(fieldName);
        } else {
            record = this.records[0];
        }

        var $row = $(qweb.render('documents.DocumentsInspector.infoRow'));

        // render the label
        if(fieldName == 'partner_id')
        {
        var $label = $(qweb.render('documents.DocumentsInspector.fieldLabel', {
            icon: options.icon,
            label: 'Partner',
            name: fieldName,
        }));
        console.log("=-=---------=-=-=-=-=-=-=-=-=-=-=-=-=-=-",$label)
        }
        else
        {
            var $label = $(qweb.render('documents.DocumentsInspector.fieldLabel', {
            icon: options.icon,
            label: options.label || record.fields[fieldName].string,
            name: fieldName,
        }));
        }


        $label.appendTo($row.find('.o_inspector_label'));

        // render and append field
        var type = record.fields[fieldName].type;
        var FieldWidget = fieldRegistry.get(type);
        options = _.extend({}, options, {
            noOpen: true, // option for many2one fields
            viewType: 'kanban',
        });
        var fieldWidget = new FieldWidget(this, fieldName, record, options);
        const prom = fieldWidget.appendTo($row.find('.o_inspector_value')).then(function() {
            fieldWidget.getFocusableElement().attr('id', fieldName);
            if (type === 'many2one' && values.length > 1) {
                fieldWidget.$el.addClass('o_multiple_values');
            }
        });
        $row.insertBefore(this.$('.o_inspector_fields tbody tr.o_inspector_divider'));
        return prom;
    },







    _renderFields: function () {
//        var options = {mode: 'edit'};
        var options = {};
        var proms = [];
        if (this.records.length === 1) {
            proms.push(this._renderField('name', options));
            if (this.records[0].data.type === 'url') {
                proms.push(this._renderField('url', options));
            }
            proms.push(this._renderField('partner_id', options));
            proms.push(this._renderField('employee_id', options));
            console.log("pppppppppppppppppppp",options);
        }
        if (this.records.length > 0) {
            proms.push(this._renderField('owner_id', options));
            console.log("ttttttttttttttttttttt",options);
            proms.push(this._renderField('folder_id', {
                icon: 'fa fa-folder o_documents_folder_color'
            }));
        }
        return Promise.all(proms);
    }
    })
});