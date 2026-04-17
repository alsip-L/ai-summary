/* frontend/js/components/result-table.js — 结果表格 */

const ResultTable = {
    display(results) {
        const area = document.getElementById('results-area');
        const tbody = document.querySelector('#results-table tbody');
        if (!area || !tbody) return;

        tbody.innerHTML = '';
        results.forEach(result => {
            const row = document.createElement('tr');

            // 源文件列
            const srcCell = document.createElement('td');
            srcCell.textContent = result.source ? result.source.split(/[/\\]/).pop() : '';
            srcCell.style.wordBreak = 'break-all';
            srcCell.style.maxWidth = '300px';
            srcCell.style.overflow = 'hidden';
            srcCell.style.textOverflow = 'ellipsis';
            srcCell.style.whiteSpace = 'nowrap';
            row.appendChild(srcCell);

            // 结果文件列
            const outCell = document.createElement('td');
            if (result.output) {
                const fileName = result.output.split(/[/\\]/).pop();
                const link = document.createElement('a');
                link.href = '#';
                link.textContent = fileName;
                link.style.textDecoration = 'none';
                link.style.color = '#007bff';
                link.style.wordBreak = 'break-all';
                link.addEventListener('click', (e) => {
                    e.preventDefault();
                    ResultTable.viewFile(result.output);
                });
                outCell.appendChild(link);
            } else {
                outCell.textContent = '处理失败';
                outCell.style.color = '#dc3545';
            }
            outCell.style.wordBreak = 'break-all';
            outCell.style.maxWidth = '400px';
            outCell.style.overflow = 'hidden';
            outCell.style.textOverflow = 'ellipsis';
            outCell.style.whiteSpace = 'nowrap';
            row.appendChild(outCell);

            tbody.appendChild(row);
        });

        if (area.style.display !== 'block') {
            area.style.display = 'block';
            area.classList.add('visible');
        }
    },

    async viewFile(filePath) {
        try {
            const data = await API.viewResult(filePath);
            if (data.success) {
                const overlay = document.createElement('div');
                overlay.style.cssText = 'position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.5);z-index:10000;display:flex;justify-content:center;align-items:center;';

                const dialog = document.createElement('div');
                dialog.style.cssText = 'background:white;padding:20px;border-radius:8px;width:80%;max-width:800px;max-height:80vh;display:flex;flex-direction:column;';
                dialog.innerHTML = `
                    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:15px;">
                        <h3 style="margin:0;">${Utils.escapeHtml(data.file_name)}</h3>
                        <button id="close_result_view" style="padding:5px 10px;cursor:pointer;border:none;background:#ccc;border-radius:4px;">关闭</button>
                    </div>
                    <div style="flex:1;overflow:auto;">
                        <pre style="white-space:pre-wrap;word-break:break-word;margin:0;padding:10px;background:#f5f5f5;border-radius:4px;font-size:13px;line-height:1.6;">${Utils.escapeHtml(data.content)}</pre>
                    </div>
                `;

                overlay.appendChild(dialog);
                document.body.appendChild(overlay);
                document.getElementById('close_result_view').onclick = () => overlay.remove();
                overlay.onclick = (e) => { if (e.target === overlay) overlay.remove(); };
            } else {
                alert('查看失败: ' + (data.error || '未知错误'));
            }
        } catch (e) {
            alert('查看失败: ' + e.message);
        }
    }
};

window.ResultTable = ResultTable;
