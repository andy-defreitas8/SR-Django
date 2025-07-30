
document.addEventListener('DOMContentLoaded', function () {
    const clientField = document.querySelector('#id_client');
    if (clientField) {
        clientField.addEventListener('change', function () {
            this.form.submit(); 
        });
    }
});
