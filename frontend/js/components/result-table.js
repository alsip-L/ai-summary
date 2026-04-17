/* result-table.js — Result table */

const ResultTable = {
    display(results) {
        const area = document.getElementById('results-area');
        const tbody = document.querySelector('#results-table tbody');
        const countEl = document.getElementById('results-count');
        if (!area || !tbody) return;

        tbody.innerHTML = '';
        results.forEach(result => {
            const row = document.createElement('tr');

            const srcCell = document.createElement('td');
            srcCell.textContent = result.source ? result.source.split(/[/\\]/).pop() : '';
            row.appendChild(srcCell);

            const outCell = document.createElement('td');
            if (result.output) {
                const fileName = result.output.split(/[/\\]/).pop();
                const link = document.createElement('a');
                link.href = '#';
                link.textContent = fileName;
                link.addEventListener('click', (e) => {
                    e.preventDefault();
                    ResultTable.viewFile(result.output);
                });
                outCell.appendChild(link);
            } else {
                outCell.textContent = '失败';
                outCell.style.color = 'var(--danger)';
            }
            row.appendChild(outCell);
            tbody.appendChild(row);
        });

        if (countEl) countEl.textContent = results.length;

        area.classList.remove('hidden');
        area.classList.add('visible');
    },

    async viewFile(filePath) {
        try {
            const data = await API.viewResult(filePath);
            if (data.success) {
                const overlay = document.createElement('div');
                overlay.className = 'modal-overlay';
                const dialog = document.createElement('div');
                dialog.className = 'modal-content';
                dialog.style.maxWidth = '720px';
                dialog.innerHTML = `
                    <div class="modal-header">
                        <h3>${Utils.escapeHtml(data.file_name)}</h3>
                        <button class="modal-close-btn" id="close_result_view">&times;</button>
                    </div>
                    <div class="modal-body">
                        <pre style="white-space: pre-wrap; word-break: break-word; margin: 0; padding: var(--space-3); background: var(--bg-canvas); border-radius: var(--radius-sm); font-size: var(--text-xs); line-height: 1.7; font-family: var(--font-mono); color: var(--text-secondary); border: 1px solid var(--border);">${Utils.escapeHtml(data.content)}</pre>
                    </div>
                `;
                overlay.appendChild(dialog);
                document.body.appendChild(overlay);
                document.getElementById('close_result_view').onclick = () => overlay.remove();
                overlay.onclick = (e) => { if (e.target === overlay) overlay.remove(); };
            } else {
                showMessage('查看失败: ' + (data.error || '未知错误'), 'error');
            }
        } catch (e) {
            showMessage('查看失败: ' + e.message, 'error');
        }
    }
};

window.ResultTable = ResultTable;
