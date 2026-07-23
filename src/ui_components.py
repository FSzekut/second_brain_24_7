from datetime import date
from pathlib import Path
import logging
import os
import re
import secrets
import time
import streamlit as st

logger = logging.getLogger(__name__)

# Estado de bloqueio por processo (não por sessão de navegador) — assim abrir
# uma aba/sessão nova não reseta a contagem de tentativas erradas.
_gate_throttle = {"attempts": 0, "locked_until": 0.0}
_GATE_MAX_ATTEMPTS = 5
_GATE_BASE_COOLDOWN = 30  # segundos

_EMAIL_LIKE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")

# Glifos de linha customizados (2px stroke, sem fonte de ícone padrão) — cada
# um abstrato, ligado ao tema em vez de ser o objeto literal (vassoura/porta/
# caneta/engrenagem).
_ICON_RESET = """<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12a9 9 0 1 0 3-6.7"/><polyline points="3 4 3 9 8 9"/></svg>"""

_ICON_DISCONNECT = """<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="3" y1="12" x2="9" y2="12"/><line x1="15" y1="12" x2="21" y2="12"/><circle cx="12" cy="12" r="1.5" fill="currentColor" stroke="none"/></svg>"""

_ICON_CAPTURE = """<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M4 8V5a1 1 0 0 1 1-1h3"/><path d="M16 4h3a1 1 0 0 1 1 1v3"/><path d="M20 16v3a1 1 0 0 1-1 1h-3"/><path d="M8 20H5a1 1 0 0 1-1-1v-3"/><circle cx="12" cy="12" r="2" fill="currentColor" stroke="none"/></svg>"""

_ICON_TUNE = """<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="5" y1="4" x2="5" y2="20"/><circle cx="5" cy="9" r="2" fill="currentColor" stroke="none"/><line x1="12" y1="4" x2="12" y2="20"/><circle cx="12" cy="15" r="2" fill="currentColor" stroke="none"/><line x1="19" y1="4" x2="19" y2="20"/><circle cx="19" cy="6" r="2" fill="currentColor" stroke="none"/></svg>"""


def _icon_tag(svg, label, color, header=False):
    header_class = " as-header" if header else ""
    st.markdown(f'<div class="icon-tag{header_class} tag-{color}">{svg}{label}</div>', unsafe_allow_html=True)


def _render_gate_scene():
    st.markdown(
        """
        <div class="gate-scene">
          <div class="gate-horizon"><div class="plane"></div></div>
          <p class="gate-eyebrow">// sinal criptografado</p>
          <div class="gate-title" role="heading" aria-level="1">
            <div class="gate-title-echo" aria-hidden="true">LIMIAR</div>
            <div class="gate-title-main">LIMIAR</div>
          </div>
          <p class="gate-subtitle">Alguns terminais só respondem a quem já os conhece.</p>
          <div class="gate-prompt-row"><span class="gate-prompt-glyph">&gt;</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _inject_gate_cursor():
    st.iframe(
        """
        <script>
        (function () {
          try {
            var doc = window.parent.document;
            if (window.parent.__gateCursorCleanup) { window.parent.__gateCursorCleanup(); }

            var dot = doc.createElement('div');
            dot.className = 'gate-cursor-dot';
            var ring = doc.createElement('div');
            ring.className = 'gate-cursor-ring';
            doc.body.appendChild(dot);
            doc.body.appendChild(ring);

            var mouseX = window.parent.innerWidth / 2, mouseY = window.parent.innerHeight / 2;
            var ringX = mouseX, ringY = mouseY, raf = null;

            function onMove(e) {
              mouseX = e.clientX;
              mouseY = e.clientY;
              dot.style.transform = 'translate(' + mouseX + 'px,' + mouseY + 'px) translate(-50%,-50%)';
            }
            function animate() {
              ringX += (mouseX - ringX) * 0.15;
              ringY += (mouseY - ringY) * 0.15;
              ring.style.transform = 'translate(' + ringX + 'px,' + ringY + 'px) translate(-50%,-50%)';
              raf = doc.defaultView.requestAnimationFrame(animate);
            }
            function targetIsInteractive(el) {
              return el.closest && el.closest('div[data-testid="stTextInput"], button, a');
            }
            function onOver(e) { if (targetIsInteractive(e.target)) { ring.classList.add('is-active'); } }
            function onOut(e) { if (targetIsInteractive(e.target)) { ring.classList.remove('is-active'); } }

            doc.addEventListener('mousemove', onMove);
            doc.addEventListener('mouseover', onOver);
            doc.addEventListener('mouseout', onOut);
            animate();

            window.parent.__gateCursorCleanup = function () {
              doc.removeEventListener('mousemove', onMove);
              doc.removeEventListener('mouseover', onOver);
              doc.removeEventListener('mouseout', onOut);
              if (raf) { doc.defaultView.cancelAnimationFrame(raf); }
              dot.remove();
              ring.remove();
            };
          } catch (e) {
            console.warn('gate cursor indisponível, seguindo com cursor padrão', e);
          }
        })();
        </script>
        """,
        height=1,
    )


def check_password():
    def password_entered():
        now = time.time()
        if now < _gate_throttle["locked_until"]:
            st.session_state["password_correct"] = False
            return

        entered = st.session_state.get("password", "")
        real = os.getenv("APP_PASSWORD", "")
        if secrets.compare_digest(entered, real):
            st.session_state["password_correct"] = True
            _gate_throttle["attempts"] = 0
            _gate_throttle["lockouts"] = 0
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False
            if _EMAIL_LIKE.match(entered):
                logger.info("Tentativa de acesso ao gate com formato de e-mail: %s", entered)
            _gate_throttle["attempts"] += 1
            if _gate_throttle["attempts"] >= _GATE_MAX_ATTEMPTS:
                _gate_throttle["lockouts"] = _gate_throttle.get("lockouts", 0) + 1
                cooldown = min(_GATE_BASE_COOLDOWN * (2 ** (_gate_throttle["lockouts"] - 1)), 900)
                _gate_throttle["locked_until"] = now + cooldown
                _gate_throttle["attempts"] = 0

    if st.session_state.get("password_correct", False):
        return True

    load_css("gate.css")
    _render_gate_scene()

    remaining = _gate_throttle["locked_until"] - time.time()
    if remaining > 0:
        st.markdown(
            f'<p class="gate-denied">// canal bloqueado — tente novamente em {int(remaining) + 1}s</p>',
            unsafe_allow_html=True,
        )
    else:
        st.text_input(
            "Senha de acesso",
            type="password",
            on_change=password_entered,
            key="password",
            label_visibility="collapsed",
        )
        if "password_correct" in st.session_state and not st.session_state["password_correct"]:
            last_try = st.session_state.get("password", "")
            if _EMAIL_LIKE.match(last_try):
                st.markdown('<p class="gate-denied">// sinal rejeitado</p>', unsafe_allow_html=True)
            else:
                st.markdown(
                    '<p class="gate-denied">// formato de e-mail inválido<br>// você sabe o que está fazendo?</p>',
                    unsafe_allow_html=True,
                )

    _inject_gate_cursor()
    return False

def load_css(file_name):
    css_path = Path(__file__).parent / "assets" / file_name
    if css_path.exists():
        st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)


def render_page_config():
    st.set_page_config(
        page_title="Meu Claude Pessoal",
        page_icon="🤖",
        layout="centered",
        initial_sidebar_state="auto",
    )
    st.markdown(
        '<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">',
        unsafe_allow_html=True,
    )


def render_sidebar(providers, default_messages):
    with st.sidebar:
        _icon_tag(_ICON_TUNE, "Configurações", "cyan", header=True)
        st.markdown("Ajuste os parâmetros do seu assistente.")

        selected_provider_name = st.selectbox(
            "Escolha o provedor:",
            options=list(providers.keys()),
        )
        st.session_state.selected_provider = selected_provider_name

        model_mapping = providers[selected_provider_name]["models"]
        selected_model_name = st.selectbox(
            "Escolha o modelo:",
            options=list(model_mapping.keys()),
        )
        st.session_state.selected_model = model_mapping[selected_model_name]

        _icon_tag(_ICON_RESET, "Limpar histórico", "amber")
        if st.button("Limpar Histórico da Conversa", key="clear_btn"):
            st.session_state.messages = default_messages.copy()
            st.success("Histórico limpo!")

        st.divider()

        _icon_tag(_ICON_DISCONNECT, "Encerrar sessão", "purple")
        if st.button("Sair", key="logout_btn"):
            st.session_state["password_correct"] = False
            st.rerun()

    return selected_provider_name, selected_model_name


def render_message_history(messages):
    for message in messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

def render_alerts_panel(alerts):
    if not alerts:
        return

    today = date.today()
    has_overdue = False
    rows = []
    for alert in alerts:
        try:
            prazo = date.fromisoformat(alert["prazo"])
        except (KeyError, ValueError):
            continue
        dias = (prazo - today).days
        if dias < 0:
            dot_class = "dot-red"
            has_overdue = True
        elif dias <= 3:
            dot_class = "dot-amber"
        else:
            dot_class = "dot-muted"
        projeto = f" ({alert['projeto']})" if alert.get("projeto") else ""
        rows.append(
            f'<span class="status-dot {dot_class}"></span>'
            f"**{alert['titulo']}**{projeto} — prazo: {alert['prazo']}"
        )

    if not rows:
        return

    with st.expander(f"Alertas ({len(rows)})", icon=":material/notifications:", expanded=has_overdue):
        for row in rows:
            st.markdown(row, unsafe_allow_html=True)


def render_note_capture(save_fn):
    with st.sidebar:
        with st.expander("Capturar nota rápida"):
            _icon_tag(_ICON_CAPTURE, "Nova entrada", "cyan")
            with st.form(key="note_form", clear_on_submit=True):
                title = st.text_input("Título (opcional)")
                content = st.text_area("O que você quer anotar?")
                submitted = st.form_submit_button("Salvar nota", icon=":material/save:")

            if submitted:
                if content.strip():
                    filename = save_fn(title, content)
                    st.success(f"Salvo: {filename}")
                else:
                    st.warning("Escreve alguma coisa antes de salvar 🙂")