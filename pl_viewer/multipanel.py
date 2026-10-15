"""v1.5: independent PL subplots. Preview geometry is owned by Qt.

Raw acquisitions remain V/nm. Panel settings/annotations are presentation only.
This module deliberately imports no Qt components, allowing headless validation.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from pathlib import Path
from copy import deepcopy
import json
import math

import matplotlib as mpl
from matplotlib.figure import Figure
from matplotlib.transforms import ScaledTranslation
import numpy as np

from .models import Spectrum
from .plotting import (
    PlotSettings, VerticalAnnotation, HorizontalAnnotation, PLOT_COLOR_CYCLE,
    signal_display, scaled_signal, find_spectrum_maximum, wavelength_display,
    format_wavelength, legend_label, validate_factor,
)

LAYOUTS = {"1x1": (1, 1), "1x2": (1, 2), "2x1": (2, 1), "2x2": (2, 2)}


@dataclass
class PanelState:
    uids: list[str] = field(default_factory=list)
    settings: PlotSettings = field(default_factory=PlotSettings)
    annotations: list[VerticalAnnotation | HorizontalAnnotation] = field(default_factory=list)
    grid: bool = True
    legend: bool = True

    def validate(self):
        if len(self.uids) != len(set(self.uids)) or len(self.uids) > 200:
            raise ValueError("IDs repetidos ou excesso de curvas em um painel.")
        if any(not isinstance(uid, str) or not uid or len(uid) > 500 for uid in self.uids):
            raise ValueError("Identificador de série inválido.")
        self.settings.validate()
        if len(self.annotations) > 100:
            raise ValueError("Limite de 100 anotações por painel.")
        for annotation in self.annotations:
            annotation.validate()
        if not isinstance(self.grid, bool) or not isinstance(self.legend, bool):
            raise ValueError("Configuração de grade/legenda inválida.")


@dataclass
class Composition:
    layout: str = "1x2"
    active: int = 0
    panels: list[PanelState] = field(default_factory=lambda: [PanelState() for _ in range(4)])
    share_x: bool = False
    share_y: bool = False
    hspace: float = .34
    wspace: float = .27
    mode: int = 0  # 0 = acquired scaled signal, 2 = normalized

    @property
    def shape(self):
        return LAYOUTS[self.layout]

    @property
    def count(self):
        r, c = self.shape
        return r * c

    def validate(self):
        if not isinstance(self.share_x, bool) or not isinstance(self.share_y, bool):
            raise ValueError("Compartilhamento dos eixos inválido.")
        if self.layout not in LAYOUTS or self.mode not in (0, 2):
            raise ValueError("Layout ou modo de composição desconhecido.")
        if not isinstance(self.active, int) or not 0 <= self.active < 4:
            raise ValueError("Painel ativo inválido.")
        if len(self.panels) != 4:
            raise ValueError("São necessários quatro estados de painel para alternar layouts.")
        for panel in self.panels:
            panel.validate()
        for key in ("hspace", "wspace"):
            value = getattr(self, key)
            if not isinstance(value, (float, int)) or not math.isfinite(value) or not .02 <= value <= .85:
                raise ValueError(f"{key} deve estar entre 0,02 e 0,85.")
        shown = self.panels[:self.count]
        if self.share_x and len({p.settings.x_unit for p in shown}) > 1:
            raise ValueError("Eixo X compartilhado exige a mesma unidade (nm/Å) em todos os painéis.")
        if self.share_y and self.mode == 0 and len({p.settings.y_unit for p in shown}) > 1:
            raise ValueError("Eixo Y compartilhado exige a mesma unidade (V/mV) em todos os painéis.")
        for shared, low, high, axis in (
            (self.share_x, 'x_min', 'x_max', 'X'),
            (self.share_y, 'y_min', 'y_max', 'Y'),
        ):
            if shared:
                for key in (low, high):
                    explicit = {getattr(p.settings, key) for p in shown if getattr(p.settings, key) is not None}
                    if len(explicit) > 1:
                        raise ValueError(f"Limites de {axis} compartilhados conflitantes: ajuste {key} nos painéis.")


def _label_annotation(ax, fig, ann, settings, mode, selected=False):
    width = settings.annotation_line_width * (1.4 if selected else 1)
    if isinstance(ann, VerticalAnnotation):
        x = wavelength_display(ann.wavelength_nm, settings.x_unit)
        ax.axvline(x, color=ann.color, ls=ann.linestyle, lw=width, zorder=3)
        label = ann.text.strip()
        if ann.show_value:
            label += ('\n' if label else '') + format_wavelength(ann.wavelength_nm, settings.x_unit)
        if label:
            trans = ax.get_xaxis_transform() + ScaledTranslation(ann.label_dx_pt / 72., 0, fig.dpi_scale_trans)
            ax.text(x, ann.label_y, label, transform=trans, fontsize=settings.font_annotations,
                    ha='center', va='center', color='#252525', zorder=7,
                    bbox=dict(boxstyle='square,pad=.2', facecolor='white', edgecolor='#d3d3d3', alpha=.93))
    else:
        if (ann.reference_scale == 'normalized') != (mode == 2):
            return
        value = ann.signal_value if mode == 2 else signal_display(ann.signal_value, settings.y_unit)
        ax.axhline(value, color=ann.color, ls=ann.linestyle, lw=width, zorder=3)
        label = ann.text.strip()
        if ann.show_value:
            label += ('\n' if label else '') + (f"Y = {value:.6g} (norm.)" if mode == 2 else f"Y = {value:.6g} {settings.y_unit}")
        if label:
            trans = ax.get_yaxis_transform() + ScaledTranslation(0, ann.label_dy_pt / 72., fig.dpi_scale_trans)
            ax.text(ann.label_x, value, label, transform=trans, fontsize=settings.font_annotations,
                    ha='center', va='center', color='#252525', zorder=7,
                    bbox=dict(boxstyle='square,pad=.2', facecolor='white', edgecolor='#d3d3d3', alpha=.93))


def render_composition(figure: Figure, spectra_by_uid: dict[str, Spectrum], composition: Composition,
                       *, display_factors: dict[str, float] | None = None, peak_uid: str | None = None,
                       resize_figure: bool = False, selected_annotation: int | None = None):
    """Draw all panels on an existing Figure. In Qt, resize_figure MUST be False.

    Returns axes in row-major order. Display scaling affects no acquisition arrays.
    """
    composition.validate()
    factors = display_factors or {}
    for f in factors.values():
        validate_factor(f)
    first = composition.panels[0].settings
    if resize_figure:
        figure.set_size_inches(first.figure_width_in, first.figure_height_in, forward=False)
    figure.clear()
    rows, cols = composition.shape
    with mpl.rc_context({'font.family': first.font_family, 'axes.edgecolor': '#222222',
                         'axes.linewidth': .75, 'savefig.facecolor': 'white'}):
        axes = list(figure.subplots(rows, cols, sharex=composition.share_x,
                                   sharey=composition.share_y, squeeze=False).flat)
        # Independent margins are a *figure-level* setting; use first panel's margins.
        any_header = any((p.settings.show_title and p.settings.title.strip()) or
                         (p.settings.show_subtitle and p.settings.subtitle.strip())
                         for p in composition.panels[:composition.count])
        footer_visible = first.show_footer and bool(first.footer.strip())
        figure.subplots_adjust(left=first.margin_left, right=first.margin_right,
                               bottom=(first.margin_bottom if footer_visible else max(.08, first.margin_bottom-.09)),
                               top=(first.margin_top if any_header else min(.96, first.margin_top+.08)),
                               hspace=composition.hspace, wspace=composition.wspace)
        for i, (ax, panel) in enumerate(zip(axes, composition.panels)):
            if i >= composition.count:
                break
            s = panel.settings
            ax.set_facecolor('white')
            ax.grid(panel.grid, color='#89909a', lw=s.grid_line_width, alpha=s.grid_alpha)
            ax.tick_params(colors='#202020', labelsize=s.font_ticks)
            drawn = []
            for rank, uid in enumerate(panel.uids):
                sp = spectra_by_uid.get(uid)
                if sp is None:
                    continue
                f = validate_factor(factors.get(uid, 1))
                x = wavelength_display(np.asarray(sp.wavelength_nm), s.x_unit)
                y = scaled_signal(sp, f)
                if composition.mode == 2:
                    denom = float(np.max(np.abs(y)))
                    if not denom:
                        continue
                    y = y / denom
                else:
                    y = signal_display(y, s.y_unit)
                (curve,) = ax.plot(x, y, color=PLOT_COLOR_CYCLE[rank % len(PLOT_COLOR_CYCLE)],
                                   lw=s.line_width, ls=s.line_style, label=legend_label(sp, s.legend_fields, f))
                drawn.append(sp)
                if uid == peak_uid:
                    peak = find_spectrum_maximum(sp, f)
                    if peak.tied_points == 1:
                        xp = wavelength_display(peak.wavelength_nm, s.x_unit)
                        yp = float(y[peak.index])
                        ax.plot([xp], [yp], marker='o', ms=7, mec=curve.get_color(),
                                mfc='white', mew=1.6, ls='none', zorder=9)
                        ax.annotate(f"Máximo: {yp:.5g} {'norm.' if composition.mode == 2 else s.y_unit}\n"
                                    f"λ = {format_wavelength(peak.wavelength_nm, s.x_unit)}",
                                    xy=(xp, yp), xytext=(12, 20), textcoords='offset points',
                                    fontsize=s.font_annotations, zorder=10,
                                    arrowprops={'arrowstyle':'-', 'color':curve.get_color()},
                                    bbox={'fc':'white','ec':'#aaa','alpha':.94,'boxstyle':'round,pad=.2'})
            if not drawn:
                ax.text(.5, .5, 'Sem curvas neste painel', transform=ax.transAxes,
                        ha='center', va='center', fontsize=10, color='#777777')
            if s.show_title and s.title:
                ax.set_title(f"({chr(97+i)}) {s.title}", loc='left', fontsize=s.font_title,
                             fontweight='semibold', pad=8)
            if s.show_subtitle and s.subtitle:
                ax.text(0, 1.015, s.subtitle, transform=ax.transAxes, ha='left', va='bottom',
                        fontsize=s.font_subtitle, color='#555555')
            if (not composition.share_x or i // cols == rows-1):
                ax.set_xlabel(f"{s.x_label} ({'Å' if s.x_unit == 'angstrom' else 'nm'})", fontsize=s.font_axes)
            if (not composition.share_y or i % cols == 0):
                ylabel = 'Sinal relativo (normalizado)' if composition.mode == 2 else f"{s.y_label} ({s.y_unit})"
                ax.set_ylabel(ylabel, fontsize=s.font_axes)
            if panel.legend and drawn:
                ax.legend(loc=s.legend_location, fontsize=s.font_legend,
                          ncol=s.legend_columns, frameon=s.legend_frame)
            for index, ann in enumerate(panel.annotations):
                _label_annotation(ax, figure, ann, s, composition.mode,
                                  selected=(i == composition.active and index == selected_annotation))
            if not composition.share_x:
                if s.x_min is not None or s.x_max is not None:
                    ax.set_xlim(left=s.x_min, right=s.x_max)
            if not composition.share_y:
                if s.y_min is not None or s.y_max is not None:
                    ax.set_ylim(bottom=s.y_min, top=s.y_max)
        if composition.share_x:
            lo = next((p.settings.x_min for p in composition.panels[:composition.count] if p.settings.x_min is not None), None)
            hi = next((p.settings.x_max for p in composition.panels[:composition.count] if p.settings.x_max is not None), None)
            if lo is not None or hi is not None:
                axes[0].set_xlim(left=lo, right=hi)
        if composition.share_y:
            lo = next((p.settings.y_min for p in composition.panels[:composition.count] if p.settings.y_min is not None), None)
            hi = next((p.settings.y_max for p in composition.panels[:composition.count] if p.settings.y_max is not None), None)
            if lo is not None or hi is not None:
                axes[0].set_ylim(bottom=lo, top=hi)
        if footer_visible:
            figure.text(.5, .04, first.footer, ha='center', va='center',
                        fontsize=first.font_footer, color='#555555', wrap=True)
    return axes


def create_composition_export_figure(spectra_by_uid, composition, *, display_factors=None, peak_uid=None):
    """Separate publication figure; never overwrite the embedded Qt canvas size."""
    s = composition.panels[0].settings
    result = Figure(figsize=(s.figure_width_in, s.figure_height_in), dpi=100)
    render_composition(result, spectra_by_uid, composition, display_factors=display_factors,
                       peak_uid=peak_uid, resize_figure=False)
    return result


def composition_to_dict(composition: Composition):
    composition.validate()
    result = asdict(composition)
    for panel_out, panel in zip(result['panels'], composition.panels):
        panel_out['annotations'] = [dict(asdict(a), orientation=('vertical' if isinstance(a, VerticalAnnotation)
                                                          else 'horizontal')) for a in panel.annotations]
    return result


def composition_from_dict(data: dict) -> Composition:
    if not isinstance(data, dict):
        raise ValueError('Composição inválida.')
    raw = dict(data)
    panels = raw.pop('panels')
    if not isinstance(panels, list) or len(panels) != 4:
        raise ValueError('A sessão deve conter os quatro painéis.')
    parsed = []
    for item in panels:
        item = dict(item)
        settings = PlotSettings(**item.pop('settings'))
        annotations = []
        for entry in item.pop('annotations', []):
            mark = dict(entry)
            orientation = mark.pop('orientation')
            if orientation == 'vertical':
                annotations.append(VerticalAnnotation(**mark))
            elif orientation == 'horizontal':
                annotations.append(HorizontalAnnotation(**mark))
            else:
                raise ValueError('Tipo de anotação de painel inválido.')
        parsed.append(PanelState(settings=settings, annotations=annotations, **item))
    comp = Composition(panels=parsed, **raw)
    comp.validate()
    return comp


def augment_session_json(path: str | Path, composition: Composition, enabled: bool):
    """Extend original /v1 JSON (readable by older versions, which ignore extra fields)."""
    path = Path(path)
    obj = json.loads(path.read_text(encoding='utf-8'))
    obj['multipanel_v15'] = {'enabled': bool(enabled), 'composition': composition_to_dict(composition)}
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding='utf-8')


def restore_composition_from_session(data: dict):
    extra = data.get('multipanel_v15')
    if not extra:
        return None
    return bool(extra['enabled']), composition_from_dict(extra['composition'])
