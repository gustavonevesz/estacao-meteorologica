const el = id => document.getElementById(id);
const ESTACAO_ID = 'esp32-01';
let registros = [], ocupado = false;
const formatar = valor => valor === null || valor === undefined ? '—' : typeof valor === 'number' ? valor.toLocaleString('pt-BR', {maximumFractionDigits: 2}) : valor;
function limpar() {
  registros = [];
  for (const campo of ['temperatura','umidade','pressao','estado','gas','temperatura_bmp']) el(campo).textContent = '—';
  el('luz').textContent = 'Saída digital · LDR';
  el('bmp').textContent = 'Aguardando sensor';
  el('horario').textContent = 'Aguardando primeira leitura';
  el('historico').replaceChildren(); el('vazio').hidden = false; el('exportar').disabled = true;
}
async function atualizar() {
  if (ocupado) return;
  ocupado = true;
  try {
    const resposta = await fetch('/api/leituras?' + new URLSearchParams({estacao_id: ESTACAO_ID, limite: '100'}), {cache:'no-store', signal: AbortSignal.timeout(8000)});
    if (!resposta.ok) throw new Error('HTTP ' + resposta.status);
    const dados = await resposta.json();
    limpar(); registros = dados;
    el('status').dataset.error = 'false';
    el('status').textContent = 'API conectada';
    if (!dados.length) { el('status').textContent = 'Aguardando dados'; return; }
    const ultima = dados[0];
    for (const campo of ['temperatura','umidade','pressao','estado','gas','temperatura_bmp']) el(campo).textContent = formatar(ultima[campo]);
    el('luz').textContent = 'Saída digital: ' + ultima.luz;
    el('bmp').textContent = ultima.bmp_conectado ? 'Sensor conectado' : 'Sem medição válida';
    el('horario').textContent = 'Última leitura: ' + new Date(ultima.recebido_em).toLocaleString('pt-BR');
    const atrasada = Date.now() - new Date(ultima.recebido_em).getTime() > 30000;
    el('status').textContent = atrasada ? 'Sem leituras recentes' : 'Recebendo dados';
    el('status').dataset.error = String(atrasada);
    el('vazio').hidden = true; el('exportar').disabled = false;
    for (const item of dados) {
      const tr = document.createElement('tr');
      for (const valor of [new Date(item.recebido_em).toLocaleString('pt-BR'), item.temperatura, item.umidade, item.pressao, item.estado, item.gas, item.temperatura_bmp]) {
        const td = document.createElement('td'); td.textContent = formatar(valor); tr.append(td);
      }
      el('historico').append(tr);
    }
  } catch (erro) {
    el('status').textContent = 'API indisponível — dados podem estar desatualizados';
    el('status').dataset.error = 'true';
  } finally { ocupado = false; }
}
el('exportar').addEventListener('click', () => {
  const campos = ['id','estacao_id','recebido_em','temperatura','umidade','pressao','estado','gas','temperatura_bmp','bmp_conectado'];
  const linhas = [campos.join(';'), ...registros.map(r => campos.map(c => '"' + String(r[c] ?? '').replaceAll('"','""') + '"').join(';'))];
  const url = URL.createObjectURL(new Blob(['\ufeff' + linhas.join('\r\n')], {type:'text/csv;charset=utf-8'}));
  const a = document.createElement('a'); a.href = url; a.download = 'leituras.csv'; a.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
});
atualizar(); setInterval(atualizar, 5000);
