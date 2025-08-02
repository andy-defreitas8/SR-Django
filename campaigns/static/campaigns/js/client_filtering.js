document.addEventListener('DOMContentLoaded', function () {
    const clientSelect = document.querySelector('#id_client');
    if (!clientSelect) return;

    clientSelect.addEventListener('change', function () {
        const clientId = this.value;
        if (!clientId) return;

        const url = new URL(window.location.href);
        url.searchParams.set('client_id', clientId);
        window.location.href = url.toString(); // reload with ?client_id=
    });
});
