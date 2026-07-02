document.addEventListener('DOMContentLoaded', function () {
    const messages = document.querySelectorAll('.message');
    messages.forEach(msg => setTimeout(() => msg.style.display = 'none', 3000));
});

document.addEventListener('DOMContentLoaded', function () {
    const form = document.querySelector('form');
    if (!form) return;

    const genderInputs  = document.querySelectorAll('input[name="gender"]');
    const ageInput      = document.getElementById('age');
    const heightInput   = document.getElementById('height');
    const pregnantInput = document.getElementById('pregnant');
    const errorBox      = document.getElementById('error-msg');
    const symptomError  = document.getElementById('symptom-error');

    const isPatientForm = ageInput && genderInputs.length > 0;
    if (!isPatientForm) return;

    function updatePregnantAvailability() {
        const sel = document.querySelector('input[name="gender"]:checked');
        const gender = sel?.value?.trim().toLowerCase();
        const ageVal = ageInput?.value?.trim();
        const age = ageVal !== '' ? parseInt(ageVal) : null;

        const shouldDisable = gender === 'male' || (age !== null && age < 10);

        if (pregnantInput) {
            pregnantInput.disabled = shouldDisable;
            if (shouldDisable) {
                pregnantInput.checked = false;
                if (errorBox) errorBox.textContent = "";
            }
            const lbl = pregnantInput.closest('label');
            if (lbl) {
                lbl.style.opacity = shouldDisable ? '0.4' : '1';
                lbl.style.cursor  = shouldDisable ? 'not-allowed' : 'pointer';
            }
        }
    }

    function validate() {
        const sel = document.querySelector('input[name="gender"]:checked');
        const gender = sel?.value?.trim().toLowerCase();
        const ageVal = ageInput?.value?.trim();
        const age    = ageVal !== '' ? parseInt(ageVal) : null;
        const hVal   = heightInput?.value?.trim();
        const height = hVal !== '' && hVal != null ? parseFloat(hVal) : null;
        const isPregnant = pregnantInput?.checked;
        const symptoms = document.querySelectorAll('input[type="checkbox"]:not(#pregnant):checked');

        if (errorBox)     errorBox.textContent = "";
        if (symptomError) symptomError.textContent = "";

        if (!gender) { if (errorBox) errorBox.textContent = "Please select a gender."; return false; }
        if (age === null || isNaN(age)) { if (errorBox) errorBox.textContent = "Please enter your age."; return false; }
        if (heightInput && (height === null || isNaN(height) || height <= 0)) {
            if (errorBox) errorBox.textContent = "Please enter a valid height in cm.";
            return false;
        }
        if (isPregnant && gender === 'male') { if (errorBox) errorBox.textContent = "Males cannot be pregnant."; return false; }
        if (isPregnant && age < 10) { if (errorBox) errorBox.textContent = "Pregnancy not valid for age below 10."; return false; }
        if (symptoms.length === 0) { if (symptomError) symptomError.textContent = "Please select at least one symptom."; return false; }
        return true;
    }

    genderInputs.forEach(i => i.addEventListener('change', updatePregnantAvailability));
    ageInput?.addEventListener('input', updatePregnantAvailability);
    pregnantInput?.addEventListener('change', validate);
    document.querySelectorAll('input[type="checkbox"]').forEach(cb => cb.addEventListener('change', validate));
    form.addEventListener('submit', e => { if (!validate()) e.preventDefault(); });

    updatePregnantAvailability();
});


/* ============================================================
   Public Symptom Form — pregnant checkbox disable/enable
   based on gender selection
   ============================================================ */
document.addEventListener('DOMContentLoaded', function () {
    // Only run on the public check form (no height/weight fields)
    var genderRadios   = document.querySelectorAll('input[name="gender"]');
    var pregnantCb     = document.querySelector('input[name="pregnant"]');

    // If either element is missing this isn't the right page
    if (!genderRadios.length || !pregnantCb) return;

    // Only run on the PUBLIC form — patient form has #age and #height ids,
    // public form does not use those same ids
    var isPublicForm = !document.getElementById('height');
    if (!isPublicForm) return;

    function syncPregnant() {
        var selected = document.querySelector('input[name="gender"]:checked');
        var gender   = selected ? selected.value.toLowerCase() : '';
        var disable  = (gender === 'male' || gender === 'other');

        pregnantCb.disabled = disable;
        if (disable) {
            pregnantCb.checked = false;
        }

        // Visual feedback on the label wrapper
        var label = pregnantCb.closest('label');
        if (label) {
            label.style.opacity    = disable ? '0.4' : '1';
            label.style.cursor     = disable ? 'not-allowed' : 'pointer';
            label.title            = disable ? 'Only available when sex is set to Female' : '';
        }
    }

    genderRadios.forEach(function (radio) {
        radio.addEventListener('change', syncPregnant);
    });

    // Run once on load in case a value is already selected (e.g. form re-render)
    syncPregnant();
});
