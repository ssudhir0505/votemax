function syntaxHighlight(json) {
    if (typeof json != 'string') {
        json = JSON.stringify(json, undefined, 4);
    }
    json = json.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    return json.replace(/("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+-]?\d+)?)/g, function (match) {
        var cls = 'json-number';
        if (/^"/.test(match)) {
            if (/:$/.test(match)) {
                cls = 'json-key';
            } else {
                cls = 'json-string';
            }
        } else if (/true|false/.test(match)) {
            cls = 'json-boolean';
        } else if (/null/.test(match)) {
            cls = 'json-null';
        }
        return '<span class="' + cls + '">' + match + '</span>';
    });
}

function forceMine() {
    const btn = document.getElementById('mine-btn');
    btn.innerText = 'Mining...';
    btn.disabled = true;

    fetch('/api/mine', { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            alert(data.message);
            refreshChain();
            btn.innerText = 'Manual Override: Mine Block';
            btn.disabled = false;
        });
}

function refreshChain() {
    const treeEl = document.getElementById('block-tree');
    const voterEl = document.getElementById('voter-tree');
    const pendingEl = document.getElementById('pending-pool');
    const countEl = document.getElementById('block-count');
    const vCountEl = document.getElementById('voter-count');
    const viewerEl = document.getElementById('json-viewer');
    const mineBtn = document.getElementById('mine-btn');

    fetch('/api/system_state')
        .then(response => response.json())
        .then(data => {
            // Update Metadata
            countEl.innerText = data.blockchain.ledger.length;
            vCountEl.innerText = data.voter_registry.total_registered;

            // Update Sidebar Blocks
            treeEl.innerHTML = '';
            data.blockchain.ledger.forEach(block => {
                const link = document.createElement('a');
                link.href = '#';
                link.className = 'block-link';
                link.innerHTML = `
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/>
                    </svg>
                    Block #${block.index}
                `;
                link.onclick = (e) => {
                    e.preventDefault();
                    const pos = viewerEl.innerHTML.indexOf(`"index": ${block.index}`);
                    if (pos !== -1) viewerEl.scrollTop = pos * 0.1;
                };
                treeEl.appendChild(link);
            });

            // Update Sidebar Voters
            voterEl.innerHTML = '';
            data.voter_registry.registry.forEach(v => {
                const link = document.createElement('a');
                link.href = '#';
                link.className = 'block-link';
                link.style.fontSize = '0.75rem';
                link.innerHTML = `
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>
                    </svg>
                    ID: ${v.voter_id}
                `;
                link.onclick = (e) => {
                    e.preventDefault();
                    const pos = viewerEl.innerHTML.indexOf(`"voter_id": "${v.voter_id}"`);
                    if (pos !== -1) viewerEl.scrollTop = pos * 0.1;
                };
                voterEl.appendChild(link);
            });

            // Update Pending Pool
            pendingEl.innerHTML = '';
            if (data.pending_pool.count > 0) {
                mineBtn.style.display = 'block';
                data.pending_pool.transactions.forEach(tx => {
                    const div = document.createElement('div');
                    div.style.cssText = 'background: #1e293b; padding: 0.75rem; border-radius: 8px; margin-bottom: 0.5rem; font-size: 0.7rem; border: 1px dashed #fbbf24;';
                    div.innerHTML = `<strong>${tx.voter_id}</strong> ➔ ${tx.party}`;
                    pendingEl.appendChild(div);
                });
            } else {
                mineBtn.style.display = 'none';
                pendingEl.innerHTML = '<div style="padding: 1rem; color: #475569; font-size: 0.8rem; text-align: center;">Pool empty</div>';
            }

            // Show FULL system state
            viewerEl.innerHTML = syntaxHighlight(data);
        });
}

// Initial load
refreshChain();
