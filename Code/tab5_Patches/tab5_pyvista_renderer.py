"""
PyVista / VTK-based 3D Renderer for Tab 5
==========================================
Offscreen VTK → numpy → PIL → tk.Canvas pipeline.
No libvtkRenderingTk.so required (works with PyPI vtk wheel).

Improvements:
  • Solid black background matching all other 3D viewers
  • Translucent / fully-opaque toggle (preserved across redraws)
  • Throttled blit: drag events queue a single redraw ~16 ms later
    so the interactor style always runs but pixel readback is capped
    at ~60 fps instead of firing on every mouse-move event
  • Legend is a pure tkinter Frame overlaid with .place() –
    no VTK text actors, no distorted colours
"""

from __future__ import annotations

import tkinter as tk
from typing import Callable, Optional

import numpy as np
import vtk
from vtk.util import numpy_support as vtk_np
from PIL import Image, ImageTk

#  constants 

FACE_DEFS: list[tuple[str, list[int]]] = [
    ("bottom", [0, 3, 2, 1]),
    ("top",    [4, 5, 6, 7]),
    ("front",  [0, 1, 5, 4]),
    ("back",   [3, 7, 6, 2]),
    ("left",   [0, 4, 7, 3]),
    ("right",  [1, 2, 6, 5]),
]

# Per-patch colours as (r, g, b) in 0-1 float range
PATCH_COLORS: list[tuple[float, float, float]] = [
    (0.90, 0.10, 0.29), (0.20, 0.63, 0.17), (1.00, 0.88, 0.10),
    (0.26, 0.39, 0.85), (0.95, 0.51, 0.19), (0.57, 0.12, 0.71),
    (0.15, 0.83, 0.93), (0.90, 0.20, 0.90), (0.75, 0.94, 0.27),
    (0.98, 0.75, 0.83), (0.46, 0.60, 0.60), (0.87, 0.75, 1.00),
    (0.58, 0.39, 0.14), (0.00, 0.46, 0.46), (0.50, 0.00, 0.00),
]

# Same colours as hex strings for the tkinter legend swatches
PATCH_COLORS_HEX: list[str] = [
    "#e61a4a", "#33a12b", "#ffe01a", "#4263db", "#f38230",
    "#911eb4", "#26d4ef", "#e633e6", "#bff045", "#fac4d4",
    "#75999a", "#debeff", "#944f1e", "#007575", "#800000",
]

_COL_DEFAULT = (52,  52,  72)   # dark grey (unselected face, RGB 0-255)
_COL_SELECT  = (76, 201, 176)   # teal     (selected face)

# Throttle interval for drag redraws (milliseconds).
# 16 ms ≈ 60 fps.  Increase to 33 for slower machines.
_BLIT_INTERVAL_MS = 16


#  renderer 

class HexBlockRenderer:
    """
    VTK 3D renderer embedded in a tk.Frame via offscreen pixel blitting.

    Controls:
        Left-drag   : rotate
        Middle-drag : pan
        Right-drag  : zoom
        Scroll      : zoom
        Left-click  : pick / toggle face selection
    """

    def __init__(self, parent_frame: tk.Frame, mesh_data):
        self.parent_frame = parent_frame
        self.mesh_data    = mesh_data

        #  geometry state 
        self.all_faces:      list[dict] = []
        self.selected_faces: set[int]   = set()
        self._face_cache_valid           = False
        self._cell_to_face:  list[int]  = []

        #  display options 
        self.patch_coloring_mode = True
        self.opaque_mode         = False   # False = translucent, True = fully opaque
        self.patch_edit_mode     = False
        self.normals_tab         = None

        #  patch colour maps 
        self._patch_color_map: dict[str, tuple]     = {}   # name → (r,g,b) 0-1
        self._patch_hex_map:   dict[str, str]       = {}   # name → "#rrggbb"
        self._face_to_patch:   dict[int, str]       = {}
        self._ptset_to_patch:  dict[frozenset, str] = {}

        #  VTK objects 
        self.vtk_renderer:   Optional[vtk.vtkRenderer]               = None
        self.render_window:  Optional[vtk.vtkRenderWindow]           = None
        self.interactor:     Optional[vtk.vtkRenderWindowInteractor] = None
        self._surface_actor: Optional[vtk.vtkActor]                  = None
        self._sel_actor:     Optional[vtk.vtkActor]                  = None
        self._axes_widget                                             = None
        self._w2i:           Optional[vtk.vtkWindowToImageFilter]    = None

        #  tk widgets 
        self.canvas:         Optional[tk.Canvas] = None
        self._legend_frame:  Optional[tk.Frame]  = None
        self._photo:         Optional[ImageTk.PhotoImage] = None  # must hold ref

        #  interaction state 
        self._last_xy       = (0, 0)
        self._drag_btn: Optional[int] = None
        self._blit_pending  = False     # throttle flag

        #  external callbacks 
        self.on_selection_changed: Optional[Callable]              = None
        self._click_override:      Optional[Callable[[int], None]] = None

        self._build_pipeline()

    #  pipeline 

    def _build_pipeline(self) -> None:
        """Create the tk.Canvas, VTK offscreen pipeline, and event bindings."""

        frame = self.parent_frame

        # Canvas that receives the blitted VTK frames
        self.canvas = tk.Canvas(frame, bg="#1e1e1e",
                                highlightthickness=0, cursor="fleur")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # VTK renderer – solid black background
        self.vtk_renderer = vtk.vtkRenderer()
        self.vtk_renderer.SetBackground(0.0, 0.0, 0.0)
        self.vtk_renderer.GradientBackgroundOff()

        # Offscreen render window
        self.render_window = vtk.vtkRenderWindow()
        self.render_window.AddRenderer(self.vtk_renderer)
        self.render_window.SetOffScreenRendering(1)
        self.render_window.SetSize(800, 600)
        self.render_window.SetMultiSamples(4)

        # Interactor (drives the camera style; OS event loop not used)
        self.interactor = vtk.vtkRenderWindowInteractor()
        self.interactor.SetRenderWindow(self.render_window)
        self.interactor.Initialize()
        style = vtk.vtkInteractorStyleTrackballCamera()
        self.interactor.SetInteractorStyle(style)

        # Cell picker – restricted to surface actor only so we avoid the
        # VTK Python wrapper identity problem (GetActor() is != stored actor).
        self.picker = vtk.vtkCellPicker()
        self.picker.SetTolerance(0.002)
        self.picker.PickFromListOn()   # only pick from AddPickList() entries

        # Window-to-image (pixel extraction)
        self._w2i = vtk.vtkWindowToImageFilter()
        self._w2i.SetInput(self.render_window)
        self._w2i.SetInputBufferTypeToRGB()
        self._w2i.ReadFrontBufferOff()

        # Axes orientation marker (bottom-left)
        axes = vtk.vtkAxesActor()
        axes.SetTotalLength(1.0, 1.0, 1.0)
        axes.SetShaftTypeToLine()
        self._axes_widget = vtk.vtkOrientationMarkerWidget()
        self._axes_widget.SetOrientationMarker(axes)
        self._axes_widget.SetInteractor(self.interactor)
        self._axes_widget.SetViewport(0.0, 0.0, 0.18, 0.18)
        self._axes_widget.SetEnabled(1)
        self._axes_widget.InteractiveOff()

        # Tkinter legend overlay (built/rebuilt in _rebuild_legend)
        self._legend_frame = tk.Frame(self.canvas, bg="#1e1e1e")
        # positioned with .place() so it floats over the canvas

        #  Canvas event bindings 
        # Control scheme matches Tab 3 / Tab 4:
        #   Left click/drag  → select faces  (ANSYS-style brush on drag)
        #   Middle drag      → rotate
        #   Right drag       → pan
        #   Scroll           → zoom
        self.canvas.bind("<Configure>",        self._on_resize)
        # Left button – selection / drag-select only
        self.canvas.bind("<ButtonPress-1>",    self._on_lmb_press)
        self.canvas.bind("<B1-Motion>",        self._on_lmb_drag)
        self.canvas.bind("<ButtonRelease-1>",  self._on_lmb_release)
        # Middle button – rotate  (mapped to VTK LeftButton for TrackballCamera)
        self.canvas.bind("<ButtonPress-2>",    self._on_mmb_press)
        self.canvas.bind("<B2-Motion>",        self._on_mmb_drag)
        self.canvas.bind("<ButtonRelease-2>",  self._on_mmb_release)
        # Right button – pan  (mapped to VTK MiddleButton for TrackballCamera)
        self.canvas.bind("<ButtonPress-3>",    self._on_rmb_press)
        self.canvas.bind("<B3-Motion>",        self._on_rmb_drag)
        self.canvas.bind("<ButtonRelease-3>",  self._on_rmb_release)
        # Scroll – zoom
        self.canvas.bind("<MouseWheel>",       self._on_wheel)
        self.canvas.bind("<Button-4>",         self._on_wheel_up)
        self.canvas.bind("<Button-5>",         self._on_wheel_down)
        self.canvas.bind("<Enter>",            lambda e: self.canvas.focus_set())

    #  blit (throttled) 

    def _vtk_y(self, y: int) -> int:
        """Canvas Y → VTK Y (VTK origin is bottom-left)."""
        return self.render_window.GetSize()[1] - y

    def _schedule_blit(self) -> None:
        """Queue a single blit at most every _BLIT_INTERVAL_MS milliseconds."""
        if not self._blit_pending:
            self._blit_pending = True
            self.canvas.after(_BLIT_INTERVAL_MS, self._do_blit)

    def _do_blit(self) -> None:
        """Actually render and push pixels to the canvas."""
        self._blit_pending = False
        self._blit()

    def _blit(self) -> None:
        """Render VTK offscreen, extract pixels, paste onto tk.Canvas."""
        if not self.render_window or not self.canvas:
            return

        self.render_window.Render()

        self._w2i.Modified()
        self._w2i.Update()
        img_data = self._w2i.GetOutput()

        w, h, _ = img_data.GetDimensions()
        if w < 1 or h < 1:
            return

        scalars = img_data.GetPointData().GetScalars()
        arr = vtk_np.vtk_to_numpy(scalars).astype(np.uint8).reshape(h, w, 3)

        # VTK y-axis is flipped
        pil_img = Image.fromarray(arr[::-1], "RGB")
        self._photo = ImageTk.PhotoImage(image=pil_img)

        self.canvas.delete("vtk_image")
        self.canvas.create_image(0, 0, anchor=tk.NW,
                                 image=self._photo, tags="vtk_image")

        # Keep legend on top
        if self._legend_frame:
            self._legend_frame.lift()

    #  resize 

    def _on_resize(self, event) -> None:
        w, h = max(event.width, 50), max(event.height, 50)
        self.render_window.SetSize(w, h)
        self._blit()

    #  helpers 

    def _vtk_pos(self, event) -> tuple[int, int]:
        """Return (vtk_x, vtk_y) for an event, flipping Y."""
        return event.x, self._vtk_y(event.y)

    def _camera_move(self, event) -> None:
        """Feed a mouse-move to the VTK interactor and schedule a blit."""
        lx, ly = self._last_xy
        self.interactor.SetLastEventPosition(lx, self._vtk_y(ly))
        x, y = self._vtk_pos(event)
        self.interactor.SetEventPosition(x, y)
        self.interactor.InvokeEvent("MouseMoveEvent")
        self._last_xy = (event.x, event.y)
        self._schedule_blit()

    #  LEFT button – selection + ANSYS-style drag-select 
    # Left button is handled entirely by us; no VTK camera events fired.

    def _on_lmb_press(self, event) -> None:
        self.canvas.focus_set()
        self._lmb_press_xy = (event.x, event.y)
        self._last_xy      = (event.x, event.y)
        self._lmb_dragging = False          # becomes True once pointer moves > threshold
        self._drag_added: set[int] = set()  # faces added in this drag stroke

    def _on_lmb_drag(self, event) -> None:
        """
        ANSYS-style brush selection:
        As the pointer moves, any face under it is added to the selection
        (or added to deselection if the first picked face was already selected).
        The decision (add vs remove) is locked at drag start.
        """
        px, py = self._lmb_press_xy
        if not self._lmb_dragging:
            if abs(event.x - px) >= 4 or abs(event.y - py) >= 4:
                self._lmb_dragging = True
                # Decide the drag mode: the first face under the cursor
                # determines whether this stroke adds or removes.
                fid = self._pick_face_id(event.x, event.y)
                if fid is not None:
                    self._drag_mode = 'remove' if fid in self.selected_faces else 'add'
                else:
                    self._drag_mode = 'add'

        if not self._lmb_dragging:
            return

        fid = self._pick_face_id(event.x, event.y)
        if fid is not None and fid not in self._drag_added:
            self._drag_added.add(fid)
            if self._drag_mode == 'add':
                self.selected_faces.add(fid)
            else:
                self.selected_faces.discard(fid)
            self._schedule_blit()

    def _on_lmb_release(self, event) -> None:
        if self._lmb_dragging:
            # Drag stroke finished – fire the selection-changed callback
            self._lmb_dragging = False
            if self.on_selection_changed:
                self.on_selection_changed(self.selected_faces.copy())
            return

        # Pure click (no drag): toggle the single face under the cursor
        self._pick_and_toggle(event.x, event.y)

    #  MIDDLE button – rotate 
    # Mapped to VTK LeftButton so TrackballCamera provides rotation.

    def _on_mmb_press(self, event) -> None:
        self._last_xy = (event.x, event.y)
        x, y = self._vtk_pos(event)
        self.interactor.SetEventPosition(x, y)
        self.interactor.InvokeEvent("LeftButtonPressEvent")

    def _on_mmb_drag(self, event) -> None:
        self._camera_move(event)

    def _on_mmb_release(self, event) -> None:
        x, y = self._vtk_pos(event)
        self.interactor.SetEventPosition(x, y)
        self.interactor.InvokeEvent("LeftButtonReleaseEvent")

    #  RIGHT button – pan 
    # Mapped to VTK MiddleButton so TrackballCamera provides panning.

    def _on_rmb_press(self, event) -> None:
        self._last_xy = (event.x, event.y)
        x, y = self._vtk_pos(event)
        self.interactor.SetEventPosition(x, y)
        self.interactor.InvokeEvent("MiddleButtonPressEvent")

    def _on_rmb_drag(self, event) -> None:
        self._camera_move(event)

    def _on_rmb_release(self, event) -> None:
        x, y = self._vtk_pos(event)
        self.interactor.SetEventPosition(x, y)
        self.interactor.InvokeEvent("MiddleButtonReleaseEvent")

    #  scroll – zoom 

    def _on_wheel(self, event) -> None:
        x, y = self._vtk_pos(event)
        self.interactor.SetEventPosition(x, y)
        ev = "MouseWheelForwardEvent" if event.delta > 0 else "MouseWheelBackwardEvent"
        self.interactor.InvokeEvent(ev)
        self._schedule_blit()

    def _on_wheel_up(self, event) -> None:
        x, y = self._vtk_pos(event)
        self.interactor.SetEventPosition(x, y)
        self.interactor.InvokeEvent("MouseWheelForwardEvent")
        self._schedule_blit()

    def _on_wheel_down(self, event) -> None:
        x, y = self._vtk_pos(event)
        self.interactor.SetEventPosition(x, y)
        self.interactor.InvokeEvent("MouseWheelBackwardEvent")
        self._schedule_blit()

    #  face picking 

    def _pick_face_id(self, cx: int, cy: int) -> int | None:
        """Ray-cast at canvas (cx, cy). Return face_id or None."""
        if not self._cell_to_face:
            return None
        self.picker.Pick(cx, self._vtk_y(cy), 0, self.vtk_renderer)
        cell_id = self.picker.GetCellId()
        if cell_id < 0 or cell_id >= len(self._cell_to_face):
            return None
        return self._cell_to_face[cell_id]

    def _pick_and_toggle(self, cx: int, cy: int) -> None:
        """Single-click toggle: pick the face and toggle its selection state."""
        face_id = self._pick_face_id(cx, cy)
        if face_id is None:
            return

        if self._click_override is not None:
            self._click_override(face_id)
            return

        if face_id in self.selected_faces:
            self.selected_faces.discard(face_id)
        else:
            self.selected_faces.add(face_id)

        self.draw()
        if self.on_selection_changed:
            self.on_selection_changed(self.selected_faces.copy())

    #  geometry building 

    def _build_faces(self) -> None:
        if self._face_cache_valid:
            return

        self.all_faces = []
        raw: list[dict] = []
        hex_blocks = getattr(self.mesh_data, 'hex_blocks', {})

        for block_idx, block in hex_blocks.items():
            if not isinstance(block, dict):
                continue
            refs = block.get('point_refs', [])
            if len(refs) != 8:
                continue

            verts: list[np.ndarray] = []
            for pid in refs:
                c = self.mesh_data.get_3d_coords_from_global(pid)
                if c is None:
                    break
                verts.append(np.asarray(c, dtype=float))
            if len(verts) != 8:
                continue

            for fname, fi in FACE_DEFS:
                fv = [verts[i] for i in fi]
                gi = [refs[i]  for i in fi]
                raw.append({
                    'block_idx':      int(block_idx),
                    'face_name':      fname,
                    'vertices':       fv,
                    'global_indices': gi,
                    'face_key':       tuple(sorted(gi)),
                    'face_id':        len(raw),
                })

        counts: dict[tuple, int] = {}
        for f in raw:
            counts[f['face_key']] = counts.get(f['face_key'], 0) + 1

        for f in raw:
            internal = counts[f['face_key']] > 1
            self.all_faces.append({
                **f,
                'is_internal': internal,
                'is_visible':  not internal,
                'center':      np.mean(f['vertices'], axis=0),
            })

        self._build_patch_mapping()
        self._face_cache_valid = True

    def _build_patch_mapping(self) -> None:
        self._face_to_patch   = {}
        self._patch_color_map = {}
        self._patch_hex_map   = {}
        self._ptset_to_patch  = {}

        patches = getattr(self.mesh_data, 'patches', {})
        if not patches:
            return

        for i, name in enumerate(patches):
            self._patch_color_map[name] = PATCH_COLORS[i % len(PATCH_COLORS)]
            self._patch_hex_map[name]   = PATCH_COLORS_HEX[i % len(PATCH_COLORS_HEX)]

        for name, pdata in patches.items():
            if not isinstance(pdata, dict):
                continue
            for face in pdata.get('faces', []):
                if isinstance(face, dict):
                    pids = face.get('point_ids')
                    if pids:
                        self._ptset_to_patch[frozenset(pids)] = name

        for face in self.all_faces:
            fs = frozenset(face['global_indices'])
            if fs in self._ptset_to_patch:
                self._face_to_patch[face['face_id']] = self._ptset_to_patch[fs]

    #  VTK mesh helpers 

    def _face_opacity(self) -> float:
        return 1.0 if self.opaque_mode else 0.72

    def _make_polydata(
        self,
        faces: list[dict],
        force_color: Optional[tuple[int, int, int]] = None,
    ) -> tuple[vtk.vtkPolyData, list[int]]:
        vtk_pts  = vtk.vtkPoints()
        vtk_poly = vtk.vtkCellArray()
        rgb      = vtk.vtkUnsignedCharArray()
        rgb.SetNumberOfComponents(3)
        rgb.SetName("RGB")
        cell_ids: list[int] = []

        for face in faces:
            fid  = face['face_id']
            base = vtk_pts.GetNumberOfPoints()
            for v in face['vertices']:
                vtk_pts.InsertNextPoint(float(v[0]), float(v[1]), float(v[2]))
            q = vtk.vtkQuad()
            for k in range(4):
                q.GetPointIds().SetId(k, base + k)
            vtk_poly.InsertNextCell(q)
            cell_ids.append(fid)

            if force_color:
                r, g, b = force_color
            elif fid in self.selected_faces:
                r, g, b = _COL_SELECT
            elif self.patch_coloring_mode and fid in self._face_to_patch:
                pr, pg, pb = self._patch_color_map[self._face_to_patch[fid]]
                r, g, b = int(pr * 255), int(pg * 255), int(pb * 255)
            else:
                r, g, b = _COL_DEFAULT
            rgb.InsertNextTuple3(r, g, b)

        pd = vtk.vtkPolyData()
        pd.SetPoints(vtk_pts)
        pd.SetPolys(vtk_poly)
        pd.GetCellData().AddArray(rgb)
        pd.GetCellData().SetActiveScalars("RGB")
        return pd, cell_ids

    def _make_actor(
        self,
        pd: vtk.vtkPolyData,
        *,
        opacity: Optional[float] = None,
        edge_color: tuple = (0.55, 0.55, 0.60),
        edge_width: float = 1.2,
    ) -> vtk.vtkActor:
        if opacity is None:
            opacity = self._face_opacity()

        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputData(pd)
        mapper.ScalarVisibilityOn()
        mapper.SetScalarModeToUseCellData()
        mapper.SelectColorArray("RGB")
        mapper.SetColorModeToDirectScalars()

        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        p = actor.GetProperty()
        p.SetOpacity(opacity)
        p.EdgeVisibilityOn()
        p.SetEdgeColor(*edge_color)
        p.SetLineWidth(edge_width)
        p.SetInterpolationToPhong()
        p.SetAmbient(0.30)
        p.SetDiffuse(0.70)
        p.SetSpecular(0.10)
        return actor

    #  scene update 

    def _clear_actors(self) -> None:
        for attr in ('_surface_actor', '_sel_actor'):
            a = getattr(self, attr, None)
            if a:
                self.vtk_renderer.RemoveActor(a)
                setattr(self, attr, None)
        self.vtk_renderer.RemoveAllViewProps()
        if self._axes_widget:
            self._axes_widget.SetEnabled(1)

    def draw(self) -> None:
        if self.patch_edit_mode and self.normals_tab:
            self.normals_tab._redraw_canvas()
            return

        self._build_faces()
        self._clear_actors()

        visible = [f for f in self.all_faces if f.get('is_visible', False)]
        if not visible:
            self._empty_msg()
            self._blit()
            self._rebuild_legend()
            return

        pd, self._cell_to_face = self._make_polydata(visible)
        self._surface_actor = self._make_actor(pd)
        self.vtk_renderer.AddActor(self._surface_actor)
        # Keep picker list in sync – this replaces the actor identity check
        self.picker.GetPickList().RemoveAllItems()
        self.picker.AddPickList(self._surface_actor)

        sel = [f for f in visible if f['face_id'] in self.selected_faces]
        if sel:
            spd, _ = self._make_polydata(sel, force_color=_COL_SELECT)
            self._sel_actor = self._make_actor(
                spd, opacity=1.0,
                edge_color=(0.00, 0.95, 0.78), edge_width=3.0)
            # Polygon offset pulls the selection overlay in front of the
            # main surface, eliminating z-fighting.
            self._sel_actor.GetMapper().SetResolveCoincidentTopologyToPolygonOffset()
            self._sel_actor.GetMapper().SetResolveCoincidentTopologyPolygonOffsetParameters(-1, -1)
            self.vtk_renderer.AddActor(self._sel_actor)

        self._blit()
        self._rebuild_legend()

    def _empty_msg(self) -> None:
        txt = vtk.vtkTextActor()
        txt.SetInput("No hex blocks to display.\nCreate blocks in Tab 4 first.")
        tp = txt.GetTextProperty()
        tp.SetFontSize(16)
        tp.SetColor(0.60, 0.60, 0.60)
        tp.SetJustificationToCentered()
        tp.SetVerticalJustificationToCentered()
        txt.GetPositionCoordinate().SetCoordinateSystemToNormalizedViewport()
        txt.GetPositionCoordinate().SetValue(0.5, 0.5)
        self.vtk_renderer.AddActor2D(txt)

    #  tk legend overlay 

    def _rebuild_legend(self) -> None:
        """
        Rebuild the patch colour legend as a pure tkinter Frame placed
        in the top-right corner of the canvas.  Much crisper than VTK
        text actors and no colour distortion.
        """
        if not self.canvas or not self._legend_frame:
            return

        # Clear old content
        for w in self._legend_frame.winfo_children():
            w.destroy()

        if not (self.patch_coloring_mode and self._patch_hex_map):
            self._legend_frame.place_forget()
            return

        BG   = "#1a1a1a"
        FG   = "#cccccc"
        FONT = ("Segoe UI", 9)

        self._legend_frame.configure(bg=BG,
                                     highlightthickness=1,
                                     highlightbackground="#3e3e42")

        # Title
        tk.Label(self._legend_frame, text="Patches",
                 font=("Segoe UI", 9, "bold"),
                 bg=BG, fg="#ffffff").pack(anchor=tk.W, padx=6, pady=(5, 2))

        # One row per patch
        for name, hex_col in self._patch_hex_map.items():
            row = tk.Frame(self._legend_frame, bg=BG)
            row.pack(fill=tk.X, padx=6, pady=1)

            # Colour swatch
            swatch = tk.Frame(row, bg=hex_col, width=13, height=13,
                              highlightthickness=1,
                              highlightbackground="#555555")
            swatch.pack(side=tk.LEFT, padx=(0, 5))
            swatch.pack_propagate(False)

            # Name label (truncated)
            display = name if len(name) <= 20 else name[:19] + "…"
            tk.Label(row, text=display, font=FONT,
                     bg=BG, fg=FG, anchor=tk.W).pack(side=tk.LEFT)

        # Padding at bottom
        tk.Frame(self._legend_frame, bg=BG, height=4).pack()

        # Force geometry calculation so winfo_reqwidth is accurate
        self._legend_frame.update_idletasks()

        # Position: top-right corner, 8 px margin
        cw = self.canvas.winfo_width()
        lw = self._legend_frame.winfo_reqwidth()
        self._legend_frame.place(x=cw - lw - 8, y=8)
        self._legend_frame.lift()

    #  public interface (mirrors original HexBlockRenderer) 

    def highlight_faces(self, face_ids) -> None:
        """
        Highlight a set of faces by id (called by the Highlight button).
        Ensures geometry is built first and filters stale/None ids.
        """
        self._build_faces()   # make sure all_faces exists
        valid = {f['face_id'] for f in self.all_faces}
        clean = {fid for fid in face_ids if fid is not None and fid in valid}
        self.selected_faces = clean
        self.draw()

    def set_click_override(self, cb: Optional[Callable[[int], None]]) -> None:
        self._click_override = cb

    def toggle_opacity(self) -> bool:
        """Toggle between translucent and fully opaque. Returns new state."""
        self.opaque_mode = not self.opaque_mode
        self.draw()
        return self.opaque_mode

    def invalidate_cache(self) -> None:
        self._face_cache_valid = False
        self.all_faces = []
        self.selected_faces.clear()
        self._cell_to_face = []

    def get_selected_face_data(self) -> list[dict]:
        return [f for f in self.all_faces if f.get('face_id') in self.selected_faces]

    def clear_selection(self) -> None:
        self.selected_faces.clear()
        self.draw()

    def select_faces_by_block(self, block_idx: int) -> None:
        for f in self.all_faces:
            if f.get('block_idx') == block_idx and f.get('is_visible', False):
                self.selected_faces.add(f['face_id'])
        self.draw()

    def set_patch_coloring_mode(self, enabled: bool) -> None:
        self.patch_coloring_mode = enabled
        self.invalidate_cache()
        self.draw()

    def toggle_patch_coloring(self) -> bool:
        self.patch_coloring_mode = not self.patch_coloring_mode
        self.draw()
        return self.patch_coloring_mode

    def show_all_faces(self) -> None:
        for f in self.all_faces:
            if not f.get('is_internal', False):
                f['is_visible'] = True
        self.draw()

    def get_hidden_face_count(self) -> int:
        return sum(
            1 for f in self.all_faces
            if not f.get('is_internal', False) and not f.get('is_visible', True)
        )

    def set_patch_edit_mode(self, enabled: bool, normals_tab=None) -> None:
        self.patch_edit_mode = enabled
        self.normals_tab = normals_tab
        self.draw()

    def draw_patch_edit_mode(self, patch_faces, normals_tab) -> None:
        self.draw()

    def fit_view(self) -> None:
        self.vtk_renderer.ResetCamera()
        self._blit()

    def reset_view(self) -> None:
        self.fit_view()

    def fit_all(self) -> None:
        self.fit_view()
