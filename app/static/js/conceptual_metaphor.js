/**
 * Script to get all conceptual metaphors from server and display in dropdown.
 * When a value is selected, update the conceptual metaphor text input.
 *
 * Author: Matthew Turner <maturner01@gmail.com>
 * Date: 2/13/2017
 */

var cm_options = [];

$.get('/all_conceptual_metaphors').done(
  (data) => {
    cm_options = data['conceptual_metaphors'];
    cm_options.forEach(
      option => {
        $('#cm_dropdown').append(
          '<option value=' + option + '>' + option + '</option>'
        );
        console.log(option);
      }
    );
  }
);

$('#cm_dropdown').change( () => {
  
  // get the selected option from the dropdown
  var selected = $('#cm_dropdown option:selected').text();

  // put that option into the conceptual metaphor input box
  $('#conceptual_metaphor').val(selected);

});
