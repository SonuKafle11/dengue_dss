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

    function validate() {
        const gender = document.querySelector('input[name="gender"]:checked')?.value;
        const age = parseInt(ageInput?.value);
        const isPregnant = pregnantInput?.checked;

        const symptoms = document.querySelectorAll(
            'input[type="checkbox"]:not(#pregnant):checked'
        );
        errorBox.textContent = "";
        symptomError.textContent = "";
        if (isPregnant && gender !== 'female') {
            errorBox.textContent = "Only females can be pregnant.";
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

    genderInputs.forEach(i => i.addEventListener('change', validate));
    pregnantInput?.addEventListener('change', validate);
    ageInput?.addEventListener('input', validate);

    document.querySelectorAll('input[type="checkbox"]').forEach(cb => {
        cb.addEventListener('change', validate);
    });

    form.addEventListener('submit', function (e) {
        if (!validate()) {
            e.preventDefault();
        }
    });
});