"""
THE IMPORT ORDER MATTERS!!
    Input widgets rely on Tab Shoji
    ColorWidget relies on user input widgets

    I need more abstract classes...
"""

""" IMPORT ABSTRACT WIDGETS """
from .AbstractWidgets import *

from .AbstractWidgets.AbstractModelViewWidget import AbstractModelViewWidget
from .AbstractWidgets.AbstractModelViewWidget import AbstractModelViewItem
from .AbstractWidgets.AbstractWarningWidget import AbstractWarningWidget
from .AbstractWidgets.AbstractLabelledInputWidget import AbstractLabelledInputWidget
from .AbstractWidgets.AbstractOverlayInputWidget import AbstractOverlayInputWidget
from .AbstractWidgets.AbstractShojiWidget import *
from .AbstractWidgets.AbstractPopupBarWidget import *
# from .AbstractWidgets.AbstractPopupBarOrganizerWidget import AbstractPopupBarOrganizerWidget, AbstractPiPDisplayWidget

""" MODEL VIEW WIDGET"""
from .ModelViewWidget import ModelViewWidget as ModelViewWidget
from .ModelViewWidget import ModelViewWidget as ModelViewItem

""" SHOJI """
from .ShojiWidget import ShojiModelItem as ShojiModelItem
from .ShojiWidget import ShojiModel as ShojiModel

from .ShojiWidget import ShojiLayout
from .ShojiWidget import ShojiLayoutHandle
from .ShojiWidget import ShojiModelViewWidget as ShojiModelViewWidget
from .ShojiWidget import ShojiModelDelegateWidget as ShojiModelDelegateWidget

""" Script Editor """
from .ScriptEditorWidget import ScriptEditorWidget, ScriptEditorPopupEventFilter

""" PiP """
from .PopupWidget import (
    PopupBarOrganizerWidget,
    PopupBarDisplayWidget,
    PopupBarWidget,
    PopupBarItemWidget)

""" INPUT WIDGETS """
from .InputWidgets import *

""" BASE WIDGETS """

from .BaseWidgets import *
# color widget
#from .InputWidgets.ColorInputWidgets import ColorGradientDelegate, ColorInputWidget

""" NODE WIDGETS """
""" This needs to hit a try/except for local testing and to ensure the launches are correct?"""
try:
    from .NodeWidgets import NodeTypeListWidget
    from .NodeWidgets import NodeColorRegistryWidget
except ModuleNotFoundError:
    pass
# from .NodeWidgets import NodeTypeListWidget
# old stuff
from .LibraryWidget import LibraryWidget as LibraryWidget
from .LadderWidget import LadderWidget as LadderWidget

from .__utils__ import *
