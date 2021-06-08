function polite() {
    document.getElementById("please-wait-div").style.display = "block";
}

const MIN_PRIORITY = 0;
const INIT_PRIORITY = 1;
const MAX_PRIORITY = 5; // TODO choose an appropriate value
var categoryPriorities;

function update_priorities() {
    sessionStorage.setItem("categoryPriorities", JSON.stringify(categoryPriorities));
}

function init_priorities() {
    if (sessionStorage.getItem("categoryPriorities")) {
        categoryPriorities = JSON.parse(sessionStorage.getItem("categoryPriorities"));
        var categoryDivs = document.getElementsByClassName("category-div");
        for (let i = 0; i < categoryDivs.length; i++) {
            const categoryDiv = categoryDivs[i];
            refresh_priority(categoryDiv.id);
        }
        console.log(categoryPriorities);
        return;
    }
    var categoryDivs = document.getElementsByClassName("category-div");
    categoryPriorities = {}
    for (let i = 0; i < categoryDivs.length; i++) {
        const categoryDiv = categoryDivs[i];
        categoryPriorities[categoryDiv.id] = INIT_PRIORITY;
        refresh_num_hidden(categoryDiv);
    }
    update_priorities();
}

function toggleHelp(field_id) {
    var button = document.getElementById(field_id + "-help-button");
    var div = document.getElementById(field_id + "-help-div");
    if (div.style.display === "none") {
        button.innerHTML = "Hide help";
        div.style.display = "inline-block";
    } else {
        button.innerHTML = "Show help";
        div.style.display = "none";
    }
}

function getNumHidden(div) {
    const priority = categoryPriorities[div.id];
    var numHidden = 0;
    fieldDivs = div.getElementsByClassName("field-div");
    for (let i = 0; i < fieldDivs.length; i++) {
        var fieldDiv = fieldDivs[i];
        if (fieldDiv.getAttribute('data-priority-level') > priority) {
            numHidden++;
        }
    }
    return numHidden;
}

function refresh_num_hidden(div, numHidden) {
    const div_id = div.id.slice(0, -4);
    numHiddenText = document.getElementById(div_id + "-num-hidden-text");
    if (numHidden === undefined) {
        var numHidden = getNumHidden(div);
    }
    numTotal = div.getElementsByClassName("field-div").length;
    if (numHidden == numTotal) {
        numHiddenText.innerHTML = "All fields hidden.";
        document.getElementById(div_id + "-more-button").disabled = false;
        document.getElementById(div_id + "-less-button").disabled = true;
    } else if (numHidden > 2) {
        numHiddenText.innerHTML = numHidden + " less-used fields hidden.";
        document.getElementById(div_id + "-more-button").disabled = false;
        document.getElementById(div_id + "-less-button").disabled = false;
    } else if (numHidden == 1) {
        numHiddenText.innerHTML = "1 less-used field hidden.";
        document.getElementById(div_id + "-more-button").disabled = false;
        document.getElementById(div_id + "-less-button").disabled = false;
    } else {
        numHiddenText.innerHTML = "All fields shown.";
        document.getElementById(div_id + "-more-button").disabled = true;
        document.getElementById(div_id + "-less-button").disabled = false;
    }
}

function refresh_priority(div_id) {
    const priority = categoryPriorities[div_id];
    var numHidden = 0;
    div = document.getElementById(div_id);
    fieldDivs = div.getElementsByClassName("field-div");
    for (let i = 0; i < fieldDivs.length; i++) {
        var fieldDiv = fieldDivs[i];
        if (priority == 0 ||
            fieldDiv.getAttribute('data-priority-level') > priority
        ) {
            fieldDiv.style.display = "none";
            numHidden++;
        } else {
            fieldDiv.style.display = "block";
        }
    }
    refresh_num_hidden(div, numHidden);
}

function show_more(div_id) {
    categoryPriorities[div_id] = Math.min(
        categoryPriorities[div_id] + 1, MAX_PRIORITY_DICT[div_id.slice(0, -4)]
    );
    refresh_priority(div_id);
    update_priorities();
}

function show_less(div_id) {
    categoryPriorities[div_id] = Math.max(
        categoryPriorities[div_id] - 1, MIN_PRIORITY
    );
    refresh_priority(div_id);
    update_priorities();
}

var shareableLink;

function getShareableLink() {
    const changedFields = document.getElementsByClassName('changed-field');
    var query = Array.prototype.map.call(changedFields,
        function (field) { return field.id + '=' + field.value; }
    ).join('&');
    var url = window.location.href.split("?")[0];
    return encodeURI(url + "?" + query);
}

function updateShareableLink() {
    shareableLink = getShareableLink();
    document.getElementById('shareable-link').innerHTML = shareableLink;
}

function initShareableLink() {
    document.getElementById('shareable-link').innerHTML = window.location.href;
}

// according to Mozilla docs, `false` boolean (for optional `useCapture` arg) 
// should be included for maximum browser compatability
document.addEventListener('DOMContentLoaded', init_priorities, false);

var SettingInputFields = document.getElementsByClassName("er_setting");

function update_field(field) {
    const container = document.getElementById(field.id + "-div");
    var values_match = (
        field.type == "checkbox"
            ? field.checked == (DEFAULT_FIELD_VALUES[field.id] == "y")
            : field.value == DEFAULT_FIELD_VALUES[field.id]
    );
    if (values_match) {
        container.classList.remove("changed-field-div");
        field.classList.remove("changed-field");
    } else {
        container.classList.add("changed-field-div");
        field.classList.add("changed-field");
    }
}

function init_field_colors() {
    for (let i = 0; i < SettingInputFields.length; i++) {
        var inputField = SettingInputFields[i];
        inputField.addEventListener('change', function (event) { update_field(event.target) });
        inputField.addEventListener('change', updateShareableLink, false);
        update_field(inputField);
    }
}

// function copyLink() {
// doesn't work --- link would have to be an input element
//     var link = document.getElementById('shareable-link');
//     link.select();
//     link.setSelectionRange(0, 99999); /* For mobile devices */
//     document.execCommand("copy");
//     console.log("HI!");
//     alert("Link copied to clipboard");
// }

document.addEventListener('DOMContentLoaded', initShareableLink, false);
document.addEventListener('DOMContentLoaded', init_field_colors, false);
document.addEventListener('DOMContentLoaded', function () {
    document.getElementById('top-submit').addEventListener('click', polite, false);
    document.getElementById('bottom-submit').addEventListener('click', polite, false);
    // document.getElementById('shareable-link').addEventListener('click', copyLink, false);
}, false);



