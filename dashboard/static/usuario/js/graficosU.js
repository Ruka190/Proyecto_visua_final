// Iniciar primero el html con los datos
document.addEventListener('DOMContentLoaded', () => {
  // Fuente y color por defecto para todos los gráficos
  Chart.defaults.font.family = "'Poppins', sans-serif";
  Chart.defaults.color = '#4C2A36';

  // Leer los datos desde el django
  const leerJSON = (id, fallback) => {
    try {
      const el = document.getElementById(id);
      return el && el.textContent.trim() ? JSON.parse(el.textContent) : fallback;
    } catch {
      return fallback;
    }
  };

  // Manejar los botones para mostrar y ocultar los gráficos
  const mostrarOcultar = (btnId, panelId, txtVer, txtOcultar, onShow) => {
    const btn = document.getElementById(btnId);
    const panel = document.getElementById(panelId);
    if (!btn || !panel) return;

    btn.addEventListener('click', () => {
      const oculto = panel.classList.toggle('d-none');
      panel.classList.toggle('d-flex', !oculto);
      btn.innerHTML = `<i class="bi bi-${oculto ? 'eye-fill' : 'eye-slash-fill'} me-1"></i> ${oculto ? txtVer : txtOcultar}`;
      btn.style.backgroundColor = oculto ? '#f3a69a' : '#e58f82';
      btn.style.color = oculto ? '#4C2A36' : '#ffffff';
      if (!oculto && onShow) setTimeout(onShow, 50);
    });
  };

  // ==========================================
  // GRÁFICO 1: MATCHES (DONA)
  // ==========================================
  const dataMatches = leerJSON('datos-grafico', { labels: ['Match', 'No Match'], data: [14, 8] });
  let chartMatches = null;
  
  mostrarOcultar('btnToggleGrafico', 'seccionGrafico', 'Ver balance de Matches', 'Ocultar balance de Matches', () => {
    if (chartMatches) {
      chartMatches.resize();
      return;
    }
    const canvas = document.getElementById('miGrafico');
    if (!canvas) return;
    
    chartMatches = new Chart(canvas, {
      type: 'doughnut',
      data: {
        labels: dataMatches.labels,
        datasets: [{ data: dataMatches.data, backgroundColor: ['#D62D5A', '#B944482E'], borderColor: '#4C2A36', borderWidth: 1 }]
      },
      options: { responsive: true, plugins: { legend: { position: 'bottom' } } }
    });
  });

  // ==========================================
  // GRÁFICO 2: TIEMPO EN LA APP (BARRAS)
  // ==========================================
  const dataTiempo = leerJSON('datos-tiempo', {});
  let chartTiempo = null, periodoActual = 'diario';
  
  const renderTiempo = (periodo) => {
    periodoActual = periodo;
    const conf = dataTiempo[periodo] || { labels: [], data: [], unit: '', label: '' };

    // Calcular la suma total de los datos del periodo seleccionado para el KPI
    const total = (conf.data || []).reduce((acumulado, valor) => acumulado + Number(valor), 0);

    // Actualizar el número y la unidad en la tarjeta KPI de tiempo total
    const totalEl = document.getElementById('total-tiempo');
    if (totalEl) {
      totalEl.textContent = `${total} ${conf.unit}`;
    }

    const canvas = document.getElementById('graficoTiempo');
    if (!canvas) return;

    if (!chartTiempo) {
      chartTiempo = new Chart(canvas, {
        type: 'bar',
        data: { labels: conf.labels, datasets: [{ data: conf.data, backgroundColor: '#D62D5A', borderColor: '#4C2A36', borderWidth: 1, borderRadius: 6 }] },
        options: {
          responsive: true, maintainAspectRatio: false,
          scales: { y: { beginAtZero: true, ticks: { callback: v => `${v} ${conf.unit}` } }, x: { grid: { display: false } } },
          plugins: { legend: { display: false } }
        }
      });
    } else {
      chartTiempo.data.labels = conf.labels;
      chartTiempo.data.datasets[0].data = conf.data;
      chartTiempo.options.scales.y.ticks.callback = v => `${v} ${conf.unit}`;
      chartTiempo.update();
      chartTiempo.resize();
    }
  };

  mostrarOcultar('btnToggleTiempo', 'seccionTiempo', 'Ver tiempo en la app', 'Ocultar tiempo en la app', () => renderTiempo(periodoActual));
  
  document.querySelectorAll('.btn-periodo[data-periodo]').forEach(b => b.addEventListener('click', () => {
    document.querySelectorAll('.btn-periodo[data-periodo]').forEach(x => x.classList.remove('active'));
    b.classList.add('active');
    renderTiempo(b.dataset.periodo);
  }));

  // ==========================================
  // GRÁFICO 3: CARACTERÍSTICAS DE MATCH (BARRAS HORIZONTALES)
  // ==========================================
  const dataCaracteristicas = leerJSON('datos-caracteristicas', {});
  let chartCaracteristicas = null, catActual = 'orientacion';
  
  const renderCaracteristicas = (car) => {
    catActual = car;
    const conf = dataCaracteristicas[car] || { labels: [], data: [] };
    const canvas = document.getElementById('graficoCaracteristicas');
    if (!canvas) return;

    if (!chartCaracteristicas) {
      chartCaracteristicas = new Chart(canvas, {
        type: 'bar',
        data: { labels: conf.labels, datasets: [{ data: conf.data, backgroundColor: '#D62D5A', borderColor: '#4C2A36', borderWidth: 1, borderRadius: 6 }] },
        options: {
          indexAxis: 'y', responsive: true, maintainAspectRatio: false,
          scales: { x: { beginAtZero: true, ticks: { stepSize: 1 } }, y: { grid: { display: false } } },
          plugins: { legend: { display: false }, tooltip: { callbacks: { label: ctx => `${ctx.parsed.x} matches` } } }
        }
      });
    } else {
      chartCaracteristicas.data.labels = conf.labels;
      chartCaracteristicas.data.datasets[0].data = conf.data;
      chartCaracteristicas.update();
      chartCaracteristicas.resize();
    }
  };

  mostrarOcultar('btnToggleCaracteristicas', 'seccionCaracteristicas', 'Ver tipo de Match en números', 'Ocultar grafico Caracteristicas', () => renderCaracteristicas(catActual));
  
  document.querySelectorAll('.btn-caracteristicas[data-categoria]').forEach(b => b.addEventListener('click', () => {
    document.querySelectorAll('.btn-caracteristicas[data-categoria]').forEach(x => x.classList.remove('active'));
    b.classList.add('active');
    renderCaracteristicas(b.dataset.categoria);
  }));

  // ==========================================
  // GRÁFICO 4: RADAR DE AFINIDAD (GUSTOS / DISGUSTOS)
  // ==========================================
  const dataRadar = leerJSON('datos-radar', { categorias: [], gustos_data: [], disgustos_data: [] });
  let chartRadar = null, tipoRadar = 'gustos';
  
  const renderRadar = (tipo) => {
    tipoRadar = tipo;
    const canvas = document.getElementById('graficoRadar');
    if (!canvas) return;

    const esGustos = tipo === 'gustos';
    const valores = esGustos ? dataRadar.gustos_data : dataRadar.disgustos_data;
    const color = esGustos ? '#D62D5A' : '#4C2A36';
    const bg = esGustos ? 'rgba(214, 45, 90, 0.25)' : 'rgba(76, 42, 54, 0.2)';

    if (!chartRadar) {
      chartRadar = new Chart(canvas, {
        type: 'radar',
        data: {
          labels: dataRadar.categorias,
          datasets: [{ data: valores, fill: true, backgroundColor: bg, borderColor: color, borderWidth: 2, pointBackgroundColor: color }]
        },
        options: {
          responsive: true, maintainAspectRatio: false,
          scales: { r: { suggestedMin: 0, suggestedMax: 100, ticks: { display: false } } },
          plugins: { legend: { display: false } }
        }
      });
    } else {
      chartRadar.data.datasets[0].data = valores;
      chartRadar.data.datasets[0].borderColor = color;
      chartRadar.data.datasets[0].backgroundColor = bg;
      chartRadar.data.datasets[0].pointBackgroundColor = color;
      chartRadar.update();
      chartRadar.resize();
    }
  };

  mostrarOcultar('btnToggleRadar', 'seccionRadar', 'Ver Gustos y Disgustos en común', 'Ocultar gráfico Coincidencias', () => renderRadar(tipoRadar));
  
  document.querySelectorAll('[data-tipo-radar]').forEach(b => b.addEventListener('click', () => {
    document.querySelectorAll('[data-tipo-radar]').forEach(x => x.classList.remove('active'));
    b.classList.add('active');
    renderRadar(b.dataset.tipoRadar);
  }));
});