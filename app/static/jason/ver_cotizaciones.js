const rowsPerPage = 10;
const table = document.getElementById('tabla-cotizaciones').getElementsByTagName('tbody')[0];
const pagination = document.getElementById('pagination');
let currentPage = 1;

function renderTable() {
    const rows = [...table.querySelectorAll('tr')];
    const totalPages = Math.ceil(rows.length / rowsPerPage);

    rows.forEach((row, index) => {
        row.style.display = (index >= (currentPage - 1) * rowsPerPage && index < currentPage * rowsPerPage) ? '' : 'none';
    });

    pagination.innerHTML = '';
    for (let i = 1; i <= totalPages; i++) {
        const btn = document.createElement('button');
        btn.textContent = i;
        btn.className = (i === currentPage) ? 'active' : '';
        btn.addEventListener('click', () => {
            currentPage = i;
            renderTable();
        });
        pagination.appendChild(btn);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    renderTable();

    document.getElementById('busqueda').addEventListener('input', e => {
        const query = e.target.value.toLowerCase();
        [...table.rows].forEach(row => {
            row.style.display = row.dataset.cliente.toLowerCase().includes(query) ? '' : 'none';
        });
    });

    document.getElementById('filtro-validez').addEventListener('change', e => {
        const filtro = e.target.value;
        const hoy = new Date().toISOString().split('T')[0];
        [...table.rows].forEach(row => {
            const validez = row.dataset.validez;
            if (filtro === "vigente") {
                row.style.display = validez >= hoy ? '' : 'none';
            } else if (filtro === "vencidas") {
                row.style.display = validez < hoy ? '' : 'none';
            } else {
                row.style.display = '';
            }
        });
    });

    document.getElementById('filtro-estado').addEventListener('change', e => {
        const estado = e.target.value;
        [...table.rows].forEach(row => {
            row.style.display = estado ? row.dataset.estado === estado : '';
        });
    });
});
    