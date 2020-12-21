import abc
import ipywidgets
from typing import List, Dict
from IPython.display import Image, clear_output, display


class Context(dict):
    pass


def hooked(func, hook, before=True):
    def wrapper(*args, **kwargs):
        if before:
            hook()
        res = func(*args, **kwargs)
        if not before:
            hook()
        return res
    return wrapper


class StatefulWidgets(abc.ABC):
    def __init__(self,
                 context: Context,
                 widgets: Dict[str, ipywidgets.Widget]):
        self.context = context
        self.widgets = widgets
        self._bind_context(self.context, self.widgets)
        self._bind_hooks()

    @staticmethod
    def _bind_context(context: Context, widgets: Dict[str, ipywidgets.Widget]):
        for name, widget in widgets.items():
            setattr(context, name, widget)
            setattr(widget, 'context', context)

    def _bind_hooks(self) -> None:
        # Automatically call on_context_change after update_context
        self.update_context = hooked(
            self.update_context, self.on_context_change, before=False
        )

    @abc.abstractmethod
    def show(self) -> ipywidgets.Widget:
        raise NotImplementedError

    @abc.abstractmethod
    def on_context_change(self) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def update_context(self, *args, **kwargs) -> None:
        raise NotImplementedError


class ImageViewer(StatefulWidgets):
    def __init__(self, image_files: List[str], width: int = 600):
        if len(image_files) < 1:
            raise ValueError('No images!')
        # Widgets
        widgets = {
            'next_btn': ipywidgets.Button(description='下一张'),
            'previous_btn': ipywidgets.Button(description='上一张'),
            'slider': ipywidgets.IntSlider(
                min=1, max=len(image_files), description='当前图片'
            ),
            'canvas': ipywidgets.Output()
        }
        context = Context(index=0, files=image_files)
        StatefulWidgets.__init__(self, context, widgets)
        # output element
        self._output = ipywidgets.VBox([
            ipywidgets.HBox([
                widgets['previous_btn'], widgets['next_btn'], widgets['slider']
            ]),
            widgets['canvas']
        ])
        self.width = width
        self._bind_actions()
        self._update_image()

    def _bind_actions(self) -> None:
        def on_left_clicked(btn: ipywidgets.Button) -> None:
            self.update_context(btn.context['index'] - 1)

        def on_right_clicked(btn: ipywidgets.Button) -> None:
            self.update_context(btn.context['index'] + 1)

        def on_slide(observation) -> None:
            new_value = observation['new']
            self.update_context(new_value - 1)

        self.context.next_btn.on_click(on_right_clicked)
        self.context.previous_btn.on_click(on_left_clicked)
        self.context.slider.observe(on_slide, names='value')

    def _update_image(self) -> None:
        with self.context.canvas:
            clear_output()
            # noinspection PyTypeChecker
            display(Image(
                self.context['files'][self.context['index']],
                width=self.width
            ))

    def show(self) -> ipywidgets.Widget:
        return self._output

    def update_context(self, new_index: int) -> None:
        min_index, max_index = 0, len(self.context['files']) - 1
        self.context['index'] = min(max_index, max(new_index, min_index))
        self.context.slider.value = self.context['index'] + 1

    def on_context_change(self) -> None:
        self._update_image()
