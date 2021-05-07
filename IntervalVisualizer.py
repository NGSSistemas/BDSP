from datetime import date, datetime, time, timedelta
from typing import List, Optional, Callable

import plotly.graph_objects as go
from colour import Color

from input_reading import BusLeg
from others import Employee



class VisualInterval:
    """Container for the data associated with an interval for visualisation."""

    def __init__(self, start, end, pos: int,  hover: Optional[str], text: Optional[str]) -> None:
        """Set the content.

        Start and end might be integers, datetime, or datetime strings.
        :param start: Start of the interval
        :param end: End of the interval
        :param hover: Text to show on hover, supports plotly formatting
        :param text: Text to show in the center of the interval, supports plotly formatting
        """
        self.start = start
        self.end = end
        self.pos = pos
        self.hover = hover
        self.text = text


class IntervalVisualizer:
    """Factory for creating plotly figures for interval visualisation."""

    AXIS_VAL = 0
    AXIS_HOURS = 1
    AXIS_DAYS = 2
    AXIS_DATE = 3

    def __init__(self, axis: int = AXIS_VAL, axis_delta: timedelta = timedelta(minutes=1), axis_date: date = None) -> \
            None:
        """Initialize the visualizer.

        :param axis: Scale on the time axis, one of AXIS_VAL for integers, AXIS_HOURS for HH:MM, AXIS_DAYS for 'dd hh',
        or AXIS_DATE for date and time
        :param axis_delta: Time granularity in the given intervals
        :param axis_date: Start date for AXIS_DATE, otherwise ignored
        """
        self.height = .4
        self.axis = axis
        self.axis_format = None
        self.hover_format = '%H:%M'
        if axis == self.AXIS_HOURS:
            self.axis_format = '%H:%M'
            axis_date = date(2020, 1, 1)
        elif axis == self.AXIS_DAYS:
            self.axis_format = '%-jd %Hh'
            self.hover_format = '%jd %H:%M'
            axis_date = date(2020, 1, 1)
        elif axis == self.AXIS_DATE:
            self.hover_format = '%Y-%m-%d %H:%M'
        if axis_delta < timedelta(minutes=1):
            self.hover_format += ':%S'
        self.axis_delta = axis_delta
        self.axis_start = datetime.combine(axis_date if axis_date is not None else date.today(), time())

    def __build_hover(self, interval: BusLeg, hover: Optional[str]) -> Optional[str]:
        """Build the hover text from the interval based on the template."""

        if hover is None:
            return None

        index = 0
        while '%' in hover[index:]:

            pos = hover.find('%', index)
            if hover[pos + 1] == '%':
                index += 2
                continue
            end_pos = hover.find('}', index)

            attr = hover[pos + 2:end_pos]
            replace = getattr(interval, hover[pos + 2:end_pos], None)
            if self.axis != self.AXIS_VAL and (attr == 'start' or attr == 'end'):
                replace = (self.axis_start + self.axis_delta * replace).strftime(self.hover_format)
                if self.axis == self.AXIS_DAYS:
                    replace = replace.lstrip('0')
            else:
                replace = str(replace)

            hover = hover.replace(hover[pos:end_pos + 1], replace)

        hover = hover.replace('%%', '%')
        return hover

    @staticmethod
    def __contrast_color(col: Color) -> Color:
        """Return the appropriate text color (black or white) for the given background color."""
        if 0.299 * col.red + 0.587 * col.green + 0.114 * col.blue > 0.5:
            return Color('black')
        else:
            return Color('white')

    def create(self, intervals: List[Employee], title: str, type_attr: Optional[str] = None,
               hovertext: Callable[[BusLeg], str] = lambda x: None, text_attr: Optional[str] = None,
               hidden: Optional[List[str]] = None) -> go.Figure:
        """Create the figure for the given interval sequences.

        :param intervals: List of sequences, each sequence corresponds to one row with the attribute 'name' on the axis
        :param title: Title of the figure
        :param type_attr: BusLeg attribute for grouping the intervals, each type corresponds to a legend entry and a
        (most likely) unique color
        :param hovertext: Function returing the hover text template for each interval, allows plotly formatting like
        <b>...</b> or <br> and using interval attributes with %{attr}, %{start} and %{end} are formatted according to
        self.axis, no hover text if None is returned
        :param text_attr: BusLeg attribute to show as text in the center of each interval, formatted like hovertext
        :param hidden: List of types that are initially hidden
        """

        types = {}
        if hidden is None:
            hidden = []

        for i, sequence in enumerate(intervals):
            for interval in sequence:
                t = None
                if type_attr is not None:
                    t = getattr(interval, type_attr, None)
                if t not in types:
                    types[t] = []
                text = None
                if text_attr is not None:
                    text = getattr(interval, text_attr, None)
                if self.axis == 0:
                    types[t].append(VisualInterval(interval.start,
                                                   interval.end,
                                                   i,
                                                   self.__build_hover(interval, hovertext(interval)),
                                                   text))
                else:
                    types[t].append(VisualInterval(self.axis_start + self.axis_delta * interval.start,
                                                   self.axis_start + self.axis_delta * interval.end,
                                                   i,
                                                   self.__build_hover(interval, hovertext(interval)),
                                                   text))

        data = []
        count = 0
        for t, values in types.items():
            text = []
            text_x = []
            text_y = []
            first = True
            col = Color(pick_for=t, pick_key=None)
            text_col = self.__contrast_color(col)
            for interval in values:
                data.append(go.Scatter(fill='toself',
                                       hoverinfo='none' if interval.hover is None else 'text',
                                       hoverlabel=go.scatter.Hoverlabel(bgcolor=col.hex,
                                                                        font=dict(color=text_col.hex)),
                                       hoveron='fills+points',
                                       legendgroup=t,
                                       line=dict(color=col.hex),
                                       mode='lines',
                                       name=t,
                                       showlegend=first,
                                       text=interval.hover,
                                       visible='legendonly' if t in hidden else True,
                                       x=[interval.start, interval.end, interval.end, interval.start, interval.start],
                                       y=[interval.pos - self.height, interval.pos - self.height,
                                          interval.pos + self.height, interval.pos + self.height,
                                          interval.pos - self.height]))
                first = False
                if interval.text is not None:
                    text.append(interval.text)
                    text_x.append(interval.start + (interval.end - interval.start) / 2)
                    text_y.append(interval.pos)
            data.append(go.Scatter(hoverinfo='skip', legendgroup=t, mode='text', showlegend=False, text=text,
                                   textfont=dict(color=text_col.hex), x=text_x, y=text_y))
            count += 1

        fig = go.Figure(
            data=data,
            layout=go.Layout(
                hoverdistance=3,
                title=go.layout.Title(text=title),
                xaxis=go.layout.XAxis(showspikes=True, spikedash='solid', spikemode='across', spikethickness=1),
                yaxis=go.layout.YAxis(
                    autorange='reversed',
                    ticktext=list(map(lambda v: v.name, intervals)),
                    tickvals=list(range(len(intervals))),
                    zeroline=False
                )
            )
        )

        if self.axis_format is not None:
            fig.update_xaxes(tickformat=self.axis_format)

        return fig
