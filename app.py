import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import ListedColormap
import streamlit as st

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
CMAP = ListedColormap(COLORS_MAP)
GRADE_NUM = {'A': 5, 'B': 4, 'C': 3, 'D': 2, 'E': 1, 'F': 0}

PRESETS = {
    '20+20+60 (стандарт)': (20, 20, 60),
    '15+15+70': (15, 15, 70),
    '10+10+80': (10, 10, 80),
    '25+25+50': (25, 25, 50),
    '30+30+40 (мин. вариат.)': (30, 30, 40),
    '10+30+60': (10, 30, 60),
    '0+40+60 (без посещ.)': (0, 40, 60),
}


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


def build_figure(wa, wt, wv, tim, threshold, var_thresh, w_att_pct, wt_pct, w_var_pct):
    att_vals = np.arange(0, 101, 2)
    var_vals = np.arange(0, 101, 2)

    mat_a = np.zeros((len(att_vals), len(var_vals)))
    mat_b = np.zeros((len(att_vals), len(var_vals)))
    diff_pts = {'x': [], 'y': []}

    for i, att in enumerate(att_vals):
        for j, var in enumerate(var_vals):
            s = calc_score(att, tim, var, wa, wt, wv)
            ects, *_ = get_grade(s)
            gn = GRADE_NUM[ects]
            mat_a[i, j] = gn if rule_a(s, threshold) else 0
            mat_b[i, j] = gn if rule_b(s, var, threshold, var_thresh) else 0
            if rule_a(s, threshold) and not rule_b(s, var, threshold, var_thresh):
                diff_pts['x'].append(var)
                diff_pts['y'].append(att)

    n_diff = len(diff_pts['x'])
    n_total = len(att_vals) * len(var_vals)
    pct_diff = 100 * n_diff / n_total

    fig, axes = plt.subplots(1, 2, figsize=(15, 6))
    ext = [-1, 101, -1, 101]

    titles = [
        f'Правило A  (итог ≥ {threshold})\nПосещ={w_att_pct}% · Своевр={wt_pct}% · Вариат={w_var_pct}%',
        f'Правило B  (итог ≥ {threshold}  И  вариат ≥ {var_thresh})\nРасхождений: {n_diff}/{n_total} ({pct_diff:.1f}%)',
    ]

    for ax, mat, title in zip(axes, [mat_a, mat_b], titles):
        ax.imshow(mat, origin='lower', aspect='auto',
                  cmap=CMAP, vmin=0, vmax=5, extent=ext, interpolation='nearest')
        try:
            ax.contour(var_vals, att_vals, mat,
                       levels=[0.5, 1.5, 2.5, 3.5, 4.5],
                       colors=['#c0392b', '#e07b00', '#1d6fa4', '#40916c', '#2d6a4f'],
                       linewidths=1.2, alpha=0.6)
        except Exception:
            pass

        ax.axvline(var_thresh, color='white', linestyle='--', linewidth=2, alpha=0.8)
        ax.text(var_thresh + 1, 97, f'вар={var_thresh}', color='white',
                fontsize=8.5, va='top', fontweight='bold')
        ax.set_xlabel('Вариативный балл', fontsize=11)
        ax.set_ylabel('Посещаемость', fontsize=11)
        ax.set_title(title, fontweight='bold', fontsize=10.5)
        ax.set_xlim(0, 100)
        ax.set_ylim(0, 100)

    if diff_pts['x']:
        axes[1].scatter(diff_pts['x'], diff_pts['y'],
                        marker='x', color='#c0392b', s=18,
                        linewidths=1.2, label=f'A≠B ({n_diff} точек)', zorder=5, alpha=0.7)
        axes[1].legend(fontsize=9, loc='lower right')

    patches = [
        mpatches.Patch(facecolor=COLORS_MAP[5], edgecolor='#aaa', lw=0.5, label='A — 5 Отл (92–100)'),
        mpatches.Patch(facecolor=COLORS_MAP[4], edgecolor='#aaa', lw=0.5, label='B — 5 Отл (82–91)'),
        mpatches.Patch(facecolor=COLORS_MAP[3], edgecolor='#aaa', lw=0.5, label='C — 4 Хор (62–81)'),
        mpatches.Patch(facecolor=COLORS_MAP[2], edgecolor='#aaa', lw=0.5, label='D — 3 Удов (52–61)'),
        mpatches.Patch(facecolor=COLORS_MAP[1], edgecolor='#aaa', lw=0.5, label='E — 3 Удов (42–51)'),
        mpatches.Patch(facecolor=COLORS_MAP[0], edgecolor='#aaa', lw=0.5, label='F — 2 Неуд (0–41)'),
    ]
    fig.legend(handles=patches, loc='lower center', ncol=6,
               fontsize=9, bbox_to_anchor=(0.5, -0.04))

    plt.suptitle(
        f'Своевр={tim}  ·  Веса: посещ={w_att_pct}% своевр={wt_pct}% вариат={w_var_pct}%'
        f'  ·  Порог зачёта={threshold}',
        fontsize=11, fontweight='bold', y=1.01
    )
    plt.tight_layout()
    return fig, n_diff, n_total, pct_diff, diff_pts, att_vals, var_vals


# ── Streamlit UI ──────────────────────────────────────────────────────────────

st.set_page_config(page_title='Анализ системы оценивания', layout='wide')
st.title('Анализ системы оценивания: A vs B · Тепловые карты')

# Sidebar controls
with st.sidebar:
    st.header('Параметры')

    preset_name = st.selectbox('Пресет весов', list(PRESETS.keys()), index=0)
    preset_wa, preset_wt, preset_wv = PRESETS[preset_name]

    tim = st.selectbox(
        'Своевременность',
        options=[100, 50, 0],
        format_func=lambda v: {100: 'Основной срок (100)', 50: '1-я пересдача (50)', 0: '2-я пересдача (0)'}[v],
    )

    st.subheader('Веса компонентов')
    w_att_pct = st.slider('Вес посещаемости (%)', 0, 80, preset_wa, step=5)
    w_var_pct = st.slider('Вес вариативного (%)', 20, 100, preset_wv, step=5)
    wt_pct = 100 - w_att_pct - w_var_pct

    if wt_pct < 0:
        st.error(f'Сумма весов > 100: своевременность = {wt_pct}%. Уменьшите веса.')
        st.stop()
    else:
        st.success(f'Сумма весов: 100%  (посещ={w_att_pct}%, своевр={wt_pct}%, вариат={w_var_pct}%)')

    st.subheader('Пороги')
    threshold = st.slider('Порог зачёта (≥)', 20, 60, 42, step=1)
    var_thresh = st.slider('Порог вариативного B (≥)', 10, 60, 42, step=1)

# Build and display
wa = w_att_pct / 100
wt = wt_pct / 100
wv = w_var_pct / 100

fig, n_diff, n_total, pct_diff, diff_pts, att_vals, var_vals = build_figure(
    wa, wt, wv, tim, threshold, var_thresh, w_att_pct, wt_pct, w_var_pct
)
st.pyplot(fig)
plt.close(fig)

# Statistics
st.subheader(f'Статистика расхождений A≠B при своевр={tim}')
col1, col2, col3 = st.columns(3)
col1.metric('Расхождений', f'{n_diff}')
col2.metric('Всего ячеек', f'{n_total}')
col3.metric('Доля расхождений', f'{pct_diff:.1f}%')

st.caption(
    f'Смысл: студент проходит по A (итог≥{threshold}), но не по B (вариат<{var_thresh})'
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
    st.write('**Потери по оценкам** (кто получил бы по A, но теряет по B):')
    st.table({'Оценка ECTS': list(losses.keys()), 'Ячеек': list(losses.values())})
