document.addEventListener('DOMContentLoaded', function () {
    const messages = document.querySelectorAll('.message');

    messages.forEach(function (msg) {
        setTimeout(function () {
            msg.style.display = 'none';
        }, 3000);
    });
});

document.addEventListener('DOMContentLoaded', function () {

    const form = document.querySelector('form');
    if (!form) return;

    const genderInputs = document.querySelectorAll('input[name="gender"]');
    const ageInput = document.getElementById('age');
    const pregnantInput = document.getElementById('pregnant');
    const errorBox = document.getElementById('error-msg');
    const symptomError = document.getElementById('symptom-error');

    function updatePregnantAvailability() {
        const selectedGender = document.querySelector('input[name="gender"]:checked');
        const gender = selectedGender?.value?.trim().toLowerCase();
        const ageValue = ageInput?.value?.trim();
        const age = ageValue !== '' ? parseInt(ageValue) : null;

        // Disable ONLY if gender is male OR age is entered and < 10
        // If gender not selected yet or age not entered yet → keep enabled
        const isMale = gender === 'male';
        const isTooYoung = age !== null && age < 10;

        const shouldDisable = isMale || isTooYoung;

        if (pregnantInput) {
            pregnantInput.disabled = shouldDisable;

            if (shouldDisable) {
                pregnantInput.checked = false;
                errorBox.textContent = "";
            }

            const pregnantLabel = pregnantInput.closest('label') ||
                                  document.querySelector('label[for="pregnant"]');
            if (pregnantLabel) {
                pregnantLabel.style.opacity = shouldDisable ? '0.4' : '1';
                pregnantLabel.style.cursor = shouldDisable ? 'not-allowed' : 'pointer';
            }
        }
    }

    function validate() {
        const selectedGender = document.querySelector('input[name="gender"]:checked');
        const gender = selectedGender?.value?.trim().toLowerCase();
        const ageValue = ageInput?.value?.trim();
        const age = ageValue !== '' ? parseInt(ageValue) : null;
        const isPregnant = pregnantInput?.checked;

        const symptoms = document.querySelectorAll(
            'input[type="checkbox"]:not(#pregnant):checked'
        );

        errorBox.textContent = "";
        symptomError.textContent = "";

        // Required fields check
        if (!gender) {
            errorBox.textContent = "Please select a gender.";
            return false;
        }

        if (age === null || isNaN(age)) {
            errorBox.textContent = "Please enter your age.";
            return false;
        }

        // Backup guards
        if (isPregnant && gender === 'male') {
            errorBox.textContent = "Males cannot be pregnant.";
            return false;
        }

        if (isPregnant && age < 10) {
            errorBox.textContent = "Pregnancy not valid for age below 10.";
            return false;
        }

        if (symptoms.length === 0) {
            symptomError.textContent = "Please select at least one symptom.";
            return false;
        }

        return true;
    }

    genderInputs.forEach(i => i.addEventListener('change', () => {
        updatePregnantAvailability();
    }));

    ageInput?.addEventListener('input', () => {
        updatePregnantAvailability();
    });

    pregnantInput?.addEventListener('change', validate);

    document.querySelectorAll('input[type="checkbox"]').forEach(cb => {
        cb.addEventListener('change', validate);
    });

    form.addEventListener('submit', function (e) {
        if (!validate()) {
            e.preventDefault();
        }
    });

    updatePregnantAvailability();
});