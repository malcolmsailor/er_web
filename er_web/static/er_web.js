const MIN_PRIORITY = 0;
const INIT_PRIORITY = 1;
const MAX_PRIORITY = 5; // TODO choose an appropriate value
var categoryPriorities = {};

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
}

function show_less(div_id) {
    categoryPriorities[div_id] = Math.max(
        categoryPriorities[div_id] - 1, MIN_PRIORITY
    );
    refresh_priority(div_id);
}

function init_priorities() {
    var categoryDivs = document.getElementsByClassName("category-div");
    for (let i = 0; i < categoryDivs.length; i++) {
        const categoryDiv = categoryDivs[i];
        categoryPriorities[categoryDiv.id] = INIT_PRIORITY;
        refresh_num_hidden(categoryDiv);
    }
}

// according to Mozilla docs, `false` boolean (for optional `useCapture` arg) 
// should be included for maximum browser compatability
document.addEventListener('DOMContentLoaded', init_priorities, false);