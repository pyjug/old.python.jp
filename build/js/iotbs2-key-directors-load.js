// IOTBS2.1 :: Invasion of the Body Switchers - Look Who's Switching Too
// >>> Key file for all versions
// ***********************************************
// This copyright statement must remain in place for both personal and commercial use
// GNU General Public License -- http://www.gnu.org/copyleft/gpl.html
// ***********************************************
function iotbs() { //open initialisation function
var switcher = new switchManager('body', '/styles/');
var screenSwitcher = new bodySwitcher('screen-switcher', 'Screen styles', 'no', '*');
screenSwitcher.defineClass('default', 'normal');
screenSwitcher.defineClass('largefonts', 'large');
screenSwitcher.defineClass('defaultfonts', 'userpref');
}; //close initialisation function
