###############################################################################
#
#    Trey, Kilobytes de Soluciones
#    Copyright (C) 2019-Today Trey, Kilobytes de Soluciones <www.trey.es>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
{
    'name': 'Website Bootstrap Select',
    'category': 'Website',
    'summary': 'Add scripts and styles to use Bootstrap Select library',
    'version': '12.0.1.0.0',
    'author': 'Trey (www.trey.es)',
    'depends': ['website'],
    'assets': {
        'web.assets_frontend': [
            'website_bootstrap_select/static/src/js/lib/bootstrap-select/css/bootstrap-select.min.css',
            'website_bootstrap_select/static/src/js/lib/bootstrap-select/js/bootstrap-select.min.js',
            'website_bootstrap_select/static/src/js/website_bootstrap_select.js'
        ]
    },
    'installable': True,

}
