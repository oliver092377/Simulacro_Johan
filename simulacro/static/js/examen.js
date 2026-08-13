/**
 * JS del examen VILLTECC
 * Timer congelable, auto-save AJAX, sync de tiempo, navegacion.
 */

let currentStep = 1;
const totalPreguntas = document.querySelectorAll('.pregunta-step').length;

// =============================================================================
// NAVEGACION ENTRE PREGUNTAS
// =============================================================================

function changeStep(delta) {
    jumpToStep(currentStep + delta);
}

function jumpToStep(step) {
    if (step < 1 || step > totalPreguntas) return;

    document.getElementById(`step-${currentStep}`).classList.remove('active-step');
    document.getElementById(`badge-${currentStep}`).classList.remove('current');

    currentStep = step;
    document.getElementById(`step-${currentStep}`).classList.add('active-step');
    document.getElementById(`badge-${currentStep}`).classList.add('current');

    document.getElementById('label-pregunta-actual').textContent =
        `Pregunta ${currentStep} de ${totalPreguntas}`;

    window.scrollTo(0, 0);
}

function marcarRespondida(n) {
    const badge = document.getElementById(`badge-${n}`);
    badge.classList.add('answered');
    actualizarContadorGlobal();
}

function actualizarContadorGlobal() {
    const respondidas = document.querySelectorAll('input[type="radio"]:checked').length;
    document.getElementById('cont-hechas').textContent = respondidas;
}

document.getElementById('badge-1').classList.add('current');

// =============================================================================
// AUTO-SAVE VIA AJAX
// =============================================================================

function autoSave(preguntaId, alternativaId) {
    fetch(AUTO_SAVE_URL, {
        method: 'POST',
        headers: { 'X-CSRFToken': CSRF_TOKEN, 'Content-Type': 'application/json' },
        body: JSON.stringify({ pregunta_id: preguntaId, alternativa_id: alternativaId })
    }).then(resp => {
        if (!resp.ok) throw new Error('Error al guardar');
        return resp.json();
    }).then(data => {
        if (data.ok) guardarEnLocalStorage(preguntaId, alternativaId);
    }).catch(() => {
        guardarEnLocalStorage(preguntaId, alternativaId);
    });
}

function guardarEnLocalStorage(preguntaId, alternativaId) {
    const storageKey = 'respuestas_backup_' + AREA_ID;
    let respuestas = {};
    try { respuestas = JSON.parse(localStorage.getItem(storageKey)) || {}; } catch (e) {}
    respuestas['pregunta_' + preguntaId] = String(alternativaId);
    localStorage.setItem(storageKey, JSON.stringify(respuestas));
}

// =============================================================================
// RESTAURAR RESPUESTAS DEL SERVIDOR
// =============================================================================

function restaurarRespuestas() {
    if (!RESPUESTAS_GUARDADAS || typeof RESPUESTAS_GUARDADAS !== 'object') return;
    for (const [preguntaId, alternativaId] of Object.entries(RESPUESTAS_GUARDADAS)) {
        const input = document.querySelector(`input[name="pregunta_${preguntaId}"][value="${alternativaId}"]`);
        if (input) {
            input.checked = true;
            const step = input.closest('.pregunta-step');
            if (step) marcarRespondida(parseInt(step.id.replace('step-', '')));
        }
    }
    actualizarContadorGlobal();
}

// =============================================================================
// RELOJ CONGELABLE
// Solo avanza cuando la pestana esta visible.
// Se sincroniza al servidor cada 30s y al salir de la pestana.
// =============================================================================

const display = document.getElementById('cronometro');
const SEGUNDOS_INICIALES = SEGUNDOS_RESTANTES;
let tiempoRestante = SEGUNDOS_RESTANTES;
let segundosActivosLocales = 0;
let segundosEnviados = 0; // total confirmado guardado en servidor
let timerIntervalo = null;
let syncIntervalo = null;
let examenFinalizado = false;
let timerActivo = false;

function formatearTiempo(totalSeg) {
    let h = Math.floor(totalSeg / 3600);
    let m = Math.floor((totalSeg % 3600) / 60);
    let s = totalSeg % 60;
    return (h < 10 ? "0" : "") + h + ":" + (m < 10 ? "0" : "") + m + ":" + (s < 10 ? "0" : "") + s;
}

function actualizarDisplay() {
    display.textContent = formatearTiempo(Math.max(0, tiempoRestante));
    if (tiempoRestante < 300 && tiempoRestante > 0) {
        display.classList.add('reloj-alerta');
    } else {
        display.classList.remove('reloj-alerta');
    }
}

// Timer basado en timestamps absolutos (no acumula intervals)
function tickTimer() {
    if (examenFinalizado || !timerActivo) return;

    segundosActivosLocales++;
    tiempoRestante = Math.max(0, SEGUNDOS_INICIALES - segundosActivosLocales);
    actualizarDisplay();

    if (tiempoRestante <= 0) {
        tiempoAgotado();
    }
}

function iniciarTimer() {
    if (timerActivo) return;
    timerActivo = true;
    actualizarDisplay();
    // Limpiar intervalo previo si existe
    if (timerIntervalo) clearInterval(timerIntervalo);
    timerIntervalo = setInterval(tickTimer, 1000);
}

function pausarTimer() {
    timerActivo = false;
    if (timerIntervalo) {
        clearInterval(timerIntervalo);
        timerIntervalo = null;
    }
}

// Sincronizar tiempo al servidor
function syncTiempo(forzar) {
    if (examenFinalizado) return;

    const delta = segundosActivosLocales - segundosEnviados;
    if (!forzar && delta <= 0) return;

    const payload = { segundos_activos: delta };

    fetch(SINCRONIZAR_TIEMPO_URL, {
        method: 'POST',
        headers: { 'X-CSRFToken': CSRF_TOKEN, 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    }).then(resp => resp.json()).then(data => {
        if (data.ok) {
            segundosEnviados = segundosActivosLocales;
            if (data.tiempo_agotado) {
                tiempoAgotado();
            }
        }
    }).catch(() => {
        // Si falla, el timer local sigue corriendo
    });
}

// Sync periodico cada 30 segundos
syncIntervalo = setInterval(function() { syncTiempo(false); }, 30000);

// =============================================================================
// DETECCION DE VISIBILIDAD (congelar/reanudar timer)
// =============================================================================

document.addEventListener('visibilitychange', function() {
    if (examenFinalizado) return;

    if (document.hidden) {
        // Pestaña oculta → pausar timer y sincronizar
        pausarTimer();
        syncTiempo(true);
    } else {
        // Pestaña visible → reanudar timer
        iniciarTimer();
    }
});

// Al perder foco de ventana (otra app, minimize, etc.)
window.addEventListener('blur', function() {
    if (!examenFinalizado) {
        pausarTimer();
        syncTiempo(true);
    }
});

// Al recuperar foco
window.addEventListener('focus', function() {
    if (!examenFinalizado) {
        iniciarTimer();
    }
});

// =============================================================================
// TIEMPO AGOTADO — overlay + auto-enviar
// =============================================================================

function tiempoAgotado() {
    if (examenFinalizado) return;
    examenFinalizado = true;

    pausarTimer();
    if (syncIntervalo) clearInterval(syncIntervalo);

    // Crear overlay
    const overlay = document.createElement('div');
    overlay.id = 'overlay-tiempo-agotado';
    overlay.style.cssText = `
        position: fixed; top: 0; left: 0; width: 100%; height: 100%;
        background: rgba(0,0,0,0.85); z-index: 9999;
        display: flex; flex-direction: column; align-items: center; justify-content: center;
        color: white; font-family: 'Segoe UI', sans-serif; text-align: center;
    `;
    overlay.innerHTML = `
        <div style="max-width: 500px; padding: 40px;">
            <div style="font-size: 80px; margin-bottom: 20px;">⏰</div>
            <h1 style="font-size: 2rem; margin-bottom: 15px; color: #e74c3c;">
                ¡El tiempo para el examen se ha acabado!
            </h1>
            <p style="font-size: 1.1rem; color: #bdc3c7; margin-bottom: 30px;">
                Tus respuestas han sido enviadas automaticamente.
            </p>
            <div id="mensaje-finalizando" style="font-size: 1rem; color: #f39c12;">
                <div class="spinner" style="
                    width: 30px; height: 30px; border: 3px solid rgba(255,255,255,0.3);
                    border-top-color: #f39c12; border-radius: 50%;
                    animation: girar 0.8s linear infinite; margin: 0 auto 15px;
                "></div>
                Enviando tus respuestas...
            </div>
        </div>
        <style>@keyframes girar { to { transform: rotate(360deg); } }</style>
    `;
    document.body.appendChild(overlay);

    // Enviar examen via AJAX
    fetch(FINALIZAR_EXAMEN_URL, {
        method: 'POST',
        headers: { 'X-CSRFToken': CSRF_TOKEN }
    }).then(resp => resp.json()).then(data => {
        if (data.ok && data.redirect_url) {
            localStorage.removeItem('respuestas_backup_' + AREA_ID);
            window.location.href = data.redirect_url;
        } else {
            document.getElementById('mensaje-finalizando').innerHTML =
                '<p style="color: #e74c3c;">Error al enviar. <a href="#" onclick="reintentarFinalizar()" style="color: #3498db;">Reintentar</a></p>';
        }
    }).catch(() => {
        document.getElementById('mensaje-finalizando').innerHTML =
            '<p style="color: #e74c3c;">Error de conexion. <a href="#" onclick="reintentarFinalizar()" style="color: #3498db;">Reintentar</a></p>';
    });
}

function reintentarFinalizar() {
    const msg = document.getElementById('mensaje-finalizando');
    if (msg) msg.innerHTML = '<p style="color: #f39c12;">Reintentando...</p>';
    fetch(FINALIZAR_EXAMEN_URL, {
        method: 'POST',
        headers: { 'X-CSRFToken': CSRF_TOKEN }
    }).then(resp => resp.json()).then(data => {
        if (data.ok && data.redirect_url) {
            window.location.href = data.redirect_url;
        }
    }).catch(() => {
        if (msg) msg.innerHTML = '<p style="color: #e74c3c;">Error. <a href="#" onclick="reintentarFinalizar()" style="color: #3498db;">Reintentar</a></p>';
    });
}

// =============================================================================
// PREVENCION DE SALIDA Y ENVIO
// =============================================================================

function prevenirSalida(e) {
    if (tiempoRestante > 0 && !examenFinalizado) {
        e.preventDefault();
        e.returnValue = '';
    }
}

// Sync confiable al salir usando sendBeacon
window.addEventListener('beforeunload', function() {
    if (!examenFinalizado) {
        pausarTimer();
        const delta = segundosActivosLocales - segundosEnviados;
        if (delta > 0) {
            const payload = JSON.stringify({ segundos_activos: delta });
            const blob = new Blob([payload], { type: 'text/plain' });
            navigator.sendBeacon(SINCRONIZAR_TIEMPO_URL, blob);
            segundosEnviados = segundosActivosLocales;
        }
    }
});
window.addEventListener('beforeunload', prevenirSalida);

const formulario = document.getElementById('formulario-examen');
formulario.addEventListener('submit', function() {
    localStorage.removeItem('respuestas_backup_' + AREA_ID);
    window.removeEventListener('beforeunload', prevenirSalida);
    if (syncIntervalo) clearInterval(syncIntervalo);
});

// Bloquear boton atras
history.pushState(null, null, location.href);
window.onpopstate = function() { history.go(1); };

// =============================================================================
// INICIALIZAR
// =============================================================================

restaurarRespuestas();
iniciarTimer();
