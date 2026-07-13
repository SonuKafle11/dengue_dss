document.addEventListener('DOMContentLoaded', function () {
    const messages = document.querySelectorAll('.message');
    messages.forEach(msg => setTimeout(() => msg.style.display = 'none', 3000));
});

document.addEventListener('DOMContentLoaded', function () {
    const form = document.querySelector('form');
    if (!form) return;

    const genderInputs  = document.querySelectorAll('input[name="gender"]');
    const ageInput      = document.getElementById('pc_age');
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

        const shouldDisable = gender !== 'female' || (age === null || age < 13 || age > 55);

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
        const isPregnant = pregnantInput?.checked;
        const symptoms = document.querySelectorAll('input[type="checkbox"]:not(#pregnant):checked');

        if (errorBox)     errorBox.textContent = "";
        if (symptomError) symptomError.textContent = "";

        if (!gender) { if (errorBox) errorBox.textContent = "Please select a gender."; return false; }
        if (age === null || isNaN(age)) { if (errorBox) errorBox.textContent = "Please enter your age."; return false; }
        if (isPregnant && gender === 'male') { if (errorBox) errorBox.textContent = "Males cannot be pregnant."; return false; }
        if (isPregnant && (age < 13 || age > 55)) {
    if (errorBox) {
        errorBox.textContent =
            "Pregnancy is only allowed for females aged 13 to 55 years.";
    }
    return false;
}
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


/* 
   Public Symptom Form — pregnant checkbox disable/enable
   based on gender selection
 */
document.addEventListener('DOMContentLoaded', function () {
    // Only run on the public check form (no height/weight fields)
    var genderRadios   = document.querySelectorAll('input[name="gender"]');
    var pregnantCb     = document.querySelector('input[name="pregnant"]');

    // If either element is missing this isn't the right page
    if (!genderRadios.length || !pregnantCb) return;

    // Only run on the PUBLIC form — patient form has #age and #height ids,
    // public form does not use those same ids
    
    if (!isPublicForm) return;

    function syncPregnant() {
        var selected = document.querySelector('input[name="gender"]:checked');
        var gender   = selected ? selected.value.toLowerCase() : '';
        

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


window.addEventListener('pageshow', function (event) {
    var isProtected = document.body && document.body.dataset.authRequired === '1';
    if (!isProtected) return;

    if (event.persisted) {
        window.location.reload();
    }
});


/* 
   Patient Profile — uncheck "Currently pregnant" when
   Male radio button is selected
 */
document.addEventListener('DOMContentLoaded', function () {

    var pregnantCb = document.querySelector('input[name="is_pregnant"]');
    var genderRadios = document.querySelectorAll('input[name="gender"]');
    var ageInput = document.querySelector('input[name="age"]');

    if (!pregnantCb || !genderRadios.length || !ageInput) return;

    function syncProfilePregnant() {

        var selected = document.querySelector('input[name="gender"]:checked');
        var gender = selected ? selected.value.toLowerCase() : '';

        var age = ageInput.value !== ''
            ? parseInt(ageInput.value)
            : null;

        var shouldDisable =
            (
                (gender !== 'female' && gender !== 'other')
                ||
                age === null
                ||
                age < 13
                ||
                age > 55
            );

        pregnantCb.disabled = shouldDisable;

        if (shouldDisable) {
            pregnantCb.checked = false;
        }

        var label = pregnantCb.closest('label');

        if (label) {
            label.style.opacity = shouldDisable ? '0.4' : '1';
            label.style.cursor = shouldDisable ? 'not-allowed' : 'pointer';
        }
    }

    genderRadios.forEach(function (radio) {
        radio.addEventListener('change', syncProfilePregnant);
    });

    ageInput.addEventListener('input', syncProfilePregnant);

    syncProfilePregnant();
});

/* 
   Admin Dashboard — AJAX delete (no page reload, no messages
   leaking to the login page)
 */
document.addEventListener('DOMContentLoaded', function () {

    function getCsrfToken() {
        var cookie = document.cookie.split(';').find(function (c) {
            return c.trim().startsWith('csrftoken=');
        });
        return cookie ? cookie.trim().split('=')[1] : '';
    }

    function ajaxDelete(url, row) {
        fetch(url, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCsrfToken(),
                'X-Requested-With': 'XMLHttpRequest',
            },
        })
        .then(function (res) { return res.json(); })
        .then(function (data) {
            if (data.ok) {
                row.style.transition = 'opacity 0.25s';
                row.style.opacity    = '0';
                setTimeout(function () { row.remove(); }, 260);
            } else {
                alert(data.error || 'Delete failed.');
            }
        })
        .catch(function () {
            alert('Network error. Please try again.');
        });
    }

    // User delete buttons
    document.querySelectorAll('.btn-delete-user').forEach(function (btn) {
        btn.addEventListener('click', function () {
            var name = btn.dataset.name || 'this user';
            if (!confirm('Delete ' + name + '?')) return;
            var row = btn.closest('tr');
            ajaxDelete(btn.dataset.url, row);
        });
    });

    // Record delete buttons
    document.querySelectorAll('.btn-delete-record').forEach(function (btn) {
        btn.addEventListener('click', function () {
            if (!confirm('Delete this record?')) return;
            var row = btn.closest('tr');
            ajaxDelete(btn.dataset.url, row);
        });
    });

});


/* 
   Hamburger nav toggle
   Runs on: landing, about, explore, public_symptom_form,
            public_symptom_result (standalone pages)
*/
document.addEventListener('DOMContentLoaded', function () {
    var toggle = document.getElementById('navToggle');
    var links  = document.getElementById('navLinks');
    if (!toggle || !links) return;

    toggle.addEventListener('click', function () {
        var isOpen = links.classList.toggle('open');
        toggle.classList.toggle('open', isOpen);
        toggle.setAttribute('aria-expanded', isOpen);
    });

    links.querySelectorAll('a').forEach(function (a) {
        a.addEventListener('click', function () {
            links.classList.remove('open');
            toggle.classList.remove('open');
            toggle.setAttribute('aria-expanded', 'false');
        });
    });
});

/*
   Public symptom form — pregnant checkbox sync
   Only runs when input[name="pregnant"] exists (not is_pregnant)
*/
document.addEventListener('DOMContentLoaded', function () {
    var radios     = document.querySelectorAll('input[name="gender"]');
    var pregnantCb = document.querySelector('input[name="pregnant"]');
    if (!radios.length || !pregnantCb) return;

    var label = pregnantCb.closest('label');

    function sync() {
    var sel = document.querySelector('input[name="gender"]:checked');
    var gender = sel ? sel.value.toLowerCase() : '';

    var ageInput = document.getElementById('pc_age');
    var age = ageInput && ageInput.value !== ''
        ? parseInt(ageInput.value)
        : null;

    // Disable unless Female AND age is between 13 and 55
    var disable = (
        gender !== 'female' && gender !=='other' ||
        age === null ||
        age < 13 ||
        age > 55
    );

    pregnantCb.disabled = disable;

    if (disable) {
        pregnantCb.checked = false;
    }
        
        if (label) {
            label.style.opacity = disable ? '0.4' : '1';
            label.style.cursor  = disable ? 'not-allowed' : 'pointer';
        }
    }

    radios.forEach(function (r) { r.addEventListener('change', sync); });
    var ageInput = document.getElementById('pc_age');
if (ageInput) {
    ageInput.addEventListener('input', sync);
}
    sync();
});

/*
   Public symptom form — require at least one symptom
*/
document.addEventListener('DOMContentLoaded', function () {
    var checkForm = document.getElementById('checkForm');
    if (!checkForm) return;

    checkForm.addEventListener('submit', function (e) {
        var checked = checkForm.querySelectorAll('input[type="checkbox"]:checked');
        var err     = document.getElementById('sym-error');
        if (checked.length === 0) {
            e.preventDefault();
            if (err) err.textContent = 'Please select at least one symptom before submitting.';
        } else {
            if (err) err.textContent = '';
        }
    });
});

/*
   Patient assessment form — pregnant checkbox sync
   Scoped to pages that have .symptom-grid (patient_form only)
*/
document.addEventListener('DOMContentLoaded', function () {
    var symptomGrid = document.querySelector('.symptom-grid');
    var pregnantCb  = document.querySelector('input[name="is_pregnant"]');
    var radios      = document.querySelectorAll('input[name="gender"]');
    var ageInput    = document.getElementById('age');

    if (!symptomGrid || !pregnantCb || !radios.length || !ageInput) return;

    var label = pregnantCb.closest('label');

    function sync() {
        var selected = document.querySelector('input[name="gender"]:checked');
        var gender = selected ? selected.value.toLowerCase() : '';

        var age = ageInput.value !== ''
            ? parseInt(ageInput.value)
            : null;

        var disable =
            gender !== 'female' &&gender !== 'other' ||
            age === null ||
            age < 13 ||
            age > 55;

        pregnantCb.disabled = disable;

        if (disable) {
            pregnantCb.checked = false;
        }

        if (label) {
            label.style.opacity = disable ? '0.4' : '1';
            label.style.cursor = disable ? 'not-allowed' : 'pointer';
        }
    }

    radios.forEach(function (r) {
        r.addEventListener('change', sync);
    });

    ageInput.addEventListener('input', sync);

    sync();
});
/*
   Doctor dashboard — status dropdown auto-submit
*/
document.addEventListener('DOMContentLoaded', function () {
    var statusSelect = document.getElementById('statusSelect');
    var filterForm   = document.getElementById('filterForm');
    if (!statusSelect || !filterForm) return;
    statusSelect.addEventListener('change', function () {
        filterForm.submit();
    });
});

/*
   Login page — account-created modal
 */
document.addEventListener('DOMContentLoaded', function () {
    var modal = document.getElementById('acctModal');
    var btn   = document.getElementById('acctOk');
    if (!modal) return;
    modal.classList.add('open');
    if (btn) {
        btn.addEventListener('click', function () { modal.classList.remove('open'); });
    }
    modal.addEventListener('click', function (e) {
        if (e.target === modal) modal.classList.remove('open');
    });
});
