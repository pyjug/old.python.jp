// IOTBS2.1 :: Invasion of the Body Switchers - Look Who's Switching Too
// >>> Key file for all versions
// ***********************************************
// This copyright statement must remain in place for both personal and commercial use
// GNU General Public License -- http://www.gnu.org/copyleft/gpl.html
// ***********************************************
// Original concept by Andy Clarke -- http://www.stuffandnonsense.co.uk/
// DOM scripting by brothercake -- http://www.brothercake.com/
// Create element and attributes based on a method by beetle -- http://www.peterbailey.net/
//************************************************
function iotbs() { //open initialisation function
//************************************************


//initialise the preferences manager ('canvas-element', 'path-for-load-mode')
var switcher = new switchManager('body', '');


/*****************************************************************************
 Define switching controls
*****************************************************************************/



//create a new switcher control ('container-id', 'label', 'is-native-switcher', '"selected" text')
var screenSwitcher = new bodySwitcher('screen-switcher', 'Screen styles', 'no', '');

//add a new class option ('classname', 'label')
screenSwitcher.defineClass('default', 'Normal contrast');
screenSwitcher.defineClass('high', 'High contrast');
screenSwitcher.defineClass('highvisibility', 'High visibility');


var printSwitcher = new bodySwitcher('print-switcher', 'Print styles', 'no', '');
printSwitcher.defineClass('default', 'Default');
printSwitcher.defineClass('small-sans', 'Small sans');
printSwitcher.defineClass('large-serif', 'Large serif');


var projectionSwitcher = new bodySwitcher('projection-switcher', 'Projection styles', 'no', '');
projectionSwitcher.defineClass('default', 'Default');
projectionSwitcher.defineClass('fluid', 'Fluid layout');


var auralSwitcher = new bodySwitcher('aural-switcher', 'Aural styles', 'no', '');
auralSwitcher.defineClass('default', 'Man');
auralSwitcher.defineClass('female', 'Woman');
auralSwitcher.defineClass('child', 'Child');




/*****************************************************************************
*****************************************************************************/
}; //close initialisation function
