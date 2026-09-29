"""Interactive 3D illustration of stress-tensor decomposition.

Run with: python run.py

Uses only Python's standard library (Tkinter).
"""

import math
import tkinter as tk
from tkinter import messagebox, ttk


AXES = ("x", "y", "z")
PANEL_COLORS = ("#c65353", "#237a70", "#ce8b28")
NORMAL_COLOR = "#e21f2f"
SHEAR_COLOR = "#1368c4"
BG = "#f4f6f7"


def decompose(stress):
    mean = sum(stress[i][i] for i in range(3)) / 3.0
    spherical = [[mean if i == j else 0.0 for j in range(3)] for i in range(3)]
    deviatoric = [
        [stress[i][j] - spherical[i][j] for j in range(3)]
        for i in range(3)
    ]
    return mean, spherical, deviatoric


class StressDecompositionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("3D Stress Tensor Decomposition")
        self.root.geometry("1440x900")
        self.root.minsize(1120, 760)
        self.root.configure(bg=BG)

        self.view = {"azimuth": 35.0, "elevation": 25.0, "zoom": 1.0}
        self.drag_start = None
        self.auto_rotate = False

        self.entries = {}
        self._build_controls()
        self.canvas = tk.Canvas(
            root, bg="#e9eef1", highlightthickness=0,
            cursor="hand2",
        )
        self.canvas.pack(fill="both", expand=True, padx=14, pady=(4, 8))
        self.canvas.bind("<Configure>", lambda _event: self.draw())
        self.canvas.bind("<ButtonPress-1>", self._start_rotate)
        self.canvas.bind("<B1-Motion>", self._rotate)
        self.canvas.bind("<ButtonRelease-1>", self._stop_rotate)
        self.canvas.bind("<Double-Button-1>", lambda _event: self.reset_view())
        self.canvas.bind("<MouseWheel>", self._zoom)
        self.canvas.bind("<Button-4>", lambda _event: self._change_zoom(0.1))
        self.canvas.bind("<Button-5>", lambda _event: self._change_zoom(-0.1))
        self.status = ttk.Label(
            root, text="", anchor="center", style="Status.TLabel"
        )
        self.status.pack(fill="x", padx=12, pady=(0, 10))
        self.load_example()
        self._animate()

    def _build_controls(self):
        controls = ttk.Frame(self.root, padding=(16, 12))
        controls.pack(fill="x")

        ttk.Label(
            controls,
            text="三维总应力模型",
            font=("Microsoft YaHei UI", 18, "bold"),
        ).grid(row=0, column=0, columnspan=8, sticky="w")
        ttk.Label(
            controls,
            text="三维微元体 · 正应力与剪应力分量  |  单位：MPa",
            foreground="#53616a",
            font=("Microsoft YaHei UI", 10),
        ).grid(row=1, column=0, columnspan=8, sticky="w", pady=(2, 10))

        names = (
            ("σxx", "xx"), ("σyy", "yy"), ("σzz", "zz"),
            ("τxy = τyx", "xy"), ("τxz = τzx", "xz"),
            ("τyz = τzy", "yz"),
        )
        for col, (label, key) in enumerate(names):
            group = ttk.Frame(controls)
            group.grid(row=2, column=col, sticky="w", padx=(0, 12))
            ttk.Label(group, text=label).pack(anchor="w")
            entry = ttk.Entry(group, width=9)
            entry.pack(anchor="w", pady=(3, 0))
            self.entries[key] = entry

        ttk.Button(
            controls, text="更新三维图", command=self.update_plot
        ).grid(row=2, column=6, padx=(8, 0), sticky="s")
        ttk.Button(
            controls, text="课件示例", command=self.load_example
        ).grid(row=2, column=7, padx=(8, 0), sticky="s")
        ttk.Button(
            controls, text="重置当前视角", command=self.reset_view
        ).grid(row=2, column=8, padx=(8, 0), sticky="s")
        self.auto_button = ttk.Button(
            controls, text="自动旋转", command=self.toggle_auto_rotate
        )
        self.auto_button.grid(row=2, column=9, padx=(8, 0), sticky="s")
        controls.columnconfigure(10, weight=1)

        ttk.Label(
            controls,
            text="σ = [[σxx, τxy, τxz], [τxy, σyy, τyz], [τxz, τyz, σzz]]",
            font=("Segoe UI", 11),
        ).grid(row=3, column=0, columnspan=10, sticky="w", pady=(12, 0))

        ttk.Label(
            controls,
            text="左键拖动旋转 | 滚轮缩放 | 双击画布重置视角。"
                 "  红色：正应力 σ | 蓝色：剪应力 τ",
            foreground="#53616a",
        ).grid(row=4, column=0, columnspan=10, sticky="w", pady=(4, 0))

    def load_example(self):
        # A symmetric example with nonzero normal and shear components.
        values = {"xx": "8", "yy": "2", "zz": "-4",
                  "xy": "2", "xz": "-1", "yz": "1"}
        for key, value in values.items():
            self.entries[key].delete(0, tk.END)
            self.entries[key].insert(0, value)
        self.update_plot()

    def update_plot(self):
        try:
            v = {key: float(entry.get()) for key, entry in self.entries.items()}
        except ValueError:
            messagebox.showerror("输入错误", "请在六个分量中输入有效数字。")
            return

        stress = [
            [v["xx"], v["xy"], v["xz"]],
            [v["xy"], v["yy"], v["yz"]],
            [v["xz"], v["yz"], v["zz"]],
        ]
        mean, spherical, deviatoric = decompose(stress)
        self.stress = stress
        self.mean = mean
        self.status.configure(text=self._status_text())
        self.draw()

    def _status_text(self):
        if not hasattr(self, "stress"):
            return ""
        deviatoric = [
            [self.stress[i][j] - (self.mean if i == j else 0.0)
             for j in range(3)]
            for i in range(3)
        ]
        return (
            f"平均应力 σm = {self.mean:.3g} MPa    |    "
            f"偏应力迹 tr(S) = "
            f"{sum(deviatoric[i][i] for i in range(3)):.2g} MPa    |    "
            f"方位 {self.view['azimuth']:.0f}° / "
            f"仰角 {self.view['elevation']:.0f}° / "
            f"缩放 {self.view['zoom']:.1f}x"
        )

    def _start_rotate(self, event):
        self.drag_start = (event.x, event.y)
        self.auto_rotate = False
        self.auto_button.configure(text="自动旋转")
        self._refresh_view()

    def _rotate(self, event):
        if self.drag_start is None:
            return
        last_x, last_y = self.drag_start
        view = self.view
        view["azimuth"] += (event.x - last_x) * 0.65
        view["elevation"] += (event.y - last_y) * 0.45
        view["elevation"] = max(-85.0, min(85.0, view["elevation"]))
        self.drag_start = (event.x, event.y)
        self._refresh_view()

    def _stop_rotate(self, _event):
        self.drag_start = None

    def _zoom(self, event):
        self._change_zoom(0.1 if event.delta > 0 else -0.1)

    def _change_zoom(self, amount):
        view = self.view
        view["zoom"] = max(0.55, min(1.8, view["zoom"] + amount))
        self._refresh_view()

    def reset_view(self):
        self.view = {"azimuth": 35.0, "elevation": 25.0, "zoom": 1.0}
        self._refresh_view()

    def toggle_auto_rotate(self):
        self.auto_rotate = not self.auto_rotate
        self.auto_button.configure(
            text=(
                "停止旋转" if self.auto_rotate else "自动旋转"
            )
        )

    def _animate(self):
        if self.auto_rotate:
            self.view["azimuth"] = (
                self.view["azimuth"] + 0.8
            ) % 360.0
            self._refresh_view()
        self.root.after(30, self._animate)

    def _refresh_view(self):
        self.draw()
        if hasattr(self, "stress"):
            self.status.configure(text=self._status_text())

    def _project(self, point, origin, unit, view):
        x, y, z = point
        ox, oy = origin
        azimuth = math.radians(view["azimuth"])
        elevation = math.radians(view["elevation"])

        # Rotate the model around z, then tilt it around the camera's x axis.
        x1 = x * math.cos(azimuth) - y * math.sin(azimuth)
        y1 = x * math.sin(azimuth) + y * math.cos(azimuth)
        z1 = z
        x2 = x1
        y2 = y1 * math.cos(elevation) - z1 * math.sin(elevation)
        z2 = y1 * math.sin(elevation) + z1 * math.cos(elevation)

        return (
            ox + unit * x2,
            oy - unit * z2,
        )

    def _line3(self, a, b, origin, unit, view, **kwargs):
        p1 = self._project(a, origin, unit, view)
        p2 = self._project(b, origin, unit, view)
        self.canvas.create_line(*p1, *p2, **kwargs)

    def _draw_component_arrow(
        self, start, direction, label, value, origin, unit, view, color, scale
    ):
        if abs(value) < 1e-12:
            point = self._project(start, origin, unit, view)
            self.canvas.create_oval(
                point[0] - 2, point[1] - 2, point[0] + 2, point[1] + 2,
                fill=color, outline=color,
            )
            self.canvas.create_text(
                point[0] + 5, point[1] - 8,
                text=f"{label}=0",
                fill=color, font=("Segoe UI", 8, "bold"),
            )
            return
        end = tuple(start[i] + direction[i] * value * scale for i in range(3))
        start_2d = self._project(start, origin, unit, view)
        end_2d = self._project(end, origin, unit, view)
        self.canvas.create_line(
            *start_2d, *end_2d, fill=color, width=2.6,
            arrow=tk.LAST, arrowshape=(9, 11, 5),
        )
        label_x, label_y = end_2d
        self.canvas.create_text(
            label_x + 5, label_y - 8,
            text=f"{label}={value:g}",
            fill=color, font=("Segoe UI", 8, "bold"),
        )

    def _draw_face_components(
        self, tensor, face, half, origin, unit, view, scale
    ):
        # Each row of sigma gives the force direction; each column identifies
        # the face normal. For example, on the +x face:
        # t_x = (sigma_xx, tau_yx, tau_zx).
        specs = {
            "x": {
                "center": (half, 0, 0),
                "normal": ((1, 0, 0), "σxx", tensor[0][0]),
                "shear": (
                    ((0, 1, 0), "τyx", tensor[1][0], (half, 0, 0.23)),
                    ((0, 0, 1), "τzx", tensor[2][0], (half, -0.23, 0)),
                ),
            },
            "y": {
                "center": (0, half, 0),
                "normal": ((0, 1, 0), "σyy", tensor[1][1]),
                "shear": (
                    ((1, 0, 0), "τxy", tensor[0][1], (0, half, 0.23)),
                    ((0, 0, 1), "τzy", tensor[2][1], (0.23, half, 0)),
                ),
            },
            "z": {
                "center": (0, 0, half),
                "normal": ((0, 0, 1), "σzz", tensor[2][2]),
                "shear": (
                    ((1, 0, 0), "τxz", tensor[0][2], (0, 0.23, half)),
                    ((0, 1, 0), "τyz", tensor[1][2], (-0.23, 0, half)),
                ),
            },
        }
        item = specs[face]
        normal_direction, normal_label, normal_value = item["normal"]
        self._draw_component_arrow(
            item["center"], normal_direction, normal_label, normal_value,
            origin, unit, view, NORMAL_COLOR, scale,
        )
        for direction, label, value, start in item["shear"]:
            self._draw_component_arrow(
                start, direction, label, value, origin, unit,
                view, SHEAR_COLOR, scale,
            )
        face_center = self._project(item["center"], origin, unit, view)
        self.canvas.create_text(
            face_center[0], face_center[1] + 17,
            text=f"+{face}面", fill="#4e5b62", font=("Segoe UI", 8),
        )

    def _draw_panel(self, center_x, center_y, panel_w, title, tensor, color, view):
        c = self.canvas
        c.create_text(
            center_x, 30, text=title,
            fill="#263238",
            font=("Microsoft YaHei UI", 16, "bold"),
        )
        half = 0.72
        unit = min(panel_w * 0.48, 145) * view["zoom"]
        origin = (center_x, center_y)

        # Draw the twelve edges of a cube centered at the origin.
        vertices = [
            (x * half, y * half, z * half)
            for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)
        ]
        for point in vertices:
            for axis in range(3):
                neighbor = list(point)
                if point[axis] < 0:
                    neighbor[axis] = half
                    self._line3(point, tuple(neighbor), origin, unit, view,
                                fill="#879198", width=1.2)

        # Coordinate axes and labels.
        for end, label in (((1.22, 0, 0), "x"), ((0, 1.22, 0), "y"),
                           ((0, 0, 1.22), "z")):
            self._line3((0, 0, 0), end, origin, unit, view,
                        fill="#53616a", width=1.4, arrow=tk.LAST)
            px, py = self._project(end, origin, unit, view)
            c.create_text(px + 8, py - 4, text=label, fill="#3c484f",
                          font=("Segoe UI", 10, "bold"))

        max_component = max(
            (abs(tensor[i][j]) for i in range(3) for j in range(3)),
            default=0.0,
        )
        component_scale = 0.48 / max_component if max_component else 0.0
        for face in ("x", "y", "z"):
            self._draw_face_components(
                tensor, face, half, origin, unit, view, component_scale,
            )

        c.create_text(
            center_x, center_y + unit * 1.35,
            text=self._format_matrix(tensor),
            font=("Consolas", 10), fill="#263238", justify="center",
        )

    @staticmethod
    def _format_matrix(matrix):
        rows = ["[" + "  ".join(f"{value:7.2f}" for value in row) + "]"
                for row in matrix]
        return "应力分量矩阵 (MPa)\n" + "\n".join(rows)

    def draw(self):
        if not hasattr(self, "stress"):
            return
        c = self.canvas
        c.delete("all")
        width = max(c.winfo_width(), 600)
        height = max(c.winfo_height(), 400)
        margin = 14
        c.create_rectangle(
            margin, 12, width - margin, height - 16,
            fill="#ffffff", outline="#c7d3d9", width=1,
        )
        c.create_line(
            margin + 22, 54, width - margin - 22, 54,
            fill="#c65353", width=4,
        )
        center_y = height * 0.43
        self._draw_panel(
            width / 2, center_y, width - margin * 2,
            "总应力模型 σ", self.stress, "#c65353", self.view,
        )
        c.create_text(
            width / 2, height - 30,
            text=(
                f"方位 {self.view['azimuth']:.0f}°  |  "
                f"仰角 {self.view['elevation']:.0f}°  |  "
                f"缩放 {self.view['zoom']:.1f}x"
            ),
            fill="#6a767d", font=("Segoe UI", 9),
        )
        c.create_text(
            18, height - 10,
            text="拖动模型即可旋转，滚轮可缩放",
            anchor="sw", fill="#6a767d", font=("Microsoft YaHei UI", 9),
        )


def main():
    root = tk.Tk()
    style = ttk.Style(root)
    try:
        style.theme_use("vista")
    except tk.TclError:
        pass
    style.configure("TFrame", background=BG)
    style.configure(
        "TLabel",
        background=BG,
        foreground="#263238",
        font=("Microsoft YaHei UI", 9),
    )
    style.configure(
        "TButton",
        padding=(10, 6),
        font=("Microsoft YaHei UI", 9),
    )
    style.configure(
        "TEntry",
        padding=(5, 4),
        font=("Segoe UI", 10),
    )
    style.configure(
        "Status.TLabel",
        background="#dfe8ed",
        foreground="#263238",
        padding=(8, 6),
        font=("Microsoft YaHei UI", 9),
    )
    StressDecompositionApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
