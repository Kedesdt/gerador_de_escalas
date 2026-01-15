// Drag and Drop Functions
function allowDrop(ev) {
    ev.preventDefault();
    ev.currentTarget.classList.add('drag-over');
}

function removeDragOver(ev) {
    ev.currentTarget.classList.remove('drag-over');
}

function dragFunc(ev) {
    const funcionarioId = ev.target.getAttribute('data-funcionario-id');
    const escalaId = ev.target.getAttribute('data-escala-id');
    const folgaId = ev.target.getAttribute('data-folga-id');
    
    ev.dataTransfer.setData("funcionarioId", funcionarioId);
    if (escalaId) ev.dataTransfer.setData("escalaId", escalaId);
    if (folgaId) ev.dataTransfer.setData("folgaId", folgaId);
}

function dropTurno(ev) {
    ev.preventDefault();
    ev.currentTarget.classList.remove('drag-over');
    
    const funcionarioId = ev.dataTransfer.getData("funcionarioId");
    const escalaIdAntiga = ev.dataTransfer.getData("escalaId");
    const folgaId = ev.dataTransfer.getData("folgaId");
    const data = ev.currentTarget.getAttribute('data-date');
    const faixaId = ev.currentTarget.getAttribute('data-faixa-id');
    
    adicionarEscala(funcionarioId, faixaId, data, escalaIdAntiga, folgaId);
}

function dropFolga(ev) {
    ev.preventDefault();
    ev.currentTarget.classList.remove('drag-over');
    
    const funcionarioId = ev.dataTransfer.getData("funcionarioId");
    const escalaId = ev.dataTransfer.getData("escalaId");
    const data = ev.currentTarget.getAttribute('data-date');
    
    adicionarFolga(funcionarioId, data, escalaId);
}

// API Functions
async function adicionarEscala(funcionarioId, faixaId, data, escalaIdAntiga, folgaId) {
    try {
        // Se veio de uma escala antiga ou folga, remover primeiro
        if (escalaIdAntiga) {
            await fetch(`/api/escala/${escalaIdAntiga}/remover`, { method: 'DELETE' });
        }
        if (folgaId) {
            await fetch(`/api/folga/${folgaId}/remover`, { method: 'DELETE' });
        }
        
        const response = await fetch('/api/escala/adicionar', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                funcionario_id: funcionarioId,
                faixa_horario_id: faixaId,
                data: data
            })
        });
        
        if (response.ok) {
            location.reload();
        } else {
            const result = await response.json();
            alert(result.erro || 'Erro ao adicionar na escala');
            location.reload();
        }
    } catch (error) {
        alert('Erro: ' + error);
        location.reload();
    }
}

async function adicionarFolga(funcionarioId, data, escalaId) {
    try {
        // Se veio de uma escala, remover primeiro
        if (escalaId) {
            await fetch(`/api/escala/${escalaId}/remover`, { method: 'DELETE' });
        }
        
        const response = await fetch('/api/folga/adicionar', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                funcionario_id: funcionarioId,
                data: data
            })
        });
        
        if (response.ok) {
            location.reload();
        } else {
            const result = await response.json();
            alert(result.erro || 'Erro ao adicionar folga');
            location.reload();
        }
    } catch (error) {
        alert('Erro: ' + error);
        location.reload();
    }
}

async function removerEscala(escalaId, data) {
    if (!confirm('Deseja remover este funcionário do turno?')) return;
    
    try {
        const response = await fetch(`/api/escala/${escalaId}/remover`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            location.reload();
        }
    } catch (error) {
        alert('Erro ao remover: ' + error);
    }
}

async function removerFolga(folgaId) {
    if (!confirm('Deseja remover esta folga?')) return;
    
    try {
        const response = await fetch(`/api/folga/${folgaId}/remover`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            location.reload();
        }
    } catch (error) {
        alert('Erro ao remover folga: ' + error);
    }
}

async function toggleBloqueio(data) {
    try {
        const response = await fetch('/api/dia-bloqueado/toggle', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ data: data })
        });
        
        if (response.ok) {
            location.reload();
        } else {
            alert('Erro ao bloquear/desbloquear dia');
        }
    } catch (error) {
        alert('Erro: ' + error);
    }
}

async function gerarEscala(mes, ano) {
    if (!confirm('Deseja gerar uma sugestão de escala para este mês? Isso pode substituir folgas existentes.')) {
        return;
    }
    
    try {
        const response = await fetch('/admin/gerar-escala', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                mes: mes,
                ano: ano
            })
        });
        
        const result = await response.json();
        
        if (response.ok) {
            alert('Escala gerada com sucesso!');
            location.reload();
        } else {
            alert(result.erro || 'Erro ao gerar escala');
        }
    } catch (error) {
        alert('Erro ao gerar escala: ' + error);
    }
}

// Prevenir drag-over default
document.addEventListener('dragover', function(e) {
    const target = e.target.closest('td[data-date]');
    if (!target) {
        document.querySelectorAll('.drag-over').forEach(el => {
            el.classList.remove('drag-over');
        });
    }
});
