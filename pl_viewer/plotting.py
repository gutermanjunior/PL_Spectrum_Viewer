"""Scientific PL plots and annotations, independent from Qt.

Internal units: wavelength nm, acquired lock-in signal V.
Display/output can use nm/Å and V/mV; multiplying a curve does not mutate measurements.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
import json
import math
from pathlib import Path
from typing import Iterable

import matplotlib as mpl
from matplotlib.figure import Figure
from matplotlib.transforms import ScaledTranslation
import numpy as np

from .models import Spectrum

COLOR_OPTIONS = {
    "Cinza": "#687180", "Preto": "#252b37", "Vermelho": "#d14343",
    "Azul": "#2458b4", "Verde": "#26864b", "Roxo": "#894bba",
}
LINE_OPTIONS = {"Pontilhada": ":", "Tracejada": "--", "Contínua": "-", "Traço-ponto": "-."}
# Fixed Matplotlib Tableau cycle. Each spectrum receives a color from its
# chronological selection position, INCLUDING in separate-subplot mode.
PLOT_COLOR_CYCLE = (
    "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
    "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf",
)


@dataclass
class VerticalAnnotation:
    wavelength_nm: float
    text: str = ""
    color: str = "#687180"
    linestyle: str = ":"
    label_y: float = 0.76  # fraction of axes height (not calibrated signal)
    label_dx_pt: float = 0.0  # visual label displacement in typographic points; line stays fixed
    show_value: bool = True

    def validate(self):
        if not (math.isfinite(self.wavelength_nm) and self.wavelength_nm > 0):
            raise ValueError("Comprimento de onda da anotação deve ser positivo e finito.")
        if not (math.isfinite(self.label_y) and 0.06 <= self.label_y <= 0.96):
            raise ValueError("Posição vertical deve estar entre 6% e 96%.")
        if not (math.isfinite(self.label_dx_pt) and -240 <= self.label_dx_pt <= 240):
            raise ValueError("Deslocamento horizontal deve estar entre -240 e +240 pt.")
        if self.linestyle not in LINE_OPTIONS.values():
            raise ValueError("Estilo de linha desconhecido.")
        if self.color not in COLOR_OPTIONS.values():
            raise ValueError("Cor de linha desconhecida.")
        if len(self.text) > 200:
            raise ValueError("Anotação limitada a 200 caracteres.")


@dataclass
class HorizontalAnnotation:
    """Reference at a plotted Y-value, in the CURRENT displayed Y-scale.

    In normalized mode it refers to normalized signal; with ×f it refers to
    the multiplied (displayed) signal. It never implies lock-in calibration.
    """
    signal_value: float
    text: str = ""
    color: str = "#687180"
    linestyle: str = ":"
    label_x: float = 0.76  # horizontal fraction of plot area (independent of x unit)
    label_dy_pt: float = 0.0  # vertical text offset; reference line remains fixed
    show_value: bool = True
    reference_scale: str = "signal_v"  # older sessions: Y stored in V; normalized separate

    def validate(self):
        if self.reference_scale not in ("signal_v", "normalized"):
            raise ValueError("Escala da anotação horizontal desconhecida.")
        if not math.isfinite(self.signal_value):
            raise ValueError("Valor Y da linha horizontal deve ser finito.")
        if not (math.isfinite(self.label_x) and 0.06 <= self.label_x <= 0.96):
            raise ValueError("Posição horizontal do rótulo deve estar entre 6% e 96%.")
        if not (math.isfinite(self.label_dy_pt) and -240 <= self.label_dy_pt <= 240):
            raise ValueError("Deslocamento vertical deve estar entre -240 e +240 pt.")
        if self.linestyle not in LINE_OPTIONS.values() or self.color not in COLOR_OPTIONS.values():
            raise ValueError("Cor ou estilo de linha desconhecidos.")
        if len(self.text) > 200:
            raise ValueError("Anotação limitada a 200 caracteres.")


LEGEND_FIELDS = {
    "sample": "Amostra (com código auxiliar)",
    "slit": "Fendas de entrada e saída (µm)",
    "temperature": "Temperatura indicada no nome (K)",
    "lockin": "Fundo de escala do lock-in (mV)",
    "date": "Data e horário indicados",
    "factor": "Fator multiplicativo ×f",
    "filename": "Nome completo do arquivo",
}
FONT_FAMILIES = ("DejaVu Sans", "DejaVu Serif", "Liberation Sans", "Liberation Serif", "STIXGeneral")
LEGEND_LOCATIONS = ("upper right", "upper left", "lower right", "lower left", "best",
                    "center right", "center left", "upper center", "lower center")


@dataclass
class PlotSettings:
    title: str = "Espectros de fotoluminescência"
    subtitle: str = ""
    show_title: bool = True
    show_subtitle: bool = True
    show_footer: bool = True
    x_label: str = "Comprimento de onda"
    y_label: str = "Sinal do lock-in"
    footer: str = "Dados experimentais; fatores ×f são apenas transformações de exibição."
    x_unit: str = "nm"
    y_unit: str = "V"  # A aquisição guarda valores em V. Exibição em mV = 1000 × V.
    x_min: float | None = None
    x_max: float | None = None
    y_min: float | None = None
    y_max: float | None = None
    line_width: float = 1.8
    line_style: str = "-"
    annotation_line_width: float = 1.25
    figure_width_in: float = 13.5
    figure_height_in: float = 7.7
    font_family: str = "DejaVu Sans"
    font_title: float = 17.5
    font_subtitle: float = 10.3
    font_axes: float = 12.0
    font_ticks: float = 10.0
    font_legend: float = 10.0
    font_annotations: float = 9.3
    font_footer: float = 9.3
    legend_fields: list[str] = field(default_factory=lambda: ["sample", "slit", "lockin", "factor"])
    legend_location: str = "upper right"
    legend_columns: int = 1
    legend_frame: bool = False
    grid_alpha: float = .16
    grid_line_width: float = .8
    margin_left: float = .105
    margin_right: float = .975
    margin_bottom: float = .18
    margin_top: float = .87
    subplot_hspace: float = .27
    subplot_wspace: float = .27

    def validate(self):
        for flag in ("show_title", "show_subtitle", "show_footer"):
            if not isinstance(getattr(self, flag), bool):
                raise ValueError(f"A opção {flag} deve ser ligada ou desligada.")
        if self.x_unit not in ("nm", "angstrom"):
            raise ValueError("Unidade de comprimento de onda não suportada.")
        if self.y_unit not in ("V", "mV"):
            raise ValueError("Unidade de sinal não suportada; escolha V ou mV.")
        if self.font_family not in FONT_FAMILIES:
            raise ValueError("Família de fonte não suportada.")
        if self.legend_location not in LEGEND_LOCATIONS:
            raise ValueError("Posição da legenda não suportada.")
        if self.line_style not in LINE_OPTIONS.values():
            raise ValueError("Estilo de curva não suportado.")
        if (not isinstance(self.legend_fields, list) or len(self.legend_fields) != len(set(self.legend_fields))
                or any(f not in LEGEND_FIELDS for f in self.legend_fields)):
            raise ValueError("Campos da legenda desconhecidos ou repetidos.")
        for name in ("title", "subtitle", "x_label", "y_label", "footer"):
            if not isinstance(getattr(self, name), str) or len(getattr(self, name)) > 500:
                raise ValueError(f"Campo {name} inválido.")
        for key in ("x_min", "x_max", "y_min", "y_max"):
            val = getattr(self, key)
            if val is not None and not math.isfinite(val):
                raise ValueError(f"Limite {key} não finito.")
        if self.x_min is not None and self.x_max is not None and self.x_min >= self.x_max:
            raise ValueError("O mínimo de X deve ser menor que o máximo de X.")
        if self.y_min is not None and self.y_max is not None and self.y_min >= self.y_max:
            raise ValueError("O mínimo de Y deve ser menor que o máximo de Y.")
        ranges = {
            "line_width": (.35, 8), "annotation_line_width": (.4, 5),
            "figure_width_in": (5, 24), "figure_height_in": (3.5, 16),
            "font_title": (8, 36), "font_subtitle": (7, 28),
            "font_axes": (7, 28), "font_ticks": (6, 24),
            "font_legend": (6, 24), "font_annotations": (6, 24),
            "font_footer": (6, 22), "grid_alpha": (0, 1),
            "grid_line_width": (.2, 3), "subplot_hspace": (.02, .85),
            "subplot_wspace": (.02, .85),
            "margin_left": (.04, .45), "margin_right": (.55, .99),
            "margin_bottom": (.07, .38), "margin_top": (.65, .91),
        }
        for key, (lo, hi) in ranges.items():
            val = getattr(self, key)
            if not isinstance(val, (int, float)) or not math.isfinite(val) or not lo <= val <= hi:
                raise ValueError(f"{key} deve estar entre {lo} e {hi}.")
        if self.margin_right - self.margin_left < .3 or self.margin_top - self.margin_bottom < .3:
            raise ValueError("Margens muito próximas: pouca área útil para os dados.")
        if not isinstance(self.legend_columns, int) or not 1 <= self.legend_columns <= 4:
            raise ValueError("Número de colunas da legenda deve estar entre 1 e 4.")


def signal_display(value_v: float | np.ndarray, unit: str) -> float | np.ndarray:
    if unit not in ("V", "mV"):
        raise ValueError("Unidade de sinal desconhecida.")
    return value_v * (1000.0 if unit == "mV" else 1.0)


def signal_v_from_display(value: float, unit: str) -> float:
    if unit not in ("V", "mV"):
        raise ValueError("Unidade de sinal desconhecida.")
    return value / (1000.0 if unit == "mV" else 1.0)


def legend_label(sp: Spectrum, fields: list[str] | None = None, factor: float = 1.) -> str:
    selected = ["sample", "slit", "lockin", "factor"] if fields is None else fields
    parts = []
    for key in selected:
        if key == "sample" and sp.sample and sp.sample != "Não identificada":
            parts.append(f"#{sp.sample_display}" if sp.sample.upper() != "ITA" else "ITA")
        elif key == "slit" and sp.slit_filename_um is not None:
            parts.append(f"{sp.slit_filename_um:g} µm")
        elif key == "temperature" and sp.temperature_filename_k is not None:
            parts.append(f"{sp.temperature_filename_k:g} K (nome)")
        elif key == "lockin" and sp.lockin_range_mv is not None:
            parts.append(f"{sp.lockin_range_mv:g} mV (escala)")
        elif key == "date" and sp.date_label:
            parts.append(sp.date_label)
        elif key == "factor" and factor != 1:
            parts.append(f"×{factor:g}")
        elif key == "filename":
            parts.append(sp.name)
    return "  •  ".join(parts) if parts else sp.name


def wavelength_display(wavelength_nm: float, unit: str) -> float:
    return wavelength_nm * (10 if unit == "angstrom" else 1)


def wavelength_nm_from_display(value: float, unit: str) -> float:
    return value / (10 if unit == "angstrom" else 1)


def format_wavelength(wavelength_nm: float, unit: str) -> str:
    value = wavelength_display(wavelength_nm, unit)
    return f"{value:.4f}".rstrip("0").rstrip(".") + (" Å" if unit == "angstrom" else " nm")


def validate_factor(value: float) -> float:
    """Validate a finite, bounded dimensionless display multiplier."""
    try:
        factor = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("O fator deve ser numérico.") from exc
    if not math.isfinite(factor) or abs(factor) > 1e6:
        raise ValueError("O fator deve ser finito e estar entre −1 000 000 e +1 000 000.")
    return factor


def scaled_signal(sp: Spectrum, factor: float = 1.0) -> np.ndarray:
    """New, non-mutating array for viewing/export; never overwrites acquired signal."""
    factor = validate_factor(factor)
    with np.errstate(over="ignore", invalid="ignore"):
        result = np.asarray(sp.signal, dtype=float) * factor
    if not np.all(np.isfinite(result)):
        raise ValueError("Multiplicação produziu valores não finitos; escolha um fator menor.")
    return result


@dataclass(frozen=True)
class PeakResult:
    wavelength_nm: float
    scaled_value: float
    raw_value_at_peak: float
    original_peak_value: float
    original_peak_wavelength_nm: float
    factor: float
    index: int
    tied_points: int


def find_spectrum_maximum(sp: Spectrum, factor: float = 1.0) -> PeakResult:
    """Discrete global maximum of acquired points AFTER display scaling.

    No fitting, interpolation, baseline subtraction or range restriction is applied.
    For ties, the FIRST acquired point is returned and the tie count is reported.
    """
    x = np.asarray(sp.wavelength_nm, dtype=float)
    y = np.asarray(sp.signal, dtype=float)
    if len(x) != len(y) or not len(x):
        raise ValueError("Espectro vazio ou com comprimentos de onda inconsistentes.")
    if not np.all(np.isfinite(x)) or not np.all(np.isfinite(y)):
        raise ValueError("Dados não finitos impedem a localização do máximo.")
    factor = validate_factor(factor)
    scaled = scaled_signal(sp, factor)
    idx = int(np.argmax(scaled))
    raw_idx = int(np.argmax(y))
    return PeakResult(
        wavelength_nm=float(x[idx]), scaled_value=float(scaled[idx]),
        raw_value_at_peak=float(y[idx]), original_peak_value=float(y[raw_idx]),
        original_peak_wavelength_nm=float(x[raw_idx]), factor=factor,
        index=idx, tied_points=int(np.count_nonzero(scaled == scaled[idx])),
    )


def _legend_label(sp: Spectrum) -> str:
    """Compatibility helper for callers of older versions."""
    return legend_label(sp)


def render_plot(
    figure: Figure,
    spectra: Iterable[Spectrum],
    settings: PlotSettings,
    annotations: Iterable[VerticalAnnotation | HorizontalAnnotation] = (),
    *,
    mode: int = 0,
    grid: bool = True,
    legend: bool = True,
    selected_annotation: int | None = None,
    scale_factors: dict[str, float] | None = None,
    highlight_peak_uid: str | None = None,
    resize_figure: bool = True,
):
    """Render onto an existing Matplotlib Figure. Return the list of axes.

    mode: 0=original overlay; 1=original individual; 2=maximum-normalized overlay.
    These are DISPLAY transformations only; acquired data are untouched.
    """
    settings.validate()
    annotations = list(annotations)
    for item in annotations:
        item.validate()
    spectra = list(spectra)
    scale_factors = scale_factors or {}
    for sp in spectra:
        validate_factor(scale_factors.get(sp.uid, 1.0))
    if mode not in (0, 1, 2):
        raise ValueError("Modo de gráfico desconhecido.")
    if mode == 1:
        spectra = spectra[:16]

    # Export figures use their configured physical dimensions.  Embedded Qt
    # canvases MUST retain the dimensions assigned by their layout/resizeEvent:
    # forcing a large inch size here desynchronizes the canvas and QSplitter.
    if resize_figure:
        figure.set_size_inches(settings.figure_width_in, settings.figure_height_in, forward=False)
    figure.clear()
    if not spectra:
        ax = figure.add_subplot(111)
        ax.text(.5, .5, "Marque espectros na tabela para visualizar", ha="center", va="center", transform=ax.transAxes)
        ax.set_axis_off()
        return [ax]

    # Layout reacts to omitted title/subtitle/footer, not just their visibility.
    title_visible = settings.show_title and bool(settings.title.strip())
    subtitle_visible = settings.show_subtitle and bool(settings.subtitle.strip())
    footer_visible = settings.show_footer and bool(settings.footer.strip())
    top_margin = min(.975, settings.margin_top +
                     (.051 if not title_visible else 0) + (.038 if not subtitle_visible else 0))
    bottom_margin = max(.072, settings.margin_bottom - (.092 if not footer_visible else 0))
    with mpl.rc_context({"font.family": settings.font_family, "axes.linewidth": .75,
                         "axes.edgecolor": "#202020", "savefig.facecolor": "white"}):
        if mode == 1:
            axes = list(figure.subplots(len(spectra), 1, sharex=True, squeeze=False).flat)
            figure.subplots_adjust(top=top_margin, bottom=bottom_margin,
                                   left=settings.margin_left, right=settings.margin_right,
                                   hspace=settings.subplot_hspace)
        else:
            axes = [figure.add_subplot(111)]
            figure.subplots_adjust(top=top_margin, bottom=bottom_margin,
                                   left=settings.margin_left, right=settings.margin_right)

        for index, sp in enumerate(spectra):
            ax = axes[index] if mode == 1 else axes[0]
            x = wavelength_display(np.asarray(sp.wavelength_nm), settings.x_unit)
            factor = validate_factor(scale_factors.get(sp.uid, 1.0))
            displayed_signal = scaled_signal(sp, factor)
            if mode == 2:
                maximum = float(np.max(np.abs(displayed_signal)))
                if not maximum:
                    continue  # zero curve cannot be normalized
                y = displayed_signal / maximum
            else:
                y = signal_display(displayed_signal, settings.y_unit)
            curve_label = legend_label(sp, settings.legend_fields, factor)
            (line,) = ax.plot(x, y, lw=settings.line_width, linestyle=settings.line_style,
                              label=curve_label, color=PLOT_COLOR_CYCLE[index % len(PLOT_COLOR_CYCLE)],
                              antialiased=True)
            if sp.uid == highlight_peak_uid:
                peak = find_spectrum_maximum(sp, factor)
                if peak.tied_points == 1:
                    xpos = wavelength_display(peak.wavelength_nm, settings.x_unit)
                    ypos = float(y[peak.index])
                    ax.plot([xpos], [ypos], linestyle="none", marker="o", markersize=8,
                            markerfacecolor="white", markeredgecolor=line.get_color(),
                            markeredgewidth=2, zorder=9, label="_nolegend_")
                    val = (f"{ypos:.6g} (norm.)" if mode == 2 else f"{ypos:.6g} {settings.y_unit}")
                    ax.annotate(f"Máximo: {val}\nλ = {format_wavelength(peak.wavelength_nm, settings.x_unit)}",
                                xy=(xpos, ypos), xytext=(16, 25), textcoords="offset points",
                                fontsize=settings.font_annotations, color="#222222", zorder=10,
                                arrowprops={"arrowstyle": "-", "color": line.get_color(), "lw": 1.1},
                                bbox={"boxstyle": "round,pad=0.25", "fc": "white", "ec": "#aaaaaa", "alpha": .95})
            ax.set_facecolor("white")
            ax.grid(grid, color="#89909a", alpha=settings.grid_alpha,
                    linewidth=settings.grid_line_width)
            ax.tick_params(labelsize=settings.font_ticks, colors="#171717")
            if mode == 1:
                ax.set_ylabel(f"{settings.y_label} ({settings.y_unit})", fontsize=settings.font_axes)
                ax.set_title(curve_label, loc="left", fontsize=settings.font_legend)
        axes[-1].set_xlabel(f"{settings.x_label} ({'Å' if settings.x_unit == 'angstrom' else 'nm'})",
                            fontsize=settings.font_axes)
        if mode != 1:
            axes[0].set_ylabel("Sinal relativo (normalizado)" if mode == 2
                               else f"{settings.y_label} ({settings.y_unit})", fontsize=settings.font_axes)
            if legend:
                axes[0].legend(loc=settings.legend_location, frameon=settings.legend_frame,
                               fontsize=settings.font_legend, ncol=settings.legend_columns)

        if highlight_peak_uid is not None and settings.y_max is None:
            for ax in axes:
                if any(line.get_marker() == "o" for line in ax.lines):
                    lo, hi = ax.get_ylim()
                    ax.set_ylim(top=hi + .19 * (hi - lo))

        # Axis limits are in the selected DISPLAY units (normalized mode = dimensionless).
        for ax in axes:
            if settings.x_min is not None or settings.x_max is not None:
                ax.set_xlim(left=settings.x_min, right=settings.x_max)
            if settings.y_min is not None or settings.y_max is not None:
                ax.set_ylim(bottom=settings.y_min, top=settings.y_max)

            for i, mark in enumerate(annotations):
                is_selected = selected_annotation == i
                stroke = settings.annotation_line_width * (1.4 if is_selected else 1)
                if isinstance(mark, VerticalAnnotation):
                    x = wavelength_display(mark.wavelength_nm, settings.x_unit)
                    ax.axvline(x, color=mark.color, linestyle=mark.linestyle,
                               linewidth=stroke, alpha=.95, zorder=3)
                    label = mark.text.strip()
                    if mark.show_value:
                        label = (label + "\n" if label else "") + format_wavelength(mark.wavelength_nm, settings.x_unit)
                    if label:
                        tr = ax.get_xaxis_transform() + ScaledTranslation(
                            mark.label_dx_pt / 72.0, 0, figure.dpi_scale_trans)
                        ax.text(x, mark.label_y, label, transform=tr,
                                fontsize=settings.font_annotations, color="#252525", ha="center", va="center", zorder=6,
                                bbox={"boxstyle": "square,pad=0.28", "fc": "white", "ec": "#d3d3d3", "alpha": .93, "lw": .7})
                elif isinstance(mark, HorizontalAnnotation):
                    if (mark.reference_scale == "normalized") != (mode == 2):
                        continue  # Never position a V line on a dimensionless normalized axis.
                    yref = (mark.signal_value if mode == 2
                            else signal_display(mark.signal_value, settings.y_unit))
                    ax.axhline(yref, color=mark.color, linestyle=mark.linestyle,
                               linewidth=stroke, alpha=.95, zorder=3)
                    label = mark.text.strip()
                    if mark.show_value:
                        formatted = (f"Y = {yref:.6g} (norm.)" if mode == 2
                                     else f"Y = {yref:.6g} {settings.y_unit}")
                        label = (label + "\n" if label else "") + formatted
                    if label:
                        tr = ax.get_yaxis_transform() + ScaledTranslation(
                            0, mark.label_dy_pt / 72.0, figure.dpi_scale_trans)
                        ax.text(mark.label_x, yref, label, transform=tr,
                                fontsize=settings.font_annotations, color="#252525", ha="center", va="center", zorder=6,
                                bbox={"boxstyle": "square,pad=0.28", "fc": "white", "ec": "#d3d3d3", "alpha": .93, "lw": .7})
                else:
                    raise ValueError("Tipo de anotação desconhecido.")

        if title_visible:
            figure.text(.5, .963, settings.title, ha="center", va="center",
                        fontsize=settings.font_title, fontweight="bold", color="#111111")
        if subtitle_visible:
            figure.text(.5, .912, settings.subtitle, ha="center", va="center",
                        fontsize=settings.font_subtitle, color="#4c4c4c")
        if footer_visible:
            footer = settings.footer
            if any(validate_factor(scale_factors.get(sp.uid, 1.0)) != 1 for sp in spectra):
                footer += "  Escalas visuais ×f aplicadas; medições originais preservadas."
            if mode == 2:
                footer += "  Curvas normalizadas pela amplitude máxima após escala."
            figure.text(.5, .050, footer, ha="center", va="center",
                        fontsize=settings.font_footer, color="#494949", wrap=True)
        return axes



def create_export_figure(
    spectra: Iterable[Spectrum],
    settings: PlotSettings,
    annotations: Iterable[VerticalAnnotation | HorizontalAnnotation] = (),
    *,
    mode: int = 0,
    grid: bool = True,
    legend: bool = True,
    selected_annotation: int | None = None,
    scale_factors: dict[str, float] | None = None,
    highlight_peak_uid: str | None = None,
) -> Figure:
    """Build a *separate* publication-sized figure, independent of the Qt preview.

    The embedded canvas is never repurposed for PDF/SVG export.  Its widget
    geometry therefore remains controlled exclusively by the window layout.
    """
    settings.validate()
    figure = Figure(figsize=(settings.figure_width_in, settings.figure_height_in), dpi=100)
    render_plot(
        figure, spectra, settings, annotations, mode=mode, grid=grid,
        legend=legend, selected_annotation=selected_annotation,
        scale_factors=scale_factors, highlight_peak_uid=highlight_peak_uid,
    )
    return figure


def export_vector(figure: Figure, filename: str | Path, *, title: str = "Espectros de PL") -> None:
    """Export paths and glyphs without rasterizing plots (PDF/SVG)."""
    filename = Path(filename)
    ext = filename.suffix.lower()
    if ext not in (".pdf", ".svg", ".png"):
        raise ValueError("Use .pdf, .svg ou .png")
    metadata = {"Title": title, "Creator": "PL Spectrum Viewer — Matplotlib"}
    if ext == ".svg":
        metadata["Description"] = "Espectros vetoriais; unidades V/mV e nm/Å selecionáveis"
    with mpl.rc_context({"svg.fonttype": "none", "pdf.fonttype": 42,
                         "ps.fonttype": 42, "savefig.facecolor": "white"}):
        figure.savefig(filename, format=ext.lstrip("."), dpi=240,
                       facecolor="white", metadata=metadata)


def save_session(path: str | Path, settings: PlotSettings,
                 annotations: list[VerticalAnnotation | HorizontalAnnotation], source: str | None,
                 checked_uids: list[str], mode: int, grid: bool, legend: bool,
                 *, scale_factors: dict[str, float] | None = None,
                 highlight_peak_uid: str | None = None) -> None:
    settings.validate()
    if len(annotations) > 100:
        raise ValueError("Limite de 100 anotações por gráfico.")
    for a in annotations:
        a.validate()
    if (not isinstance(checked_uids, list) or len(checked_uids) > 10000
            or any(not isinstance(uid, str) or not uid for uid in checked_uids)
            or len(set(checked_uids)) != len(checked_uids)):
        raise ValueError("Ordem de seleção inválida.")
    cleaned_factors = {str(uid): validate_factor(factor)
                       for uid, factor in (scale_factors or {}).items() if validate_factor(factor) != 1}
    output = {
        "schema": "pl-spectrum-viewer-plot-session/v1",
        "saved_at": datetime.now().astimezone().isoformat(),
        "data_source": source,
        "selected_spectrum_uids": checked_uids,
        "mode": mode, "grid": grid, "legend": legend,
        "spectrum_display_factors": cleaned_factors,
        "highlight_peak_uid": highlight_peak_uid,
        "settings": asdict(settings),
        # Compatibilidade com v1.1–v1.3.1 e preservação da ordem intercalada.
        "vertical_annotations": [asdict(a) for a in annotations if isinstance(a, VerticalAnnotation)],
        "horizontal_annotations": [asdict(a) for a in annotations if isinstance(a, HorizontalAnnotation)],
        "annotations": [dict({"orientation": "vertical" if isinstance(a, VerticalAnnotation) else "horizontal"},
                              **asdict(a)) for a in annotations],
        "caution": "Dados não incluídos. Leituras armazenadas em V; V→mV apenas conversão de unidade. Fatores ×f são visuais.",
    }
    Path(path).write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")


def load_session(path: str | Path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("schema") != "pl-spectrum-viewer-plot-session/v1":
        raise ValueError("Arquivo de sessão incompatível.")
    new_marks = data.get("annotations")
    if new_marks is not None:
        if not isinstance(new_marks, list) or len(new_marks) > 100:
            raise ValueError("Número inválido de anotações.")
        annotations = []
        for entry in new_marks:
            if not isinstance(entry, dict):
                raise ValueError("Anotação inválida na sessão.")
            entry = dict(entry)
            orientation = entry.pop("orientation", None)
            if orientation == "vertical":
                annotations.append(VerticalAnnotation(**entry))
            elif orientation == "horizontal":
                annotations.append(HorizontalAnnotation(**entry))
            else:
                raise ValueError("Orientação de anotação desconhecida.")
    else:
        # Séries v1.1–v1.3.1 continham apenas anotações verticais.
        vertical = data.get("vertical_annotations", [])
        horizontal = data.get("horizontal_annotations", [])
        if (not isinstance(vertical, list) or not isinstance(horizontal, list)
                or len(vertical) + len(horizontal) > 100):
            raise ValueError("Número inválido de anotações.")
        annotations = [VerticalAnnotation(**a) for a in vertical]
        annotations.extend(HorizontalAnnotation(**a) for a in horizontal)
    saved_settings = dict(data["settings"])
    # Sessions from v1.1–v1.3.2 used generic Y axis text and contained readings in V.
    if saved_settings.get("y_label") == "Recorded lock-in signal (original units; uncalibrated)":
        saved_settings["y_label"] = "Sinal do lock-in"
    settings = PlotSettings(**saved_settings)
    settings.validate()
    for a in annotations: a.validate()
    raw_order = data.get("selected_spectrum_uids", [])
    if (not isinstance(raw_order, list) or len(raw_order) > 10000
            or any(not isinstance(uid, str) or not uid for uid in raw_order)
            or len(set(raw_order)) != len(raw_order)):
        raise ValueError("Ordem de seleção inválida no arquivo de edição.")
    raw_factors = data.get("spectrum_display_factors", {})
    if not isinstance(raw_factors, dict) or len(raw_factors) > 10000:
        raise ValueError("Fatores de série inválidos.")
    for uid, factor in raw_factors.items():
        if not isinstance(uid, str) or not uid or len(uid) > 500:
            raise ValueError("ID de série inválido nos fatores.")
        validate_factor(factor)
    if data.get("highlight_peak_uid") is not None and not isinstance(data["highlight_peak_uid"], str):
        raise ValueError("Identificador do destaque de pico inválido.")
    mode = data.get("mode", 0)
    if mode not in (0, 1, 2): raise ValueError("Modo da sessão inválido.")
    return data, settings, annotations
