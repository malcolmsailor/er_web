function polite() {
    document.getElementById("please-wait-div").style.display = "block";
}

const MIN_PRIORITY = 0;
const INIT_PRIORITY = 1;
const MAX_PRIORITY = 5; // TODO choose an appropriate value
var categoryPriorities;
var x;
var y;

function getCoords(event) {
    x = event.clientX;
    y = event.clientY;
}

function updatePriorities() {
    sessionStorage.setItem("categoryPriorities", JSON.stringify(categoryPriorities));
}

function initPriorities() {
    if (sessionStorage.getItem("categoryPriorities")) {
        categoryPriorities = JSON.parse(sessionStorage.getItem("categoryPriorities"));
        var categoryDivs = document.getElementsByClassName("category-div");
        for (let i = 0; i < categoryDivs.length; i++) {
            const categoryDiv = categoryDivs[i];
            refreshPriority(categoryDiv.id);
        }
        return;
    }
    var categoryDivs = document.getElementsByClassName("category-div");
    categoryPriorities = {}
    for (let i = 0; i < categoryDivs.length; i++) {
        const categoryDiv = categoryDivs[i];
        categoryPriorities[categoryDiv.id] = INIT_PRIORITY;
        refreshNumHidden(categoryDiv);
    }
    updatePriorities();
}

function toggleHelp(fieldId) {
    var button = document.getElementById(fieldId + "-help-button");
    var div = document.getElementById(fieldId + "-help-div");
    if (div.style.display === "none") {
        button.innerHTML = button.innerHTML.replace("show", "hide").replace("?", "⨯");
        div.style.display = "block";
    } else {
        button.innerHTML = button.innerHTML.replace("hide", "show").replace("⨯", "?");
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

function refreshNumHidden(div, numHidden) {
    // remove "-cat-div" from end of container id
    const id = div.id.slice(0, -8);
    numHiddenText = document.getElementById(id + "-num-hidden-text");
    if (numHidden === undefined) {
        var numHidden = getNumHidden(div);
    }
    numTotal = div.getElementsByClassName("field-div").length;
    if (numHidden == numTotal) {
        numHiddenText.innerHTML = "All fields hidden.";
        document.getElementById(id + "-more-button").disabled = false;
        document.getElementById(id + "-less-button").disabled = true;
    } else if (numHidden > 1) {
        numHiddenText.innerHTML = numHidden + " less-used fields hidden.";
        document.getElementById(id + "-more-button").disabled = false;
        document.getElementById(id + "-less-button").disabled = false;
    } else if (numHidden == 1) {
        numHiddenText.innerHTML = "1 less-used field hidden.";
        document.getElementById(id + "-more-button").disabled = false;
        document.getElementById(id + "-less-button").disabled = false;
    } else {
        numHiddenText.innerHTML = "All fields shown.";
        document.getElementById(id + "-more-button").disabled = true;
        document.getElementById(id + "-less-button").disabled = false;
    }
}

function refreshPriority(divId) {
    const priority = categoryPriorities[divId];
    var numHidden = 0;
    div = document.getElementById(divId);
    fieldDivs = div.getElementsByClassName("field-div");
    for (let i = 0; i < fieldDivs.length; i++) {
        var fieldDiv = fieldDivs[i];
        if ((priority == 0 ||
            fieldDiv.getAttribute('data-priority-level') > priority
        ) && !fieldDiv.classList.contains('has-error')
        ) {
            fieldDiv.style.display = "none";
            numHidden++;
        } else {
            fieldDiv.style.display = "block";
        }
    }
    refreshNumHidden(div, numHidden);
}

function showMore(divId) {
    categoryPriorities[divId] = Math.min(
        categoryPriorities[divId] + 1, MAX_PRIORITY_DICT[divId.slice(0, -8)]
    );
    refreshPriority(divId);
    updatePriorities();
}

function showLess(divId) {
    categoryPriorities[divId] = Math.max(
        categoryPriorities[divId] - 1, MIN_PRIORITY
    );
    refreshPriority(divId);
    updatePriorities();
}

var shareableLink;

function getShareableLink() {
    const changedFields = document.getElementsByClassName('changed-field');
    var query = Array.prototype.map.call(changedFields,
        function (field) { return field.id + '=' + field.value; }
    ).join('&');
    var url = window.location.href.split("?")[0];
    var url = url.split("#")[0];
    return encodeURI(url + "?" + query);
}

function updateShareableLink() {
    shareableLink = getShareableLink();
    document.getElementById('shareable-link').innerHTML = shareableLink;
}

function initTraceback() {
    var tracebackLink = document.getElementById("traceback-mail");
    if (tracebackLink) {
        tracebackLink.href = tracebackLink + "%0A%0A" + shareableLink.replace("&", "%26");
    }
}



var SettingInputFields = document.getElementsByClassName("er_setting");

function updateField(field) {
    const container = document.getElementById(field.id + "-div");
    var valuesMatch = (
        field.type == "checkbox"
            ? field.checked == (DEFAULT_FIELD_VALUES[field.id] == "y")
            : field.value == DEFAULT_FIELD_VALUES[field.id]
    );
    if (valuesMatch) {
        container.classList.remove("changed-field-div");
        field.classList.remove("changed-field");
    } else {
        container.classList.add("changed-field-div");
        field.classList.add("changed-field");
    }
}

function adjustFieldContext(field, visibility) {
    var typingString = document.getElementById(field.id + "-typing-string");
    if (typingString) {
        typingString.style.visibility = visibility;
    }
    var constantsDiv = document.getElementById(field.id + "-constants-div");
    if (constantsDiv) {
        constantsDiv.style.visibility = visibility;
    }
}

function showFieldContext(field) {
    adjustFieldContext(field, "visible");
}

function hideFieldContext(event) {
    var clickedElement = document.elementFromPoint(x, y);
    var field = event.target;
    var constantsDiv = document.getElementById(field.id + "-constants-div");
    // TODO debug why the check for visibility here is not working
    if (constantsDiv && constantsDiv.contains(clickedElement) && constantsDiv.style.visibility == "visible") {
        field.focus();
    } else {
        adjustFieldContext(field, "hidden");
    }
}

function addConstant(constantName, fieldId) {
    var field = document.getElementById(fieldId);
    // TODO handle commas more carefully
    field.value += (field.value ? ", " : "") + constantName;
}

function initFieldColors() {
    for (let i = 0; i < SettingInputFields.length; i++) {
        var inputField = SettingInputFields[i];
        inputField.addEventListener('change', function (event) { updateField(event.target) });
        inputField.addEventListener('change', updateShareableLink, false);
        updateField(inputField);
        if (inputField.type === "text") {
            inputField.addEventListener(
                'focus', function (event) { showFieldContext(event.target); }, false
            );
            inputField.addEventListener(
                'blur', function (event) { hideFieldContext(event); }, false
            );
        }
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

function revealShareableLink() {
    var link = document.getElementById("shareable-link");
    var button = document.getElementById("show-shareable-link");
    if (link.style.display === "none") {
        link.style.display = "inline-block";
        button.innerHTML = button.innerHTML.replace("Show", "Hide");
    } else {
        link.style.display = "none";
        button.innerHTML = button.innerHTML.replace("Hide", "Show");
    }

}

function clearQueryFromUrl() {
    // executed on page load, clears any query string from the url
    window.history.replaceState(
        null,
        document.title,
        location.protocol + "//" + location.host + location.pathname
    );
}

function revealLinkedField(linkDiv) {
    var targetDiv = document.getElementById(linkDiv.href.split("#")[1]);
    targetDiv.style.display = "block";
}

function initHelpLinks() {
    const helpLinks = document.getElementsByClassName('help-field-a');
    for (let i = 0; i < helpLinks.length; i++) {
        helpLinks[i].addEventListener('click', function (event) { revealLinkedField(event.target) }, false);
    }
}



function initPage() {
    document.addEventListener('mousedown', getCoords, false);
    initPriorities();
    initFieldColors();
    updateShareableLink();
    document.getElementById('top-submit').addEventListener('click', polite, false);
    document.getElementById('bottom-submit').addEventListener('click', polite, false);
    document.getElementById('show-shareable-link').addEventListener('click', revealShareableLink, false);
    initTraceback();
    clearQueryFromUrl();
    initHelpLinks();
}

// according to Mozilla docs, `false` boolean (for optional `useCapture` arg) 
// should be included for maximum browser compatability
document.addEventListener('DOMContentLoaded', initPage, false);
