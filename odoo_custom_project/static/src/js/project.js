odoo.define('vkp_project_ext.update_kanban', function (require) {
    'use strict';

    var KanbanRecord = require('web.KanbanRecord');

    KanbanRecord.include({
        //--------------------------------------------------------------------------
        // Private
        //--------------------------------------------------------------------------

        /**
         * @override
         * @private
         */

        _openRecord: function () {
            if (this.modelName === 'project.project') {
                this.$('.o_kanban_card_manage_section a').last().click();
            }

            else {
                this._super.apply(this, arguments);
        }
    },

    });
});
