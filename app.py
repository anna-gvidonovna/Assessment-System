import numpy as np
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ── Шкала оценок ─────────────────────────────────────────────────────────────
GRADE_SCALE = [
    (92, 100, 'A', '5 Отл',  '#2d6a4f', '#d8f3dc'),
    (82,  91, 'B', '5 Отл',  '#40916c', '#d8f3dc'),
    (62,  81, 'C', '4 Хор',  '#1d6fa4', '#dae8fc'),
    (52,  61, 'D', '3 Удов', '#e07b00', '#fff2cc'),
    (42,  51, 'E', '3 Удов', '#c9a000', '#ffe8a0'),
    ( 0,  41, 'F', '2 Неуд', '#c0392b', '#f8cecc'),
]

COLORS_MAP = ['#f8cecc', '#ffe8a0', '#fff2cc', '#dae8fc', '#b8daf5', '#d8f3dc']
GRADE_NUM = {'A': 5, 'B': 4, 'C': 3, 'D': 2, 'E': 1, 'F': 0}
GRADE_LABEL = {v: k for k, v in GRADE_NUM.items()}

GRADE_COLORSCALE = [
    [0/6, '#f8cecc'], [1/6, '#f8cecc'],
    [1/6, '#ffe8a0'], [2/6, '#ffe8a0'],
    [2/6, '#fff2cc'], [3/6, '#fff2cc'],
    [3/6, '#dae8fc'], [4/6, '#dae8fc'],
    [4/6, '#b8daf5'], [5/6, '#b8daf5'],
    [5/6, '#d8f3dc'], [6/6, '#d8f3dc'],
]


def get_grade(s):
    s = int(round(s))
    for lo, hi, ects, ru, fg, bg in GRADE_SCALE:
        if lo <= s <= hi:
            return ects, ru, fg, bg
    return 'F', '2 Неуд', '#c0392b', '#f8cecc'


def calc_score(att, tim, var, w_att, w_tim, w_var):
    return round(w_att * att + w_tim * tim + w_var * var)


def rule_a(s, threshold):
    return s >= threshold


def rule_b(s, var, threshold, var_threshold):
    return s >= threshold and var >= var_threshold


def compute_matrices(wa, wt, wv, tim, threshold, var_thresh):
    att_vals = np.arange(0, 101, 2)
    var_vals = np.arange(0, 101, 2)

    mat_a = np.zeros((len(att_vals), len(var_vals)))
    mat_b = np.zeros((len(att_vals), len(var_vals)))
    hover_a = []
    hover_b = []
    diff_pts = {'x': [], 'y': []}

    for i, att in enumerate(att_vals):
        row_a, row_b = [], []
        for j, var in enumerate(var_vals):
            s = calc_score(att, tim, var, wa, wt, wv)
            ects, ru, *_ = get_grade(s)
            gn = GRADE_NUM[ects]

            val_a = gn if rule_a(s, threshold) else 0
            val_b = gn if rule_b(s, var, threshold, var_thresh) else 0
            mat_a[i, j] = val_a
            mat_b[i, j] = val_b

            grade_a = GRADE_LABEL[val_a]
            grade_b = GRADE_LABEL[val_b]
            row_a.append(f'a={att}, v={var}<br>S={s} → {grade_a} ({ru})')
            row_b.append(f'a={att}, v={var}<br>S={s} → {grade_b} ({ru})')

            if rule_a(s, threshold) and not rule_b(s, var, threshold, var_thresh):
                diff_pts['x'].append(var)
                diff_pts['y'].append(att)

        hover_a.append(row_a)
        hover_b.append(row_b)

    n_diff = len(diff_pts['x'])
    n_total = len(att_vals) * len(var_vals)
    pct_diff = 100 * n_diff / n_total

    return att_vals, var_vals, mat_a, mat_b, hover_a, hover_b, diff_pts, n_diff, n_total, pct_diff


def build_figure(att_vals, var_vals, mat_a, mat_b, hover_a, hover_b,
                 diff_pts, threshold, var_thresh, n_diff, n_total, pct_diff,
                 w_att_pct, wt_pct, w_var_pct, tim):

    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=[
            f'Правило A:  S \u2265 \u03b8={threshold}   (\u03b1={w_att_pct}%, \u03b2={wt_pct}%, \u03b3={w_var_pct}%)',
            f'Правило B:  S \u2265 \u03b8={threshold}  \u2227  v \u2265 v\u2080={var_thresh}   \u2014  расхождений: {n_diff}/{n_total} ({pct_diff:.1f}%)',
        ],
        horizontal_spacing=0.08,
    )

    common = dict(
        x=var_vals, y=att_vals,
        colorscale=GRADE_COLORSCALE,
        zmin=-0.5, zmax=5.5,
        showscale=False,
        hovertemplate='%{hovertext}<extra></extra>',
    )

    fig.add_trace(go.Heatmap(
        z=mat_a, hovertext=hover_a, name='Правило A', **common
    ), row=1, col=1)

    fig.add_trace(go.Heatmap(
        z=mat_b, hovertext=hover_b, name='Правило B', **common
    ), row=1, col=2)

    if diff_pts['x']:
        fig.add_trace(go.Scatter(
            x=diff_pts['x'], y=diff_pts['y'],
            mode='markers',
            marker=dict(symbol='circle', color='#c0392b', size=4, opacity=0.45),
            name=f'A\u2260B ({n_diff})',
            hovertemplate='a=%{y}, v=%{x}<extra>A\u2260B</extra>',
        ), row=1, col=2)

    for col in (1, 2):
        fig.add_vline(x=var_thresh, line_dash='dash', line_color='white',
                      line_width=2, col=col, row=1)

    grade_legend = [
        ('A — 5 Отл (92–100)', COLORS_MAP[5]),
        ('B — 5 Отл (82–91)',  COLORS_MAP[4]),
        ('C — 4 Хор (62–81)',  COLORS_MAP[3]),
        ('D — 3 Удов (52–61)', COLORS_MAP[2]),
        ('E — 3 Удов (42–51)', COLORS_MAP[1]),
        ('F — 2 Неуд (0–41)',  COLORS_MAP[0]),
    ]
    for label, color in grade_legend:
        fig.add_trace(go.Scatter(
            x=[None], y=[None], mode='markers',
            marker=dict(size=12, color=color, symbol='square',
                        line=dict(color='#aaa', width=1)),
            name=label, showlegend=True,
        ))

    fig.update_xaxes(title_text='v (вариативный)', range=[0, 100])
    fig.update_yaxes(title_text='a (посещаемость)', range=[0, 100])
    fig.update_layout(
        height=560,
        title=dict(
            text=(f't={tim}  \u00b7  \u03b1={w_att_pct}%  \u03b2={wt_pct}%  \u03b3={w_var_pct}%'
                  f'  \u00b7  \u03b8={threshold}'),
            font=dict(size=13),
        ),
        legend=dict(orientation='h', yanchor='top', y=-0.12, xanchor='center', x=0.5),
        margin=dict(b=120),
    )
    return fig


# ── Streamlit UI ──────────────────────────────────────────────────────────────

st.set_page_config(page_title='Анализ системы оценивания', layout='wide')
st.title('Анализ системы оценивания: Правило A vs Правило B')

# Формула
with st.expander('Формула оценки', expanded=True):
    st.latex(r'S = \alpha \cdot a + \beta \cdot t + \gamma \cdot v')
    st.latex(
        r'\text{Правило A}: S \geq \theta'
        r'\qquad\qquad'
        r'\text{Правило B}: S \geq \theta \;\wedge\; v \geq v_0'
    )
    st.markdown(
        r'где $a$ — посещаемость, $t$ — своевременность (фиксирована), $v$ — вариативный балл; '
        r'$\alpha, \beta, \gamma$ — их веса; $\theta$ — порог зачёта; $v_0$ — порог по правилу B.'
    )

with st.sidebar:
    st.header('Параметры')

    tim = st.selectbox(
        't (своевременность)',
        options=[100, 50, 0],
        format_func=lambda v: {100: 't = 100 (основной срок)', 50: 't = 50 (1-я пересдача)', 0: 't = 0 (2-я пересдача)'}[v],
    )

    st.subheader('Веса')
    w_att_pct = st.slider('α — вес посещаемости (%)', 0, 80, 20, step=5)
    w_var_pct = st.slider('γ — вес вариативного (%)', 20, 100, 60, step=5)
    wt_pct = 100 - w_att_pct - w_var_pct

    if wt_pct < 0:
        st.error(f'α + β + γ > 100%: β = {wt_pct}%. Уменьшите веса.')
        st.stop()
    else:
        st.success(f'α={w_att_pct}%  β={wt_pct}%  γ={w_var_pct}%  (сумма = 100%)')

    st.subheader('Пороги')
    threshold = st.slider('θ — порог зачёта (≥)', 20, 60, 42, step=1)
    var_thresh = st.slider('v₀ — порог правила B (≥)', 10, 60, 42, step=1)

wa = w_att_pct / 100
wt = wt_pct / 100
wv = w_var_pct / 100

att_vals, var_vals, mat_a, mat_b, hover_a, hover_b, diff_pts, n_diff, n_total, pct_diff = compute_matrices(
    wa, wt, wv, tim, threshold, var_thresh
)

fig = build_figure(
    att_vals, var_vals, mat_a, mat_b, hover_a, hover_b,
    diff_pts, threshold, var_thresh, n_diff, n_total, pct_diff,
    w_att_pct, wt_pct, w_var_pct, tim
)
st.plotly_chart(fig, use_container_width=True)

# Statistics
st.subheader(f'Расхождения A \u2260 B при t = {tim}')
col1, col2, col3 = st.columns(3)
col1.metric('Расхождений', f'{n_diff}')
col2.metric('Всего ячеек', f'{n_total}')
col3.metric('Доля', f'{pct_diff:.1f}%')

st.caption(
    f'Студент проходит по A (S \u2265 \u03b8={threshold}), но не по B (v < v\u2080={var_thresh})'
)

# Per-grade loss
lost_by_grade = {e: 0 for e in 'ABCDE'}
for i, att in enumerate(att_vals):
    for j, var in enumerate(var_vals):
        s = calc_score(att, tim, var, wa, wt, wv)
        ects, *_ = get_grade(s)
        if ects != 'F' and rule_a(s, threshold) and not rule_b(s, var, threshold, var_thresh):
            lost_by_grade[ects] += 1

losses = {e: cnt for e, cnt in lost_by_grade.items() if cnt > 0}
if losses:
    st.write('**Потери по оценкам** (проходит по A, теряет по B):')
    st.table({'Оценка ECTS': list(losses.keys()), 'Ячеек': list(losses.values())})
