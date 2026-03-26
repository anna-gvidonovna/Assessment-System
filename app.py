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
            row_a.append(f'M_посещ={att}, M_вар={var}<br>G_итог={s} → {grade_a} ({ru})')
            row_b.append(f'M_посещ={att}, M_вар={var}<br>G_итог={s} → {grade_b} ({ru})')

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
                 diff_pts, threshold, var_thresh, n_diff, pct_diff,
                 w_att_pct, wt_pct, w_var_pct, tim):

    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=[
            f'Правило A:  G_итог ≥ θ={threshold}',
            f'Правило B:  G_итог ≥ θ={threshold}  ∧  M_вар ≥ v₀={var_thresh}',
        ],
        horizontal_spacing=0.10,
    )

    common = dict(
        x=var_vals, y=att_vals,
        colorscale=GRADE_COLORSCALE,
        zmin=-0.5, zmax=5.5,
        showscale=False,
        hovertemplate='%{hovertext}<extra></extra>',
    )

    fig.add_trace(go.Heatmap(
        z=mat_a, hovertext=hover_a, name='Правило A', showlegend=False, **common
    ), row=1, col=1)

    fig.add_trace(go.Heatmap(
        z=mat_b, hovertext=hover_b, name='Правило B', showlegend=False, **common
    ), row=1, col=2)

    if diff_pts['x']:
        fig.add_trace(go.Scatter(
            x=diff_pts['x'], y=diff_pts['y'],
            mode='markers',
            marker=dict(symbol='circle', color='#c0392b', size=4, opacity=0.50),
            name=f'A≠B  ({n_diff} ячеек, {pct_diff:.1f}%)',
            hovertemplate='M_посещ=%{y}, M_вар=%{x}<extra>A≠B</extra>',
        ), row=1, col=2)

    for col in (1, 2):
        fig.add_vline(x=var_thresh, line_dash='dash', line_color='white',
                      line_width=2, col=col, row=1)

    grade_legend = [
        ('A — 5 Отл  (92–100)', COLORS_MAP[5]),
        ('B — 5 Отл  (82–91)',  COLORS_MAP[4]),
        ('C — 4 Хор  (62–81)',  COLORS_MAP[3]),
        ('D — 3 Удов (52–61)', COLORS_MAP[2]),
        ('E — 3 Удов (42–51)', COLORS_MAP[1]),
        ('F — 2 Неуд (0–41)',   COLORS_MAP[0]),
    ]
    for label, color in grade_legend:
        fig.add_trace(go.Scatter(
            x=[None], y=[None], mode='markers',
            marker=dict(size=14, color=color, symbol='square',
                        line=dict(color='#888', width=1)),
            name=label, showlegend=True,
        ))

    fig.update_xaxes(title_text='M_вар — вариативный балл', range=[0, 100], showgrid=False)
    fig.update_yaxes(title_text='M_посещ — посещаемость', range=[0, 100], showgrid=False)
    fig.update_layout(
        height=580,
        title=dict(
            text=(f'w_посещ={w_att_pct}%  w_своевр={wt_pct}%  w_вар={w_var_pct}%'
                  f'  ·  M_своевр={tim}  ·  θ={threshold}  ·  v₀={var_thresh}'),
            font=dict(size=13, color='#555'),
            x=0.0,
            xanchor='left',
        ),
        legend=dict(
            orientation='v',
            yanchor='middle', y=0.5,
            xanchor='left',   x=1.02,
            bgcolor='rgba(255,255,255,0.85)',
            bordercolor='#ccc',
            borderwidth=1,
            font=dict(size=12),
            tracegroupgap=4,
        ),
        margin=dict(l=60, r=200, t=80, b=60),
        plot_bgcolor='#fafafa',
        paper_bgcolor='#ffffff',
    )
    return fig


# ── Streamlit UI ──────────────────────────────────────────────────────────────

st.set_page_config(page_title='Анализ системы оценивания', layout='wide')
st.title('Анализ системы оценивания: Правило A vs Правило B')

with st.sidebar:
    st.header('Параметры')

    tim = st.selectbox(
        'M_своевр — своевременность аттестации',
        options=[100, 50, 0],
        format_func=lambda v: {
            100: 'M_своевр = 100 (основной срок)',
            50:  'M_своевр = 50  (1-я пересдача)',
            0:   'M_своевр = 0   (2-я пересдача)',
        }[v],
    )

    st.subheader('Веса компонентов')
    w_att_pct = st.slider('w_посещ — посещаемость (%)', 0, 80, 20, step=5)
    w_var_pct = st.slider('w_вар — вариативный (%)',    20, 100, 60, step=5)
    wt_pct = 100 - w_att_pct - w_var_pct

    if wt_pct < 0:
        st.error(f'w_посещ + w_своевр + w_вар > 100 %:  w_своевр = {wt_pct} %. Уменьшите веса.')
        st.stop()
    else:
        st.info(
            f'w_посещ = {w_att_pct} %  ·  w_своевр = {wt_pct} %  ·  w_вар = {w_var_pct} %'
            f'  →  сумма = 100 %'
        )

    st.subheader('Пороги')
    threshold = st.slider('θ — порог зачёта (G_итог ≥)', 20, 60, 42, step=1)
    var_thresh = st.slider('v₀ — порог правила B (M_вар ≥)', 10, 60, 42, step=1)

wa = w_att_pct / 100
wt = wt_pct / 100
wv = w_var_pct / 100

att_vals, var_vals, mat_a, mat_b, hover_a, hover_b, diff_pts, n_diff, n_total, pct_diff = compute_matrices(
    wa, wt, wv, tim, threshold, var_thresh
)

fig = build_figure(
    att_vals, var_vals, mat_a, mat_b, hover_a, hover_b,
    diff_pts, threshold, var_thresh, n_diff, pct_diff,
    w_att_pct, wt_pct, w_var_pct, tim
)

# ── Графики — первыми ─────────────────────────────────────────────────────────
st.plotly_chart(fig, use_container_width=True)

# ── Статистика расхождений ────────────────────────────────────────────────────
st.subheader(f'Расхождения A ≠ B при M_своевр = {tim}')
col1, col2, col3 = st.columns(3)
col1.metric('Расхождений', f'{n_diff}')
col2.metric('Всего ячеек', f'{n_total}')
col3.metric('Доля', f'{pct_diff:.1f} %')
st.caption(
    f'Студент проходит по правилу A (G_итог ≥ θ={threshold}), '
    f'но не по B (M_вар < v₀={var_thresh})'
)

# ── Потери по оценкам ─────────────────────────────────────────────────────────
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

# ── Формулы ───────────────────────────────────────────────────────────────────
with st.expander('Формулы системы оценивания', expanded=False):
    st.markdown('#### Итоговая оценка — формула взвешенной суммы')
    st.latex(r'''
        G_{\text{итог}} = \mathrm{round}\!\left(\sum_{i=1}^{n} w_i \cdot M_i\right),
        \qquad \sum_{i=1}^{n} w_i = 1
    ''')
    st.markdown(
        r'$G_{\text{итог}}$ — итоговая оценка, округлённая до целого;  '
        r'$M_i$ — оценка за $i$-й компонент контроля (0–100);  '
        r'$w_i$ — вес $i$-го компонента контроля.'
    )

    st.divider()
    st.markdown('#### Академическая активность  (фиксированный вес **0.4 = 40 %**)')

    st.markdown('**Посещаемость** — $w_{\\text{посещаемость}} = 20\\%$')
    st.latex(r'''
        M_{\text{посещаемость}} = \frac{n_{\text{посещено}}}{n_{\text{занятий}}} \times 100
    ''')
    st.markdown(
        r'$n_{\text{посещено}}$ — количество посещённых студентом занятий;  '
        r'$n_{\text{занятий}}$ — общее число занятий по курсу.'
    )

    st.markdown('**Своевременность аттестации** — $w_{\\text{своевременность}} = 20\\%$')
    st.latex(r'''
        M_{\text{своевременность}} = \begin{cases}
            100, & \text{промежуточная аттестация пройдена в основной срок} \\
            50,  & \text{в первую пересдачу} \\
            0,   & \text{во вторую пересдачу}
        \end{cases}
    ''')

    st.divider()
    st.markdown('#### Вариативная часть  (совокупный вес **0.6 = 60 %**)')
    st.markdown(
        'Состав, количество компонентов и их веса определяются преподавателем и/или школой.'
    )

    st.divider()
    st.markdown('#### Итоговый балл в данной модели')
    st.latex(r'''
        G_{\text{итог}} = \mathrm{round}\!\bigl(
            w_{\text{посещаемость}} \cdot M_{\text{посещаемость}}
            + w_{\text{своевременность}} \cdot M_{\text{своевременность}}
            + w_{\text{вар}} \cdot M_{\text{вар}}
        \bigr)
    ''')

    st.divider()
    st.markdown('#### Правила зачёта')
    st.latex(
        r'\text{Правило A:}\quad G_{\text{итог}} \geq \theta'
        r'\qquad\qquad'
        r'\text{Правило B:}\quad G_{\text{итог}} \geq \theta \;\wedge\; M_{\text{вар}} \geq v_0'
    )
