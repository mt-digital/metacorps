/**
 * Edit an instance within the facet view 
 *
 * Author: Matthew Turner <maturner01@gmail.com>
 */

function makeFilledForm(instanceData) {
  var fig_checked =  instanceData['figurative'] == 'True' ? 'checked' : '';
  var incl_checked =  instanceData['include'] == 'True' ? 'checked' : '';

  var filledForm = 
    '<div class="row">Figurative (check for yes)?</div><input ' + fig_checked + 
      ' id="figurative" name="figurative" type="checkbox" value="y"></div>' +

    '<div class="row">Include (check for yes)?</div><input ' + incl_checked + 
        ' id="include" name="include" type="checkbox" value="y"></div>' +

    '<div class="row"><label for="conceptual_metaphor">Conceptual metaphor</label>: ' +
                     '<input id="conceptual_metaphor" name="conceptual_metaphor" size="60" type="text" ' + 
                     ' value="' + instanceData['conceptual_metaphor'] + '"></div>' + 
      
    '<div class="row"><label for="subjects">Object(s)</label>: ' +
                     '<input id="subjects" name="subjects" size="60" type="text" ' + 
                     ' value="' + instanceData['subjects'] + '"></div>' +

    '<div class="row"><label for="objects">Object(s)</label>: ' +
                     '<input id="objects" name="objects" size="60" type="text" ' + 
                     ' value="' + instanceData['objects'] + '"></div>' +

    '<div class="row"><label for="spoken_by">Object(s)</label>: ' +
       '<input id="spoken_by" name="spoken_by" size="60" type="text" ' + 
       ' value="' + instanceData['spoken_by'] + '"></div>' +

    '<div class="row"><label for="tense">Tense</label>: ' + 
       '<input id="tense" name="tense" size="60" type="text" ' + 
       ' value="' + instanceData['tense'] + '"></div>' +

    '<div class="row"><label for="active_passive">Active or passive</label>: ' + 
                     '<input id="active_passive" name="active_passive" size="60" type="text" ' + 
                     ' value="' + instanceData['active_passive'] + '">';
}
function editInstance(instanceIndex) {

  var apiRoute =  '/api' + window.location.pathname +
    '/instances/' + instanceIndex;


  $.get(apiRoute).done(
    (instanceData) => {

      var fig_checked =  instanceData["figurative"] ? 'checked' : '';
      var incl_checked =  instanceData["include"] ? 'checked' : '';

      var filledForm = 
        '<div class="row">Figurative (check for yes)?  <input ' + fig_checked + 
          ' id="figurative" name="figurative" type="checkbox" value="y"></div>' +

        '<div class="row">Include (check for yes)?  <input ' + incl_checked + 
            ' id="include" name="include" type="checkbox" value="y"></div>' +

        '<div class="row"><label for="conceptual_metaphor">Conceptual metaphor</label>: ' +
                         '<input id="conceptual_metaphor" name="conceptual_metaphor" size="60" type="text" ' + 
                         ' value="' + instanceData["conceptual_metaphor"] + '"></div>' + 

        '<div class="row"><label for="spoken_by">Spoken by</label>: ' +
           '<input id="spoken_by" name="spoken_by" size="60" type="text" ' + 
           ' value="' + instanceData["spoken_by"] + '"></div>' +

        '<div class="row"><label for="description">Description</label>: ' +
           '<input id="description" name="description" size="100" type="text" ' + 
           ' value="' + instanceData["description"] + '"></div>' +
          
        '<div class="row"><label for="subjects">Subject(s)</label>: ' +
                         '<input id="subjects" name="subjects" size="60" type="text" ' + 
                         ' value="' + instanceData["subjects"] + '"></div>' +

        '<div class="row"><label for="objects">Object(s)</label>: ' +
                         '<input id="objects" name="objects" size="60" type="text" ' + 
                         ' value="' + instanceData["objects"] + '"></div>' +

        '<div class="row"><label for="tense">Tense</label>: ' + 
           '<input id="tense" name="tense" size="60" type="text" ' + 
           ' value="' + instanceData["tense"] + '"></div>' +

        '<div class="row"><label for="active_passive">Active or passive</label>: ' + 
                         '<input id="active_passive" name="active_passive" size="60" type="text" ' + 
                         ' value="' + instanceData["active_passive"] + '"></div>';

        document.getElementById("details-" + instanceIndex).innerHTML = 

          filledForm + 

          '<a href="#' + (instanceIndex + 1) + 
            '" onclick="freezeSaveUpdates(' 
              + instanceIndex + 
          ')">Save Changes</a>';
    });
}


function freezeSaveUpdates(instanceIndex) {

  var apiRoute =  '/api' + window.location.pathname +
    '/instances/' + instanceIndex;
  var figChecked = $('#figurative').prop('checked');
  var inclChecked = $('#include').prop('checked');
  console.log(figChecked);
  var figurative = figChecked ? 'True' : 'False';
  var include = inclChecked ? 'True' : 'False';

  var updatedData = {
    figurative: figurative,
    include: include,
    spoken_by: $('#spoken_by').val(),
    conceptual_metaphor: $('#conceptual_metaphor').val(),
    objects: $('#objects').val(),
    subjects: $('#subjects').val(),
    tense: $('#tense').val(),
    description: $('#description').val(),
    active_passive: $('#active_passive').val()
  };

  $.post(apiRoute, updatedData, (instanceData) => {

    var figurativeStr = instanceData['figurative'].toString();
    figurativeStr = figurativeStr.charAt(0).toUpperCase() + figurativeStr.slice(1);

    var includeStr = instanceData['include'].toString();
    includeStr = includeStr.charAt(0).toUpperCase() + includeStr.slice(1);
    
    document.getElementById("details-" + instanceIndex).innerHTML = 

      '<p style="font-size:18pt"><b>Figurative? </b>' + figurativeStr +
      '|   <b>Include? </b>' + includeStr + '</p>' +
      '<p><b>Conceptual metaphor: </b>' +  instanceData['conceptual_metaphor'] + '</p>' + 
      '<p><b>Subject(s): </b>' + instanceData['subjects'] + '</p>' + 
      '<p><b>Object(s): </b>' + instanceData['objects'] + '</p>' + 
      '<p><b>Description: </b>' + instanceData['description'] + '</p>' + 
      '<p><b>Tense: </b>' + instanceData['tense'] + '</p>' + 
      '<p><b>Spoken by: </b>' + instanceData['spoken_by'] + '</p>' + 
      '<p><b>Active/Passive: </b>' + instanceData['active_passive'] + '</p>';
  });
}


function makeFilledForm(instanceData) {
  return  
    '<p style="font-size:18pt"><b>Figurative?</b>' + instanceData['figurative'] +
    '|   <b>Include?</b>' + instanceData['include'] + '</p>' +
    '<p><b>Conceptual metaphor:</b>' +  instanceData['conceptual_metaphor'] + '</p>'
    '<p><b>Subject(s):</b>' + instanceData['subjects'] + '</p>'
    '<p><b>Object(s):</b>' + instanceData['objects'] + '</p>'
    '<p><b>Description:</b>' + instanceData['description'] + '</p>'
    '<p><b>Tense:</b>' + instanceData['tense'] + '</p>'
    '<p><b>Spoken by:</b>' + instanceData['spoken_by'] + '</p>'
    '<p><b>Active/Passive:</b>' + instanceData['active_passive'] + '</p>'
}
