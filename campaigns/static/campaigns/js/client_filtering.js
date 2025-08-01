document.addEventListener('DOMContentLoaded', function () {
    console.log("📦 Client filter script loaded!");
    const clientSelect = document.querySelector('#id_client');


    if (clientSelect) {
        console.log("Client dropdown found");

        clientSelect.addEventListener('change', function () {
        const clientId = this.value;

        fetch(`/admin/campaigns/get-options/?client_id=${clientId}`)
            .then(response => response.json())
            .then(data => {
                const updateSelect = (selectorPrefix, fieldName, items, labelField) => {
                    const selects = document.querySelectorAll(`select[id^="${selectorPrefix}"][id$="${fieldName}"]`);
                    selects.forEach(select => {
                        select.innerHTML = '<option value="">---------</option>';
                        items.forEach(item => {
                            const option = document.createElement('option');
                            option.value = item.ga_product_id;
                            option.textContent = item.item_name;
                            select.appendChild(option);
                        });
                    });
                };

                updateSelect('id_product_mapping_set-', 'ga_product', data.products, 'item_name');
                updateSelect('id_page_mapping_set-', 'ga_page', data.pages, 'url');
            });
    });
    } else {
        console.warn("Client dropdown not found.");
    }
});
